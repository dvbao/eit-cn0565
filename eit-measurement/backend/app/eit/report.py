"""Orchestration: single-session check and full study analysis with manifest + README."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import __version__, features as ft, plots, qc
from .config import REPO, resolve, resolve_out
from .io import Session, sha256_tree


CODE_PATHS = ("backend", "data/studies")


def _git() -> dict:
    def run(*args):
        try:
            return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, timeout=10).stdout.strip()
        except Exception:  # git missing: provenance degrades gracefully
            return ""

    def count(*paths):
        return len([x for x in run("status", "--porcelain", "--", *paths).splitlines() if x])
    return {"commit": run("rev-parse", "HEAD"), "uncommitted_changes": count(),
            "uncommitted_code_changes": count(*CODE_PATHS)}


def _command() -> str:
    """The command as typed: `python -m app ...` rather than the absolute path of __main__.py."""
    if Path(sys.argv[0]).name == "__main__.py" and Path(sys.argv[0]).parent.name == "app":
        return "python -m app " + " ".join(sys.argv[1:])
    return " ".join(sys.argv)


def _versions() -> dict:
    out = {"python": platform.python_version(), "app.eit": __version__}
    from importlib import metadata

    for name in ("numpy", "scipy", "pandas", "matplotlib", "pyeit"):
        try:
            out[name] = metadata.version(name)  # pyeit has no __version__ attribute
        except Exception:
            try:
                out[name] = __import__(name).__version__
            except Exception:
                out[name] = "not installed"
    return out


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(type(o))


def write_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=_json_default))


# ---------------------------------------------------------------------------------------
# Single session (right after acquisition)
# ---------------------------------------------------------------------------------------


def check_session(path, out=None, strong_counts=50.0, rest_label="REST", label=None) -> dict:
    s = Session(resolve(path), label=label, rest_label=rest_label)
    out = resolve_out(out) if out else REPO / "data/results/checks" / s.name
    out.mkdir(parents=True, exist_ok=True)
    summary = qc.qc_summary(s, strong_counts)
    tl = qc.timeline(s)
    tl.to_csv(out / "timeline.csv", index=False)
    qc.drive_gain_table(s, strong_counts).to_csv(out / "drive_gain.csv", index=False)
    noise = qc.rest_rest_noise(s)
    if len(noise):  # nothing to write for a session with a single rest frame
        noise.to_csv(out / "rest_rest_noise.csv", index=False)
    plots.use_style()
    plots.qc_timeline([tl], [s.label], out / "timeline.png")
    ref = s.rest_mean()
    plots.qc_baseline_maps([s], [s.label], [ref], np.abs(ref) >= strong_counts, out / "rest_maps.png", strong_counts)
    write_json({"summary": summary, "sha256": sha256_tree(s.path), "versions": _versions(),
                "checked_utc": datetime.now(timezone.utc).isoformat()}, out / "check.json")
    return {"summary": summary, "out": out}


# ---------------------------------------------------------------------------------------
# Study
# ---------------------------------------------------------------------------------------


def run_study(cfg: dict, quick: bool = False) -> Path:
    raw_root = resolve(cfg["raw_root"])
    sessions = []
    for item in cfg["sessions"]:
        path = Path(item["dir"])
        if not path.is_absolute():
            path = raw_root / path
        sessions.append(Session(path, label=item.get("label"), rest_label=cfg["rest_label"]))
    labels = [s.label for s in sessions]
    if len(set(labels)) != len(labels):
        raise ValueError(f"session labels must be unique: {labels}")
    if len({s.meta.get("protocol_hash", "") for s in sessions}) > 1:
        raise ValueError("sessions use different measurement protocols; analyse them in separate studies")

    out = resolve(cfg["out_root"]) / cfg["study_id"]
    tables, figs = out / "tables", out / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    plots.use_style()
    git = _git()
    if git["uncommitted_code_changes"]:
        _warn(f"{git['uncommitted_code_changes']} uncommitted change(s) in {', '.join(CODE_PATHS)}: "
              "the manifest commit will not reproduce these outputs. Commit first for results you keep.")

    # QC ------------------------------------------------------------------------------
    qc_rows = [qc.qc_summary(s, cfg["strong_counts"]) for s in sessions]
    pd.DataFrame(qc_rows).to_csv(tables / "qc_summary.csv", index=False)
    timelines = [qc.timeline(s) for s in sessions]
    pd.concat(timelines).to_csv(tables / "qc_timeline.csv", index=False)
    pd.concat([qc.drive_gain_table(s, cfg["strong_counts"]) for s in sessions]).to_csv(tables / "qc_drive_gain.csv", index=False)
    noise = pd.concat([qc.rest_rest_noise(s) for s in sessions])
    noise.to_csv(tables / "qc_rest_rest_noise.csv", index=False)

    # Relative change -----------------------------------------------------------------
    all_changes = [ft.changes(s, cfg["baseline"], cfg["drop_first_task_frames"], cfg["rest_reference_frames"])
                   for s in sessions]
    tasks = ft.task_order(sessions, cfg["tasks"], all_changes)
    config_warnings = _config_warnings(cfg, sessions, all_changes)
    for w in config_warnings:
        _warn(w)
    aggs = [ft.aggregate(c) for c in all_changes]
    masks = [ft.strong_mask(s, cfg["strong_counts"]) for s in sessions]
    refs = [s.rest_mean() for s in sessions]
    common = np.all(masks, axis=0)
    # analyses that need every task in every session (correlation matrices, recognition, slide grids)
    complete = [t for t in tasks if all(t in a for a in aggs)]
    pd.concat([ft.pattern_table(s, c, m) for s, c, m in zip(sessions, all_changes, masks)]).to_csv(
        tables / "changes_per_measurement.csv", index=False)
    tf = pd.concat([ft.task_features(s, c, a, tasks, cfg) for s, c, a in zip(sessions, all_changes, aggs)])
    tf.to_csv(tables / "task_features.csv", index=False)
    lat = pd.concat([ft.lateralization(s, c, a, tasks, m) for s, c, a, m in zip(sessions, all_changes, aggs, masks)])
    lat.to_csv(tables / "lateralization.csv", index=False)
    # left/right needs sites named L*/R* with measurements entirely on each side
    has_sides = bool(np.isfinite(lat[["L_median_abs_dz_pct", "R_median_abs_dz_pct"]].to_numpy(float)).any())
    if not has_sides:
        config_warnings.append("no measurements lie entirely on the left or right side (site names L*/R*): "
                               "lateralisation is not available")
    inv = pd.concat([ft.involvement(s, a, tasks, m) for s, a, m in zip(sessions, aggs, masks)])
    inv.to_csv(tables / "electrode_involvement.csv", index=False)
    add = pd.concat([ft.additivity(s, a, common) for s, a in zip(sessions, aggs)] or [pd.DataFrame()])
    add.to_csv(tables / "additivity.csv", index=False)
    xcorr = ft.cross_session_correlation(labels, aggs, tasks, common) if len(sessions) > 1 else pd.DataFrame()
    xcorr.to_csv(tables / "correlation_across_sessions.csv", index=False)
    names, cmat = ft.correlation_matrix(labels, aggs, complete, common)
    pd.DataFrame(cmat, index=names, columns=names).to_csv(tables / "correlation_matrix.csv")

    # control blocks (e.g. REST_CONTROL) are the no-task null: kept in the tables, not a class to recognise
    rec_tasks = [t for t in complete if "CONTROL" not in t.upper()]
    groups, samples = _recognition_samples(sessions, labels, all_changes, aggs, rec_tasks, common)
    rec = None
    order_caveat, same_position = _order_check(all_changes, rec_tasks)
    if len(groups) > 1 and len(rec_tasks) > 1:
        rec = ft.recognition(groups, samples, rec_tasks, 50 if quick else cfg["recognition"]["permutations"],
                             cfg["recognition"]["seed"])
        rec["groups"] = groups
        rec["tasks"] = rec_tasks
        rec["caveat"] = order_caveat
        rec["tasks_at_same_position_in_every_group"] = same_position
        write_json(rec, tables / "recognition.json")

    # Figures ---------------------------------------------------------------------------
    outputs = cfg["outputs"]
    if outputs.get("report_figures", True):
        plots.qc_timeline(timelines, labels, figs / "qc_timeline.png")
        plots.qc_baseline_maps(sessions, labels, refs, common, figs / "qc_rest_maps.png", cfg["strong_counts"])
        plots.dz_heatmap(sessions, labels, aggs, masks, tasks, figs / "dz_heatmap.png")
        plots.dz_re_vs_im(labels, aggs, masks, tasks, figs / "dz_amplitude_vs_phase.png")
        if len(sessions) > 1:
            plots.session_effect(labels, aggs, masks, tasks, figs / "dz_per_session.png")
            plots.task_correlation_across(names, cmat, len(sessions), figs / "correlation_task_x_session.png")
        if has_sides:
            plots.lateralization(lat, labels, tasks, figs / "lateralization.png")
        if len(complete) > 1:  # a correlation matrix needs at least two tasks
            plots.task_correlation_within(labels, aggs, complete, common, ft.feature_vector,
                                          figs / "correlation_within_session.png")
        plots.electrode_involvement(inv, labels, tasks, sessions[0].sites, figs / "electrode_involvement.png")
        if rec is not None:
            plots.recognition_confusion(rec, rec_tasks, rec["groups"], figs / "recognition_confusion.png")
    if outputs.get("slide_figures", True):
        plots.use_style(font="Arial")
        plots.dz_heatmap(sessions, labels, aggs, masks, tasks, out / "slides/S1_relative_change_heatmap.png", slide=True)
        if has_sides:
            plots.lateralization(lat, labels, tasks, out / "slides/S2_lateralization.png", slide=True)
        if len(sessions) > 1:
            plots.task_correlation_across(names, cmat, len(sessions), out / "slides/S3_task_session_correlation.png", slide=True)
        plots.use_style()

    recon_summary = {}
    rc = dict(cfg["reconstruction"])
    ring = {(s.n_el, s.ring_distances) for s in sessions}
    if rc.get("enabled", True) and len(ring) == 1 and sessions[0].ring_distances:
        from . import recon

        rc["noise_counts"] = cfg["noise_counts"]
        if quick:
            rc["noise_draws"] = 10
        solvers = recon.Solvers(sessions[0].n_el, rc, *sessions[0].ring_distances)
        images, metrics = recon.reconstruct_study(solvers, labels, aggs, masks, [np.abs(r) for r in refs], tasks, rc)
        metrics.to_csv(tables / "recon_metrics.csv", index=False)
        across, between = recon.image_correlations(solvers, images, labels, tasks)
        across.to_csv(tables / "recon_image_corr_across_sessions.csv", index=False)
        between.to_csv(tables / "recon_image_corr_between_algorithms.csv", index=False)
        np.savez_compressed(out / "tables/recon_images.npz", **{"|".join(k): v for k, v in images.items()})
        fit = recon.disk_model_fit(solvers, labels, refs)
        fit.to_csv(tables / "recon_disk_model_fit.csv", index=False)
        kt_cfg = rc["known_target"]
        kt = recon.known_target(solvers, masks[0], np.abs(refs[0]), cfg["noise_counts"], center=kt_cfg["center"],
                                radius=kt_cfg["radius"], contrast=kt_cfg["contrast"], seed=kt_cfg["seed"])
        recon_summary = {"known_target_median_abs_change_pct": kt["median_abs_change_pct"],
                         "known_target_contrast": kt_cfg["contrast"],
                         "disk_model_fit_spearman": [round(x, 3) for x in fit.spearman_log_abs_v_rest_vs_disk],
                         "mesh_elements": int(solvers.mesh.n_elems), "mesh_nodes": int(solvers.mesh.n_nodes)}
        if outputs.get("report_figures", True):
            plots.recon_compare_by_session(solvers, images, labels, tasks, figs / "recon_bp_jac_greit_by_session.png")
            plots.recon_known_target(solvers, kt, sessions[0].sites, figs / "recon_known_target_check.png")
        if outputs.get("slide_figures", True):
            plots.use_style(font="Arial")
            for lab in labels:
                plots.slide_algorithms(solvers, images, metrics, lab, complete, out / f"slides/S4_bp_jac_greit_{plots.slug(lab)}.png")
            plots.slide_greit_sessions(solvers, images, metrics, labels, complete, out / "slides/S5_greit_all_sessions.png")
            plots.use_style()
        if outputs.get("clean_images", True):
            plots.clean_images(solvers, images, labels, tasks, out / "clean")

    if rc.get("enabled", True) and not recon_summary:
        config_warnings.append("reconstruction skipped: the sessions do not share one regular ring protocol "
                               f"(electrodes, force/sense distance: {sorted(ring, key=str)})")

    # Manifest + README -------------------------------------------------------------------
    manifest = {
        "study_id": cfg["study_id"], "title": cfg.get("title", ""),
        "created_utc": datetime.now(timezone.utc).isoformat(), "command": _command(),
        "git": git, "versions": _versions(), "config": cfg, "quick_mode": quick,
        "sessions": {s.name: {"label": s.label, "path": str(s.path.relative_to(REPO)) if REPO in s.path.parents else str(s.path),
                              "sha256": sha256_tree(s.path)} for s in sessions},
        "tasks": tasks, "common_strong_measurements": int(common.sum()), "reconstruction": recon_summary,
    }
    write_json(manifest, out / "manifest.json")
    _write_readme(out, cfg, sessions, labels, tasks, qc_rows, tf, lat, xcorr, add, rec, order_caveat, recon_summary,
                  tables, config_warnings)
    return out


def _warn(message: str):
    print(f"warning: {message}", file=sys.stderr)


def _sentence(text: str) -> str:
    return f"{text[:1].upper()}{text[1:]}." if text else ""


def _is_control(task: str) -> bool:
    return "CONTROL" in str(task).upper()


def _config_warnings(cfg, sessions, all_changes) -> list:
    """Settings that silently change the analysis: tasks filtered out by cfg['tasks'], baseline vs design."""
    out = []
    recorded = []
    for chs in all_changes:
        recorded += [c.task for c in chs if c.task not in recorded]
    if cfg["tasks"]:
        skipped = [t for t in recorded if t not in cfg["tasks"]]
        absent = [t for t in cfg["tasks"] if t not in recorded]
        if skipped:
            out.append(f"recorded tasks not listed in config 'tasks' are left out of every table: {', '.join(skipped)}")
        if absent:
            out.append(f"config 'tasks' not found in any session: {', '.join(absent)}")
    for s in sessions:
        blist = ft.blocks(s)
        n_rest_blocks = sum(b["kind"] == "REST" and b["valid"] for b in blist)
        first_task = next((j for j, b in enumerate(blist) if b["kind"] == "TASK"), len(blist))
        if cfg["baseline"] == "initial_rest" and not any(b["kind"] == "REST" and b["valid"] for b in blist[:first_task]):
            out.append(f"{s.label}: no valid rest before the first task; 'initial_rest' falls back to later rest frames")
        if cfg["baseline"] == "initial_rest" and n_rest_blocks > 1:
            out.append(f"{s.label}: {n_rest_blocks} rest blocks between tasks but baseline is 'initial_rest'; "
                       "'bracketing_rest' uses them to cancel drift")
        if cfg["baseline"] != "initial_rest" and n_rest_blocks == 1:
            out.append(f"{s.label}: baseline '{cfg['baseline']}' but only one rest block: it falls back to that block")
        if s.invalid_trials:
            out.append(f"{s.label}: {len(s.invalid_trials)} trial(s) marked valid=False excluded: "
                       f"{', '.join(sorted(s.invalid_trials))}")
    return out


def _recognition_samples(sessions, labels, all_changes, aggs, tasks, common):
    """Groups = sessions when there are several; otherwise repetitions within the one session."""
    if len(sessions) > 1:
        samples = {(lab, t): ft.feature_vector(agg[t], common) for lab, agg in zip(labels, aggs) for t in tasks if t in agg}
        groups = [lab for lab, agg in zip(labels, aggs) if all(t in agg for t in tasks)]
        return groups, samples
    reps = sorted({c.repetition for c in all_changes[0]})
    samples = {(f"rep{c.repetition}", c.task): ft.feature_vector(c.dz, common) for c in all_changes[0]}
    groups = [f"rep{r}" for r in reps if all((f"rep{r}", t) in samples for t in tasks)]
    return groups, samples


def _order_check(all_changes, tasks):
    """Task order per recognition group (sessions, or repetitions within a single session).

    Returns (caveat, tasks at the same position in every group). An identical order confounds
    recognition with position in the sequence (time since rest, fatigue, drift).
    """
    if len(all_changes) > 1:
        seqs = [[c.task for c in chs if c.task in tasks] for chs in all_changes]
    else:
        chs = all_changes[0]
        seqs = [[c.task for c in chs if c.repetition == r and c.task in tasks]
                for r in sorted({c.repetition for c in chs})]
    seqs = [q for q in seqs if q]
    if len(seqs) < 2:
        return "", []
    same = [t for t in tasks if all(t in q for q in seqs) and len({q.index(t) for q in seqs}) == 1]
    if all(q == seqs[0] for q in seqs):
        return "task order identical in every group: recognition is confounded with position in the sequence", same
    return "", same


def _fmt_range(series, fmt="{:.2f}"):
    s = pd.Series(series).dropna()
    return "n/a" if s.empty else f"{fmt.format(s.min())} to {fmt.format(s.max())}"


def _write_readme(out, cfg, sessions, labels, tasks, qc_rows, tf, lat, xcorr, add, rec, order_caveat, recon_summary,
                  tables, config_warnings):
    qdf = pd.DataFrame(qc_rows)
    lines = [f"# {cfg['study_id']}", "", cfg.get("title", ""), "",
             "Generated by `python -m app study` — do not edit by hand; re-run the command instead.",
             f"Configuration: `{Path(cfg['config_path']).relative_to(REPO) if REPO in Path(cfg['config_path']).parents else cfg['config_path']}`. "
             "Provenance (git commit, package versions, raw-file SHA-256): `manifest.json`.", "",
             "## Sessions and QC", "",
             "| label | session | audit | frames inside cue window | strong channels | reciprocity error (median) | REST->REST noise |",
             "|---|---|---|---|---|---|---|"]
    strong_col = f"rest_n_ge_{cfg['strong_counts']:g}"
    for r in qdf.itertuples():
        d = r._asdict()
        noise_txt = (f"{d['rest_rest_rms_counts']:.2f} counts" if d["rest_rest_pairs"]
                     else "not measured (no adjacent REST frames)")
        lines.append(f"| {d['label']} | {d['session']} | {'pass' if d['audit_pass'] else 'FAIL'} | "
                     f"{d['frames_inside_hold']} | {d.get(strong_col, 'n/a')} | {d.get('recip_err_strong_median_pct', np.nan):.1f}% | {noise_txt} |")
    real = [t for t in tasks if not _is_control(t)]
    controls = [t for t in tasks if _is_control(t)]
    tf_real = tf[tf.task.isin(real)]
    lines += ["", "## Key numbers", "",
              f"- Tasks: {', '.join(tasks)}; baseline policy: `{cfg['baseline']}`; strong channel threshold {cfg['strong_counts']:g} counts.",
              f"- Median |dz| on strong channels (tasks, controls excluded): {_fmt_range(tf_real.median_abs_dz_pct_strong)} %; "
              f"on channels >= 100 counts: {_fmt_range(tf_real.median_abs_dz_pct_ge100)} %."]
    for t in controls:
        c = tf[tf.task == t]
        lines.append(f"- {t} (no-task null, same cue timing): median |dz| on strong channels {_fmt_range(c.median_abs_dz_pct_strong)} %; "
                     f"compare every task with this value, not with zero.")
    lines.append(f"- Lateralisation index LI = (L-R)/(L+R): {', '.join(f'{t} {_fmt_range(lat[lat.task == t].LI)}' for t in real)}.")
    if len(xcorr):
        lines.append(f"- Same task across sessions: r = {_fmt_range(xcorr.r_same_task_common_strong)}; "
                     f"different tasks (mean): {_fmt_range(xcorr.r_other_tasks_mean)}.")
    if len(add):
        lines.append(f"- Bilateral = a*left + b*right: R^2 = {_fmt_range(add.r2)}.")
    if rec is not None:
        lines.append(f"- Leave-one-group-out recognition: accuracy {rec['accuracy']:.2f} (chance {rec['chance']:.2f}), "
                     f"permutation p = {rec['perm_p']:.4f}. {_sentence(rec.get('caveat', ''))}")
    if recon_summary:
        m = pd.read_csv(tables / "recon_metrics.csv")
        side_ok = 0
        unilateral = m[m.task.str.endswith(("_LEFT", "_RIGHT"))]
        for r in unilateral.itertuples():
            side_ok += int((r.left_energy_fraction > 0.5) == r.task.endswith("_LEFT"))
        lines.append(f"- Reconstruction (exploratory 2-D disk): change on the cued side in {side_ok}/{len(unilateral)} "
                     f"unilateral algorithm x session x task images; image/noise {_fmt_range(m.image_to_noise, '{:.1f}')}; "
                     f"a known {100 * (recon_summary['known_target_contrast'] - 1):+.0f}% conductivity blob gives "
                     f"{recon_summary['known_target_median_abs_change_pct']:.2f}% median change on the strong channels of {labels[0]}.")
    lines += ["", "## Caveats detected automatically", ""]
    cav = list(config_warnings)
    if all(len(s.rest_frames) < 2 for s in sessions):
        cav.append("Every session has a single rest frame: drift, carry-over and the noise floor are not measured in-session.")
    elif all(r["rest_rest_pairs"] == 0 for r in qc_rows):
        cav.append("No two REST frames are adjacent: the noise floor is not measured (only drift across tasks).")
    for r in qc_rows:
        if r.get("recip_pairs") and not r.get("drive_gain_fit_supported"):
            cav.append(f"{r['label']}: the per-drive gain fit reduces the reciprocity error no more than it reduces "
                       f"pure noise (ratio {r['recip_fit_ratio']:.2f} vs null 5th percentile "
                       f"{r['recip_fit_null_ratio_p05']:.2f}); fitted drive gains are not reliable.")
    missing = [s.label for s in sessions if s.trial_windows is None]
    if missing:
        cav.append(f"No operator-confirmed trial windows for: {', '.join(missing)} (task labels are cue-assumed).")
    if any(r.get("measurement_mode", "").startswith("voltage") for r in qc_rows):
        cav.append("Voltage mode: drive current was not measured (relative changes cancel it only if it is constant).")
    if order_caveat:
        cav.append(_sentence(order_caveat))
    cav.append("Reconstructions use a 2-D disk with equally spaced electrodes: they are projections, not facial anatomy.")
    lines += [f"- {c}" for c in cav]
    lines += ["", "## Files", "",
              "- `tables/`: QC (`qc_*.csv`), per-measurement changes, task features, lateralisation, correlations, "
              "additivity, electrode involvement, recognition, reconstruction metrics and images (`recon_images.npz`).",
              "- `figures/`: report figures (English).", "- `slides/`: the same results sized for 10 x 5.63 in slides.",
              "- `clean/`: label-free reconstruction images for manual layout (see `clean/README.txt`)."]
    (out / "README.md").write_text("\n".join(lines) + "\n")
