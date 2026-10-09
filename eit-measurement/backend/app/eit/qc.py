"""Acquisition QC: integrity audit, cue/frame timing, reciprocity, drive-current spread, REST->REST noise."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .io import Session
from .protocol import pair_label

REQUIRED_CHECKS = (
    "status_complete",
    "source_live",
    "has_rest_frame",
    "frames_complete",
    "no_pattern_errors",
    "csv_matches_meta_sequence",
    "finite_values",
    "positive_durations",
    "pattern_times_monotonic",
    "nonzero_rest",
    "settings_constant",
)


def audit(s: Session) -> dict:
    """Pass/fail integrity checks (REQUIRED_CHECKS) plus informational fields."""
    p = s.patterns
    ids_ok = p.groupby("frame_id")["pattern_id"].agg(lambda x: sorted(x) == list(range(s.n_pat)))
    cols = ["f_plus", "s_plus", "s_minus", "f_minus"]
    meta_seq = np.array(s.meta["sequence"])
    seq_ok = all(np.array_equal(g.sort_values("pattern_id")[cols].to_numpy(), meta_seq) for _, g in p.groupby("frame_id"))
    monotonic = all(bool(np.all(np.diff(g.sort_values("pattern_id")["start_s"].to_numpy()) > 0))
                    for _, g in p.groupby("frame_id"))
    rest = s.rest_mean() if s.rest_frames else np.array([0.0])
    checks = {
        "status_complete": s.meta.get("status") == "complete",
        "source_live": s.meta.get("source") == "live",
        "has_rest_frame": bool(s.rest_frames),
        "frames_complete": bool(s.frames.get("complete", pd.Series([True])).astype(bool).all())
        and bool(ids_ok.all()) and len(ids_ok) == len(s.frames),
        "no_pattern_errors": int(p["error"].notna().sum()) == 0 if "error" in p else True,
        "csv_matches_meta_sequence": bool(seq_ok),
        "finite_values": bool(np.isfinite(p[["real_raw", "imag_raw", "start_s", "end_s"]].to_numpy()).all()),
        "positive_durations": bool((p["end_s"] > p["start_s"]).all()),
        "pattern_times_monotonic": bool(monotonic),
        "nonzero_rest": bool(np.all(np.abs(rest) > 0)),
        "settings_constant": _settings_constant(s),
    }
    info = {
        "n_frames": int(len(s.frames)),
        "n_rest_frames": len(s.rest_frames),
        "n_task_frames": len(s.task_frames),
        "n_electrodes": s.n_el,
        "n_measurements": s.n_pat,
        "force_distance": s.ring_distances[0] if s.ring_distances else None,
        "sense_distance": s.ring_distances[1] if s.ring_distances else None,
        "sequence_is_pyeit_std": s.protocol_is_std(),
        "measurement_mode": _mode(s),
        "trial_windows": "operator_reported" if s.trial_windows is not None else "missing (labels cue_assumed)",
        "invalid_trials_excluded": len(s.invalid_trials),
        "recording_design": s.meta.get("recording_design", "unknown"),
        "baseline_policy_at_acquisition": s.meta.get("baseline_policy", "unknown"),
    }
    return {"audit_pass": all(checks[k] for k in REQUIRED_CHECKS), **checks, **info}


def _settings_constant(s: Session) -> bool:
    if s.checks is None:
        return True
    ok = (s.checks["frequency_hz"].astype(float) == s.freq).all()
    if "amplitude_mvpp" in s.checks:
        ok = ok and (s.checks["amplitude_mvpp"].astype(float) == s.amp).all()
    return bool(ok)


def _mode(s: Session) -> str:
    if s.checks is None:
        return "unknown"
    imp = s.checks["impedance_mode"].astype(bool).any() if "impedance_mode" in s.checks else False
    mag = s.checks["magnitude_mode"].astype(bool).any() if "magnitude_mode" in s.checks else False
    return ("impedance" if imp else "voltage") + ("+magnitude" if mag else "")


def timeline(s: Session) -> pd.DataFrame:
    """One row per frame: the cue window it belongs to and whether the scan stayed inside it.

    settle_s (cue -> frame start) is a settle time only for the first frame after a cue
    (first_after_cue); later frames of a multi-frame block share that cue.
    """
    ev = s.events
    is_cue = ev["event"].astype(str).str.endswith("CUE") & ~ev["event"].astype(str).str.contains("WARNING")
    cues = np.sort(ev.loc[is_cue, "time_s"].to_numpy(float))
    end = ev.loc[ev["event"] == "SESSION_END", "time_s"]
    end_t = float(end.iloc[0]) if len(end) else np.inf
    rows, prev_start = [], -np.inf
    for fr in s.frames.sort_values("start_s").itertuples():
        before = cues[cues <= fr.start_s + 1e-6]
        cue = float(before[-1]) if len(before) else np.nan
        after = cues[cues > cue] if np.isfinite(cue) else cues[cues > fr.start_s]
        nxt = float(after[0]) if len(after) else end_t
        first = bool(np.isfinite(cue) and prev_start < cue)
        prev_start = fr.start_s
        rows.append({
            "session": s.name, "label": s.label, "freq_hz": s.freq, "frame_id": int(fr.frame_id),
            "trial_id": fr.trial_id, "task": fr.task, "state": fr.state, "is_rest": bool(fr.is_rest),
            "valid": bool(fr.valid), "first_after_cue": first,
            "cue_s": cue, "settle_s": fr.start_s - cue, "frame_start_s": fr.start_s, "frame_end_s": fr.end_s,
            "frame_duration_s": fr.end_s - fr.start_s, "next_cue_s": nxt, "hold_s": nxt - cue,
            "frame_inside_hold": bool(fr.start_s >= cue and fr.end_s <= nxt),
            "n_measurements": s.n_pat,
            "slack_after_frame_s": nxt - fr.end_s,
        })
    return pd.DataFrame(rows)


def _reciprocal_pairs(s: Session, v_ref: np.ndarray, strong_counts: float):
    """Reciprocal measurement pairs (i, k) strong in v_ref, and the drive-gain design matrix
    (row: +1 at the drive pair of i, -1 at the drive pair of k)."""
    index = {tuple(r): i for i, r in enumerate(s.seq)}
    pairs, rows = [], []
    for i, (a, b, m, n) in enumerate(s.seq):
        k = index.get((m, n, a, b))
        if k is None or k <= i or min(abs(v_ref[i]), abs(v_ref[k])) < strong_counts:
            continue
        row = np.zeros(s.n_el)
        row[a] += 1
        row[m] -= 1
        pairs.append((i, k))
        rows.append(row)
    return pairs, np.array(rows)


def _fit_drive_gain(a_mat: np.ndarray, y: np.ndarray):
    """Least-squares ln-gain per drive pair (sum fixed to zero); y may have several columns."""
    a_aug = np.vstack([a_mat, np.ones(a_mat.shape[1])])
    pad = np.zeros((1,) + y.shape[1:])
    c_re = np.linalg.lstsq(a_aug, np.concatenate([y.real, pad]), rcond=None)[0]
    c_im = np.linalg.lstsq(a_aug, np.concatenate([y.imag, pad]), rcond=None)[0]
    return c_re, y - (a_mat @ c_re + 1j * (a_mat @ c_im))


def reciprocity(s: Session, v: np.ndarray, v_ref: np.ndarray, strong_counts: float, fit_drive_gain: bool = True):
    """Reciprocity error of one frame: median |v_AB,MN / v_MN,AB - 1| over pairs strong in v_ref.

    With ``fit_drive_gain`` one complex gain per drive pair is removed first
    (ln v_i - ln v_k = c_g(i) - c_g(k)), modelling unknown drive current in voltage mode.
    Returns (median before, median after, ln|gain| per drive pair (sum zero)).
    """
    pairs, a_mat = _reciprocal_pairs(s, v_ref, strong_counts)
    if not pairs:
        return np.nan, np.nan, np.full(s.n_el, np.nan)
    y = np.array([np.log(v[i] / v[k]) for i, k in pairs])
    before = float(np.median(np.abs(np.exp(y) - 1)))
    if not fit_drive_gain:
        return before, np.nan, np.full(s.n_el, np.nan)
    c_re, resid = _fit_drive_gain(a_mat, y)
    return before, float(np.median(np.abs(np.exp(resid) - 1))), c_re


def drive_gain_null_ratio(s: Session, v_ref: np.ndarray, strong_counts: float, before: float,
                          draws: int = 2000, seed: int = 0) -> dict:
    """How much the drive-gain fit shrinks pure noise with the same pair structure.

    The fit has up to n_el - 1 free parameters for ~30 reciprocal pairs, so it removes part of any error.
    Random complex errors (no gain structure) with the observed median size are fitted the same way;
    an observed ratio after/before below the 5th percentile of this null supports a real per-drive gain.
    """
    pairs, a_mat = _reciprocal_pairs(s, v_ref, strong_counts)
    if not pairs or not np.isfinite(before):
        return {"median": np.nan, "p05": np.nan, "p95": np.nan, "n_pairs": len(pairs), "rank": 0}
    rng = np.random.default_rng(seed)
    sigma = before / np.sqrt(2 * np.log(2))  # median of a complex Gaussian's modulus = sigma * sqrt(2 ln 2)
    y = sigma * (rng.normal(size=(len(pairs), draws)) + 1j * rng.normal(size=(len(pairs), draws)))
    _, resid = _fit_drive_gain(a_mat, y)
    ratio = np.median(np.abs(np.exp(resid) - 1), axis=0) / np.median(np.abs(np.exp(y) - 1), axis=0)
    return {"median": float(np.median(ratio)), "p05": float(np.percentile(ratio, 5)),
            "p95": float(np.percentile(ratio, 95)), "n_pairs": len(pairs), "rank": int(np.linalg.matrix_rank(a_mat))}


def drive_gain_table(s: Session, strong_counts: float) -> pd.DataFrame:
    """Per frame: reciprocity error and change of ln|drive gain| vs the session rest mean (in %)."""
    ref = s.rest_mean()
    _, _, c_ref = reciprocity(s, ref, ref, strong_counts)
    force = s.ring_distances[0] if s.ring_distances else 1
    rows = []
    for fr in s.frames.itertuples():
        before, after, c = reciprocity(s, s.V[int(fr.frame_id)], ref, strong_counts)
        rows.append({
            "session": s.name, "label": s.label, "frame_id": int(fr.frame_id), "task": fr.task,
            "recip_err_median_pct": 100 * before, "recip_err_after_fit_pct": 100 * after,
            **{f"dln_gain_vs_rest_pct_{pair_label(s.sites, g, force)}": 100 * (c[g] - c_ref[g]) for g in range(s.n_el)},
            **{f"rel_gain_{pair_label(s.sites, g, force)}": float(np.exp(c[g])) for g in range(s.n_el)},
        })
    return pd.DataFrame(rows)


REST_NOISE_COLUMNS = ["session", "label", "frame_a", "frame_b", "kind", "seconds_apart", "rms_dv_counts",
                      "rms_dv_inphase_counts", "median_abs_dz_pct_ge100"]


def rest_rest_noise(s: Session) -> pd.DataFrame:
    """Differences between successive valid rest frames (time order).

    kind = "adjacent": no frame in between -> measurement noise + short-term drift (noise floor);
    kind = "across_control": only control blocks (task name containing CONTROL) in between;
    kind = "across_task": task frames in between -> drift + carry-over / recovery after the task.
    rms_dv_counts is the RMS of the complex difference |v1 - v0|; rms_dv_inphase_counts is the RMS of its
    component along v0 (the part that enters Re(dz)), which is the value to use as ``noise_counts``.
    Has the columns REST_NOISE_COLUMNS even when empty (fewer than two rest frames).
    """
    order = s.frames.sort_values("start_s").reset_index(drop=True)
    pos = {int(f): i for i, f in enumerate(order.frame_id)}
    rest = [int(f) for f in order.frame_id if int(f) in set(s.rest_frames)]
    rows = []
    for f0, f1 in zip(rest[:-1], rest[1:]):
        v0, v1 = s.V[f0], s.V[f1]
        dv = v1 - v0
        big = np.abs(v0) >= 100
        between = order.iloc[pos[f0] + 1:pos[f1]]
        between = between[~between.is_rest]  # invalid rest frames in between do not make it a task gap
        if between.empty:
            kind = "adjacent"
        elif between.task.astype(str).str.upper().str.contains("CONTROL").all():
            kind = "across_control"
        else:
            kind = "across_task"
        rows.append({
            "session": s.name, "label": s.label, "frame_a": f0, "frame_b": f1, "kind": kind,
            "seconds_apart": float(s.frame(f1).mid_s - s.frame(f0).mid_s),
            "rms_dv_counts": float(np.sqrt(np.mean(np.abs(dv) ** 2))),
            "rms_dv_inphase_counts": float(np.sqrt(np.mean(np.real(dv * np.conj(v0) / np.abs(v0)) ** 2))),
            "median_abs_dz_pct_ge100": float(np.median(100 * np.abs(dv / v0)[big])) if big.any() else np.nan,
        })
    return pd.DataFrame(rows, columns=REST_NOISE_COLUMNS)


def _median(series) -> float:
    return float(series.median()) if len(series) else np.nan


def qc_summary(s: Session, strong_counts: float) -> dict:
    a = audit(s)
    tl = timeline(s)
    ref = s.rest_mean() if s.rest_frames else None
    noise = rest_rest_noise(s)
    row = {"session": s.name, "label": s.label, "freq_hz": s.freq, "amplitude_cmd": s.amp,
           "started_utc": s.meta.get("started_utc", ""), **a}
    first = tl[tl.first_after_cue]
    row.update({
        "frames_inside_hold": f"{int(tl.frame_inside_hold.sum())}/{len(tl)}",
        # cue -> start of the first frame after that cue, task and rest separately
        "settle_task_s_median": _median(first.loc[~first.is_rest, "settle_s"]),
        "settle_rest_s_median": _median(first.loc[first.is_rest, "settle_s"]),
        "frame_s_median": float(tl.frame_duration_s.median()),
        "hold_task_s_median": _median(tl.loc[~tl.is_rest, "hold_s"]),
    })
    if ref is not None:
        before, after, c = reciprocity(s, ref, ref, strong_counts)
        null = drive_gain_null_ratio(s, ref, strong_counts, before)
        g = np.exp(c)
        # no reciprocal pairs (e.g. force distance != sense distance): drive gains cannot be estimated
        has_g = bool(np.isfinite(g).any())
        force = s.ring_distances[0] if s.ring_distances else 1
        row.update({
            "rest_abs_median_counts": float(np.median(np.abs(ref))),
            f"rest_n_ge_{strong_counts:g}": int((np.abs(ref) >= strong_counts).sum()),
            "rest_n_ge_100": int((np.abs(ref) >= 100).sum()),
            "rest_phase_median_deg": float(np.degrees(np.median(np.angle(ref)))),
            "recip_pairs": null["n_pairs"],
            "recip_err_strong_median_pct": 100 * before,
            "recip_err_after_drive_gain_fit_pct": 100 * after,
            # after/before for the data vs for pure noise fitted the same way (see drive_gain_null_ratio)
            "recip_fit_ratio": after / before if before else np.nan,
            "recip_fit_null_ratio_median": null["median"],
            "recip_fit_null_ratio_p05": null["p05"],
            "drive_gain_fit_supported": bool(after / before < null["p05"]) if before else False,
            "drive_gain_min": float(np.nanmin(g)) if has_g else np.nan,
            "drive_gain_min_pair": pair_label(s.sites, int(np.nanargmin(g)), force) if has_g else "",
            "drive_gain_max": float(np.nanmax(g)) if has_g else np.nan,
        })
    adj, ctl, acr = (noise[noise.kind == k] for k in ("adjacent", "across_control", "across_task"))
    row.update({
        "rest_rest_pairs": int(len(adj)),
        "rest_rest_rms_counts": _median(adj.rms_dv_counts),
        "rest_rest_inphase_rms_counts": _median(adj.rms_dv_inphase_counts),
        "rest_rest_median_pct_ge100": _median(adj.median_abs_dz_pct_ge100),
        "rest_across_control_pairs": int(len(ctl)),
        "rest_across_control_median_pct_ge100": _median(ctl.median_abs_dz_pct_ge100),
        "rest_across_task_pairs": int(len(acr)),
        "rest_across_task_median_pct_ge100": _median(acr.median_abs_dz_pct_ge100),
    })
    return row
