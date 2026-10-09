"""Read-only audit, English figures, and explicitly model-dependent EIT projections.

Run: .venv-sim/bin/python scripts/analysis/english_pilot_review.py
Requires the existing three_frequency_report.py plus numpy/pandas/matplotlib/pyEIT.
Raw recordings and the preliminary report are never edited. Relative changes are
voltage changes, NOT measured impedance changes. No empirical noise model is
inferred from one REST frame. All movement labels remain cue_assumed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import three_frequency_report as source
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "data/processed/pilot/english-review-20261005"
TASKS = source.TASKS
STATES = source.STATES
NAMES = {t: t.replace("_", " ").title() for t in STATES}
COLORS = ["#286bb5", "#df6b2a", "#258664"]


def relative_voltage(v1, v0):
    """Complex, pattern-wise voltage ratio, protected against a zero baseline."""
    if not np.isfinite(v0).all() or np.any(np.abs(v0) == 0):
        raise ValueError("Nonfinite/zero REST: select and document valid rows first.")
    return (v1 - v0) / v0


def file_hashes(sessions):
    return {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for s in sessions for p in sorted(s["path"].iterdir()) if p.is_file()
    }


def audit_session(s):
    """Check every frame, not just the initial REST frame's measurement sequence."""
    p, fr, meta = s["patterns"], s["frames"], s["meta"]
    tests = source.audit(s)
    from pyeit.eit.protocol import create
    library_protocol = create(16, dist_exc=1, step_meas=1, parser_meas="std")
    library_rows = np.array([
        (a, b, m, n) for (a, b), measures in zip(library_protocol.ex_mat, library_protocol.meas_mat)
        for n, m in measures])
    tests["logical_rows_match_installed_pyeit_protocol"] = bool(np.array_equal(s["seq"], library_rows))
    tests["finite_raw_and_times"] = bool(np.isfinite(p[
        ["real_raw", "imag_raw", "start_s", "end_s"]].to_numpy()).all())
    tests["positive_measurement_durations"] = bool((p.end_s > p.start_s).all())
    tests["no_zero_rest_denominators"] = bool(np.all(np.abs(s["v"]["REST"]) > 0))
    tests["frames_complete"] = bool(fr.complete.eq(True).all())
    tests["one_frame_per_state"] = bool(
        set(fr.task) == set(STATES) and fr.task.value_counts().eq(1).all())
    tests["pattern_hz_and_amplitude_constant"] = bool(
        p.configured_frequency_hz.eq(s["freq"]).all()
        and p.configured_amplitude_mvpp.eq(s["amp"]).all())
    tests["magnitude_and_phase_match_complex_counts"] = bool(
        np.allclose(p.magnitude_raw, np.hypot(p.real_raw, p.imag_raw))
        and np.allclose(p.phase_deg, np.degrees(np.arctan2(p.imag_raw, p.real_raw))))
    origin = meta["origin_perf_counter_ns"]
    tests["host_clock_fields_consistent"] = bool(
        np.allclose(p.start_s, (p.start_perf_counter_ns - origin) / 1e9, atol=1e-6)
        and np.allclose(p.end_s, (p.end_perf_counter_ns - origin) / 1e9, atol=1e-6))
    physical_sites = {c["index"]: c["site"] for c in meta["mapping"]["channels"]}
    seq_ok, site_ok, bounds_ok, nonoverlap_ok = True, True, True, True
    for _, frame in fr.iterrows():
        g = p[p.frame_id == frame.frame_id].sort_values("pattern_id")
        seq_ok &= np.array_equal(g.pattern_id, np.arange(208))
        seq_ok &= np.array_equal(g[["f_plus", "s_plus", "s_minus", "f_minus"]], meta["sequence"])
        seq_ok &= bool(g.task.eq(frame.task).all() and g.trial_id.eq(frame.trial_id).all())
        for role in ("f_plus", "s_plus", "s_minus", "f_minus"):
            site_ok &= bool(g[role + "_site"].eq(g[role].map(physical_sites)).all())
        f0, f1 = (frame.start_perf_counter_ns - origin) / 1e9, (frame.end_perf_counter_ns - origin) / 1e9
        bounds_ok &= bool(g.start_s.ge(f0 - 1e-6).all() and g.end_s.le(f1 + 1e-6).all())
        nonoverlap_ok &= bool(np.all(g.start_s.to_numpy()[1:] >= g.end_s.to_numpy()[:-1]))
    tests.update(all_frames_sequence_and_labels_match=bool(seq_ok),
                 site_names_match_physical_mapping=bool(site_ok),
                 every_measurement_inside_its_frame=bool(bounds_ok),
                 measurements_do_not_overlap=bool(nonoverlap_ok))
    tests["all_frames_inside_cue_windows"] = bool(source.timing(s).frame_inside_hold.all())
    if not all(tests.values()):
        raise ValueError(f"Audit failed for {s['name']}: {[k for k, v in tests.items() if not v]}")
    return tests


def tables(sessions, common):
    qc, features, patterns = [], [], []
    for s in sessions:
        v0 = s["v"]["REST"]
        tm = source.timing(s)
        qc.append({"session": s["name"], "frequency_hz": s["freq"],
                   "amplitude_command": s["amp"], "n_rows": len(s["patterns"]),
                   "median_scan_s": tm.frame_duration_s.median(),
                   "median_rest_magnitude_counts": np.median(np.abs(v0)),
                   "n_rest_ge50": int((np.abs(v0) >= 50).sum()),
                   "n_rest_ge100": int((np.abs(v0) >= 100).sum()),
                   "last_task_since_rest_mid_s": tm.t_since_rest_mid_s.max(),
                   "operator_reported_windows_present": s["trial_windows"] is not None})
        for task in TASKS:
            v1 = s["v"][task]
            r = relative_voltage(v1, v0)
            magnitude_change = np.abs(v1) / np.abs(v0) - 1
            phase_change = np.degrees(np.angle(v1 / v0))
            g = s["patterns"][s["patterns"].task == task].sort_values("pattern_id")
            f = {"session": s["name"], "frequency_hz": s["freq"], "task": task,
                 "label_provenance": "cue_assumed", "n_common_patterns": int(common.sum()),
                 "rms_voltage_difference_counts": np.sqrt(np.mean(np.abs(v1 - v0)**2)),
                 "median_abs_relative_voltage_pct_common": np.median(100 * np.abs(r[common])),
                 "median_signed_magnitude_change_pct_common": np.median(100 * magnitude_change[common]),
                 "median_signed_phase_change_deg_common": np.median(phase_change[common])}
            for threshold in (50, 100):
                mask = np.abs(v0) >= threshold
                f[f"n_patterns_ge{threshold}"] = int(mask.sum())
                f[f"median_abs_relative_voltage_pct_ge{threshold}"] = np.median(100 * np.abs(r[mask]))
            features.append(f)
            for k in range(208):
                patterns.append({"session": s["name"], "frequency_hz": s["freq"],
                    "task": task, "pattern_id": k, "label_provenance": "cue_assumed",
                    "force_pair": g.iloc[k].f_plus_site + "-" + g.iloc[k].f_minus_site,
                    "sense_pair": g.iloc[k].s_plus_site + "-" + g.iloc[k].s_minus_site,
                    "rest_real_counts": v0[k].real, "rest_imag_counts": v0[k].imag,
                    "task_real_counts": v1[k].real, "task_imag_counts": v1[k].imag,
                    "rest_magnitude_counts": abs(v0[k]),
                    "delta_real_counts": (v1[k] - v0[k]).real,
                    "delta_imag_counts": (v1[k] - v0[k]).imag,
                    "relative_voltage_real": r[k].real, "relative_voltage_imag": r[k].imag,
                    "relative_voltage_abs_pct": 100 * abs(r[k]),
                    "signed_magnitude_change_pct": 100 * magnitude_change[k],
                    "signed_phase_change_deg": phase_change[k],
                    "common_rest_ge50": bool(common[k]),
                    "start_s": g.iloc[k].start_s, "end_s": g.iloc[k].end_s})
    return pd.DataFrame(qc), pd.DataFrame(features), pd.DataFrame(patterns)


def save_plot(fig, out, name):
    fig.savefig(out / name, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_measurements(sessions, features, common, out):
    fig, axes = plt.subplots(3, 1, figsize=(12, 5.7), layout="constrained", sharex=True)
    for ax, s in zip(axes, sessions):
        tm = source.timing(s)
        for k, row in tm.iterrows():
            color = "#747d89" if row.task == "REST" else ("#286bb5" if "SMILE" in row.task else "#d57434")
            ax.broken_barh([(row.frame_start_s, row.frame_duration_s)], (0, .8), facecolors=color)
            ax.axvline(row.cue_s, color="#757575", lw=.8, ls=":")
            ax.text((row.frame_start_s + row.frame_end_s) / 2, .4,
                    NAMES[row.task].replace(" ", "\n", 1), ha="center", va="center", color="white", fontsize=9)
        ax.set_ylim(0, 1)
        ax.set_yticks([])
        ax.set_ylabel(f"{s['freq']//1000} kHz")
    axes[-1].set_xlabel("Seconds from session clock origin (not electrical phase)")
    fig.suptitle("One sequential 208-pattern scan per state; bars = acquisition, dotted lines = cues\n"
                 "Cue timing does not independently verify a stable facial pose", fontsize=12)
    save_plot(fig, out, "01_acquisition_timeline.png")

    fig, axes = plt.subplots(3, 1, figsize=(12, 7), layout="constrained", sharex=True)
    cmap = plt.get_cmap("viridis").copy()
    cmap.set_bad("#dddddd")
    values = []
    for ax, s in zip(axes, sessions):
        arr = np.array([100 * np.abs(relative_voltage(s["v"][t], s["v"]["REST"])) for t in TASKS])
        arr[:, ~common] = np.nan
        values.append(arr)
    upper = float(np.nanmax(values))
    for ax, s, arr in zip(axes, sessions, values):
        im = ax.imshow(arr, aspect="auto", interpolation="none", cmap=cmap, vmin=0, vmax=upper,
                       extent=(-.5, 207.5, 5.5, -.5))
        ax.set_yticks(range(6), [NAMES[t] for t in TASKS])
        ax.set_title(f"{s['freq']//1000} kHz", loc="left")
        for x in np.arange(12.5, 208, 13):
            ax.axvline(x, color="white", lw=.4, alpha=.5)
    axes[-1].set_xlabel("Measurement pattern ID (0-207); every 13 columns = one force pair; NOT image pixels")
    fig.colorbar(im, ax=axes, label="100 x |(task voltage - REST voltage) / REST voltage| (%)", shrink=.8)
    fig.suptitle(f"Voltage-change fingerprints: identical {common.sum()}-pattern subset at all frequencies\n"
                 "Grey = excluded because REST magnitude <50 counts in at least one session", fontsize=12)
    save_plot(fig, out, "02_voltage_change_fingerprints.png")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    for color, s in zip(COLORS, sessions):
        f = features[features.frequency_hz == s["freq"]].set_index("task").loc[list(TASKS)]
        axes[0].plot(range(6), f.median_abs_relative_voltage_pct_common, "o-", color=color,
                     label=f"{s['freq']//1000} kHz")
        axes[1].plot(range(6), f.median_signed_magnitude_change_pct_common, "o-", color=color)
    for ax in axes:
        ax.set_xticks(range(6), [NAMES[t].replace(" ", "\n", 1) for t in TASKS])
        ax.grid(axis="y", alpha=.2)
    axes[0].set_ylabel("Median absolute complex voltage change (%)")
    axes[0].set_title("How large is the combined magnitude/phase change?")
    axes[0].legend()
    axes[1].set_ylabel("Median signed voltage-magnitude change (%)")
    axes[1].axhline(0, color="#666", lw=.8)
    axes[1].set_title("Does sensed voltage magnitude increase or decrease?")
    fig.suptitle(f"Same {common.sum()} patterns in every panel; medians across patterns, not trial repeats\n"
                 "Lines connect task categories, not continuous time; no statistical error bars", fontsize=12)
    save_plot(fig, out, "03_task_change_summary.png")

    s = sessions[1]
    fig, axes = plt.subplots(1, 2, figsize=(11.7, 4.8), layout="constrained")
    v0 = s["v"]["REST"]
    axes[0].plot(np.abs(v0), color="#747d89", label="REST")
    axes[0].plot(np.abs(s["v"]["SMILE_BOTH"]), color="#b34236", label="Smile Both", alpha=.8)
    axes[0].axhline(50, color="#777", lw=.8, ls=":", label="50-count analysis threshold")
    axes[0].set_xlabel("Measurement pattern ID (not a pixel or electrode)")
    axes[0].set_ylabel("DFT voltage magnitude (uncalibrated counts)")
    axes[0].legend()
    axes[0].set_title("REST magnitude varies strongly with the four-electrode pattern")
    for t, color in zip(TASKS, plt.get_cmap("tab10").colors):
        ratio = s["v"][t][common] / v0[common]
        axes[1].scatter(100 * (np.abs(ratio) - 1), np.degrees(np.angle(ratio)),
                        s=16, color=color, alpha=.6, label=NAMES[t])
    axes[1].axhline(0, color="#777", lw=.8)
    axes[1].axvline(0, color="#777", lw=.8)
    axes[1].set_xlabel("Signed voltage-magnitude change (%)")
    axes[1].set_ylabel("Signed phase change (degrees)")
    axes[1].legend(fontsize=8, ncol=2)
    axes[1].set_title("Each dot = a pattern, not a repeated task or anatomical point")
    fig.suptitle("50 kHz: raw counts and complex relative changes measure different things", fontsize=12)
    save_plot(fig, out, "04_raw_and_complex_voltage.png")


def make_solvers(seq, selected, h0=.08):
    import pyeit.eit.bp as bp
    import pyeit.eit.jac as jac
    import pyeit.eit.greit as greit
    from pyeit.eit.protocol import PyEITProtocol
    from pyeit.mesh import create
    from pyeit.eit.fem import EITForward

    angles = np.deg2rad(101.25 + 22.5 * np.arange(16))
    xy = np.c_[np.cos(angles), np.sin(angles)]
    np.random.seed(20261005)
    mesh = create(16, h0=h0, p_fix=xy)
    rows = seq[selected]
    # Repeat the force pair for each selected measurement. This allows unequal
    # counts per force pair without filling excluded measurements with zeros.
    # pyEIT convention is V[N]-V[M], the reverse of the logger's named S+/S-.
    protocol = PyEITProtocol(ex_mat=rows[:, :2], meas_mat=rows[:, [3, 2]][:, None, :],
                            keep_ba=np.ones(len(rows), dtype=bool))
    vmodel = EITForward(mesh, protocol).solve_eit(perm=1.0)
    b = bp.BP(mesh, protocol)
    b.setup(weight="none", perm=1.0)
    j = jac.JAC(mesh, protocol)
    j.setup(p=.5, lamb=.01, method="kotre", perm=1.0, jac_normalized=True)
    g = greit.GREIT(mesh, protocol)
    g.setup(p=.5, lamb=.01, n=32, s=20., ratio=.1, perm=1.0, jac_normalized=True)
    return mesh, protocol, vmodel, {"BP": b, "JAC": j, "GREIT": g}


def project_ratio(q, mesh, vmodel, solvers):
    """Use REAL ratios to construct surrogate model volts, not calibrated volts.

    Standard normalized JAC/GREIT receive sign(vmodel)*q. BP in pyEIT 1.2.4
    uses its separate sign-only normalization. Record this distinction rather
    than claiming all algorithms have identical numerical input scaling.
    """
    v1 = vmodel * (1 + q)
    return {name: np.real(solver.solve(v1, vmodel, normalize=True))
            for name, solver in solvers.items()}


def draw_projection(ax, name, values, mesh, solvers, scale):
    norm = TwoSlopeNorm(vmin=-scale, vcenter=0, vmax=scale)
    if name == "BP":
        im = ax.tripcolor(mesh.node[:, 0], mesh.node[:, 1], mesh.element, values,
                          shading="gouraud", cmap="coolwarm", norm=norm)
    elif name == "JAC":
        im = ax.tripcolor(mesh.node[:, 0], mesh.node[:, 1], mesh.element, facecolors=values,
                          shading="flat", cmap="coolwarm", norm=norm)
    else:
        xg, yg, grid = solvers[name].mask_value(values.copy(), mask_value=np.nan)
        im = ax.pcolormesh(xg, yg, grid, cmap="coolwarm", norm=norm, shading="auto")
    xy = mesh.node[mesh.el_pos, :2]
    ax.scatter(xy[:, 0], xy[:, 1], s=6, c="black", zorder=5)
    ax.text(0, 1.1, "L1 / R1", ha="center", fontsize=7)
    ax.text(0, -1.16, "L8 / R8", ha="center", fontsize=7)
    ax.set_aspect("equal")
    ax.set_xlim(-1.16, 1.16)
    ax.set_ylim(-1.22, 1.2)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return im


def reconstruct_states(sessions, common, mesh, vm, solvers):
    """Every state uses REST from its own frequency session, including REST itself."""
    return {
        s["freq"]: {
            state: project_ratio(
                relative_voltage(s["v"][state], s["v"]["REST"])[common].real,
                mesh, vm, solvers)
            for state in STATES}
        for s in sessions}


def shared_image_scales(images):
    """One symmetric scale per algorithm, shared over all frequencies/states."""
    algorithms = next(iter(next(iter(images.values())).values())).keys()
    return {
        name: max(1e-12, max(float(np.max(np.abs(state_images[name])))
                             for states in images.values() for state_images in states.values()))
        for name in algorithms}


def plot_reconstruction_grid(images, row_specs, mesh, solvers, scales, out, name, title):
    """Columns are the seven states; rows specify (frequency, algorithm)."""
    fig, axes = plt.subplots(len(row_specs), len(STATES),
                             figsize=(15.4, 2.25 * len(row_specs) + .7),
                             layout="constrained", squeeze=False)
    mappables = {}
    for row, (freq, algorithm) in enumerate(row_specs):
        for col, state in enumerate(STATES):
            ax = axes[row, col]
            im = draw_projection(ax, algorithm, images[freq][state][algorithm],
                                 mesh, solvers, scales[algorithm])
            mappables[algorithm] = im
            if row == 0:
                ax.set_title("REST\n(self-reference)" if state == "REST" else NAMES[state])
            if col == 0:
                ax.set_ylabel(f"{algorithm}\n{freq//1000} kHz", fontsize=11, color="black")
            if state == "REST":
                ax.text(0, 0, "0 change\nby definition", ha="center", va="center",
                        fontsize=8, color="#4a4a4a")
    for algorithm, im in mappables.items():
        group = [ax for row, (_, a) in enumerate(row_specs) if a == algorithm for ax in axes[row]]
        ticks = np.linspace(-scales[algorithm], scales[algorithm], 5)
        bar = fig.colorbar(im, ax=group, shrink=.7,
                           ticks=ticks, label=f"{algorithm} image value (a.u.)")
        bar.ax.set_yticklabels([f"{tick:.4g}" for tick in ticks])
    fig.suptitle(title + "\n"
                 "Circular-model projections, not facial anatomy. Scale fixed per algorithm across all 3 frequencies.",
                 fontsize=12)
    save_plot(fig, out, name)


def reconstructions(sessions, common, out):
    from pyeit.eit.fem import EITForward
    mesh, protocol, vm, solvers = make_solvers(sessions[0]["seq"], common)
    images = reconstruct_states(sessions, common, mesh, vm, solvers)
    scales = shared_image_scales(images)
    frequency_figures = {
        10000: "05a_BP_JAC_GREIT_10000Hz_7states.png",
        50000: "05_exploratory_BP_JAC_GREIT.png",
        80000: "05c_BP_JAC_GREIT_80000Hz_7states.png"}
    for s in sessions:
        freq = s["freq"]
        plot_reconstruction_grid(images, [(freq, n) for n in solvers], mesh, solvers, scales,
                                 out, frequency_figures[freq],
                                 f"{freq//1000} kHz: BP / JAC / GREIT, all seven states relative to this session's REST")
    algorithm_figures = {}
    for index, n in enumerate(solvers, start=7):
        filename = f"{index:02d}_{n}_three_frequencies_7states.png"
        algorithm_figures[n] = filename
        plot_reconstruction_grid(images, [(s["freq"], n) for s in sessions], mesh, solvers, scales,
                                 out, filename,
                                 f"{n}: 10 / 50 / 80 kHz, all seven states relative to each session's own REST")
    overview_filename = "10_all_algorithms_frequencies_7states.png"
    plot_reconstruction_grid(images, [(s["freq"], n) for n in solvers for s in sessions],
                             mesh, solvers, scales, out, overview_filename,
                             "BP / JAC / GREIT x 10 / 50 / 80 kHz x seven states: 63 difference images")
    # Preserve legacy unprefixed 50-kHz task keys for existing readers; add
    # explicit frequency/state keys for all 63 images and GREIT grid geometry.
    xg, yg, grid_mask = solvers["GREIT"].get_grid()
    np.savez_compressed(out / "exploratory_images.npz", node=mesh.node, element=mesh.element,
                        el_pos=mesh.el_pos, selected_pattern_ids=np.flatnonzero(common),
                        model_reference_voltage=vm,
                        frequencies_hz=np.array([s["freq"] for s in sessions]),
                        states=np.array(STATES), greit_grid_x=xg, greit_grid_y=yg,
                        greit_outside_mask=grid_mask,
                        **{f"{freq}Hz_{state}_{n}": ims[n]
                           for freq, state_images in images.items() for state, ims in state_images.items()
                           for n in solvers},
                        **{t + "_" + n: images[50000][t][n] for t in TASKS for n in solvers})

    center = np.array([-.45, -.3])
    inside = np.linalg.norm(mesh.elem_centers[:, :2] - center, axis=1) < .2
    conductivity = np.ones(mesh.n_elems)
    conductivity[inside] = 1.10
    blob_v = EITForward(mesh, protocol).solve_eit(perm=conductivity)
    blob_q = blob_v / vm - 1
    drive = int(np.argmax(np.bincount(sessions[0]["seq"][common, 0], minlength=16)))
    drive_q = .03 * (sessions[0]["seq"][common, 0] == drive)
    controls = {
        "Known +10% conductivity blob\nSynthetic disk data, no added noise": project_ratio(blob_q, mesh, vm, solvers),
        "+2% voltage gain on every pattern\nNO internal conductivity change": project_ratio(np.full(len(vm), .02), mesh, vm, solvers),
        "+3% voltage gain on one force pair\nNO internal conductivity change": project_ratio(drive_q, mesh, vm, solvers)}
    fig, axes = plt.subplots(3, 3, figsize=(9.5, 9), layout="constrained")
    for row, (label, ims) in enumerate(controls.items()):
        for col, n in enumerate(solvers):
            scale = max(float(np.max(np.abs(ims[n]))), 1e-12)
            im = draw_projection(axes[row, col], n, ims[n], mesh, solvers, scale)
            if row == 0:
                axes[row, col].set_title(n)
            if col == 0:
                axes[row, col].set_ylabel(label, fontsize=9, color="black")
            if row == 0:
                axes[row, col].add_patch(plt.Circle(center, .2, fill=False, color="black", ls=":", lw=1))
            fig.colorbar(im, ax=axes[row, col], shrink=.65)
    fig.suptitle("Why an image alone cannot establish muscle activation\n"
                 "Synthetic diagnostic examples, individually scaled; not measured artifacts in this participant", fontsize=12)
    save_plot(fig, out, "06_model_sanity_and_gain_confound.png")
    checks = {"zero_change_produces_zero_image": all(
        np.allclose(v, 0) for v in project_ratio(np.zeros(len(vm)), mesh, vm, solvers).values()),
        "all_state_images_finite": all(np.isfinite(ims[n]).all()
            for states in images.values() for ims in states.values() for n in solvers),
        "all_rest_self_reference_images_zero": all(np.allclose(states["REST"][n], 0)
            for states in images.values() for n in solvers),
        "all_63_frequency_state_algorithm_images_present":
            sum(len(ims) for states in images.values() for ims in states.values()) == 3 * 7 * 3,
        "all_three_solvers_receive_selected_rows_only": all(sol.H.shape[1] == int(common.sum()) for sol in solvers.values())}
    peaks = {}
    for n, vals in next(iter(controls.values())).items():
        if n == "BP":
            pos = mesh.node[int(np.argmax(vals)), :2]
        elif n == "JAC":
            pos = mesh.elem_centers[int(np.argmax(vals)), :2]
        else:
            xg, yg, grid = solvers[n].mask_value(vals.copy(), mask_value=np.nan)
            ii = np.unravel_index(np.nanargmax(grid), grid.shape)
            pos = np.array([xg[ii], yg[ii]])
        peaks[n] = {"positive_peak_xy": pos.tolist(), "distance_from_blob_center": float(np.linalg.norm(pos - center))}
    params = {"interpretation": "Exploratory 2D circular-model projection; not facial anatomy",
        "input": "Re((Vtask-Vrest)/Vrest) on common REST>=50-count patterns",
        "surrogate_voltage": "model_v0 * (1 + real_relative_voltage_change)",
        "discarded_for_projection": "imaginary relative-voltage component",
        "frequencies_hz": [s["freq"] for s in sessions], "states": list(STATES),
        "n_images": 63,
        "reference": "Each frequency session's own REST; REST versus itself is identically zero",
        "rest_interpretation": "Zero difference by definition; not an absolute baseline conductivity map or noise estimate",
        "color_scale_abs_limit_per_algorithm_all_frequencies": scales,
        "figures_by_frequency_hz": frequency_figures, "figures_by_algorithm": algorithm_figures,
        "overview_figure": overview_filename,
        "archive_key_format": "<frequency>Hz_<STATE>_<ALGORITHM>; legacy unprefixed task keys denote 50 kHz",
        "n_selected_patterns": int(common.sum()), "selected_pattern_ids": np.flatnonzero(common).tolist(),
        "h0": .08, "n_nodes": mesh.n_nodes, "n_elements": mesh.n_elems,
        "background_relative_conductivity": 1., "radius": "1, dimensionless; not cm",
        "electrode_angles_deg": (101.25 + 22.5 * np.arange(16)).tolist(),
        "logical_site_order": sessions[0]["sites"],
        "BP": {"weight": "none", "normalized_difference": "(v1-v0)/sign(v0.real)"},
        "JAC": {"p": .5, "lambda": .01, "method": "kotre", "jac_normalized": True},
        "GREIT": {"p": .5, "lambda": .01, "n": 32, "s": 20., "ratio": .1, "jac_normalized": True},
        "known_blob": {"center": center.tolist(), "radius": .2, "conductivity": 1.1,
                       "peaks": peaks, "same_mesh_forward_inverse": True},
        "drive_gain_control_force_pair": [sessions[0]["sites"][drive], sessions[0]["sites"][(drive+1)%16]],
        "checks": checks,
        "validation": "Synthetic same-model consistency only; not hardware/geometry/muscle validation"}
    if not all(checks.values()):
        raise ValueError(f"Reconstruction consistency checks failed: {checks}")
    return params


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.out.resolve()
    sessions = [source.load_session(source.resolve_session(n)) for n in source.SESSION_NAMES]
    # Never allow a mistaken --out to replace files inside a source recording.
    for s in sessions:
        if out == s["path"].resolve() or s["path"].resolve() in out.parents:
            raise ValueError("Output directory must not be a raw session directory.")
    before = file_hashes(sessions)
    audits = {s["name"]: audit_session(s) for s in sessions}
    for s in sessions[1:]:
        if s["sites"] != sessions[0]["sites"] or not np.array_equal(s["seq"], sessions[0]["seq"]):
            raise ValueError("Cross-session protocol/mapping mismatch.")
    common = np.all([np.abs(s["v"]["REST"]) >= 50 for s in sessions], axis=0)
    if common.sum() == 0:
        raise ValueError("No common >=50-count patterns.")
    out.mkdir(parents=True, exist_ok=True)
    qc, features, patterns = tables(sessions, common)
    qc.to_csv(out / "qc_summary.csv", index=False)
    features.to_csv(out / "task_features.csv", index=False)
    patterns.to_csv(out / "pattern_voltage_changes.csv", index=False)
    pd.concat([source.timing(s) for s in sessions]).to_csv(out / "timeline.csv", index=False)
    pd.DataFrame(sessions[0]["meta"]["mapping"]["channels"]).to_csv(out / "recorded_electrode_map.csv", index=False)
    correlations = source.table_t4(sessions).rename(columns={
        "r_same_task_common_strong": "r_same_cued_task_common_ge50",
        "r_same_task_all_208": "r_same_cued_task_all_208"})
    correlations.to_csv(out / "cross_frequency_fingerprint_correlations.csv", index=False)
    plot_measurements(sessions, features, common, out)
    params = reconstructions(sessions, common, out)
    sample = patterns[(patterns.frequency_hz == 50000) & (patterns.task == "SMILE_BOTH") & (patterns.pattern_id == 0)].iloc[0].to_dict()
    r0 = np.array([1 + 2j, -3 + .4j])
    r1 = r0 * np.array([1.02 + .01j, .97 - .02j])
    gain = np.array([2j, -3 + 1j])
    checks = {"raw_hashes_unchanged": before == file_hashes(sessions),
              "fixed_complex_gain_cancels_in_voltage_ratio": bool(np.allclose(relative_voltage(r1, r0), relative_voltage(r1*gain, r0*gain))),
              "features_cover_18_task_frames": len(features) == 18,
              "pattern_changes_cover_18x208_rows": len(patterns) == 18 * 208}
    if not all(checks.values()):
        raise ValueError(f"Consistency checks failed: {checks}")
    summary = {"audits": audits, "qc": qc.to_dict("records"), "consistency_checks": checks,
        "common_ge50_patterns": int(common.sum()), "example_50k_smile_both_pattern0": sample,
        "correlation_min": float(correlations.r_same_cued_task_common_ge50.min()),
        "correlation_max": float(correlations.r_same_cued_task_common_ge50.max()),
        "label_provenance": "cue_assumed; first session additionally operator-reported",
        "noise_level": "Not estimated: only one REST frame per frequency; separate control not present",
        "reconstruction": params}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "raw_sha256.json").write_text(json.dumps(before, indent=2) + "\n")
    print(qc.to_string(index=False))
    print(features[["frequency_hz", "task", "median_abs_relative_voltage_pct_common", "median_abs_relative_voltage_pct_ge50", "median_abs_relative_voltage_pct_ge100"]].to_string(index=False))
    print("Checks:", checks)
    print("Known-blob positive peaks:", params["known_blob"]["peaks"])
    print("Output:", out)


if __name__ == "__main__":
    main()
