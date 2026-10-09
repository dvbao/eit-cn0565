"""All figures (English text only). Report figures, slide-sized figures and label-free images."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, LogNorm, TwoSlopeNorm  # noqa: E402

from .protocol import pair_label, ring_xy, to_matrix  # noqa: E402
from .recon import ALGOS  # noqa: E402

SURFACE, INK, INK2, GRID, MASK = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#d9d8d3"
# Validated categorical order; the first three slots are distinct in every pair (also for colour-blind viewers).
SESSION_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SIDE_COLORS = {"L": "#4a3aa7", "R": "#008300"}
SEQ = LinearSegmentedColormap.from_list(
    "seq_blue", ["#f4f8fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])
SEQ.set_bad(MASK)
DIV = LinearSegmentedColormap.from_list(
    "div_blue_red", ["#0d366b", "#2a78d6", "#9ec5f4", "#f0efec", "#f3b0ab", "#e34948", "#8f2322"])
DIV.set_bad(MASK)
DIV_CLEAR = DIV.copy()
DIV_CLEAR.set_bad((0, 0, 0, 0))
COLOR_NOTE = "blue = less conductive than at rest, red = more conductive (2-D disk model, arbitrary units)"


def use_style(font=None):
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "text.color": INK, "axes.labelcolor": INK2, "axes.edgecolor": GRID, "xtick.color": INK2,
        "ytick.color": INK2, "axes.titlesize": 10, "axes.labelsize": 9, "xtick.labelsize": 8,
        "ytick.labelsize": 8, "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
    })
    if font:
        plt.rcParams["font.family"] = font


def save(fig, path: Path, dpi=160, **kw):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", **kw)
    plt.close(fig)


def nice(task: str) -> str:
    return task.replace("_", " ").title()


def slug(label: str) -> str:
    return "".join(ch for ch in label if ch.isalnum() or ch in "-_")


def session_color(i: int) -> str:
    return SESSION_COLORS[i % len(SESSION_COLORS)]


# ---------------------------------------------------------------------------------------
# QC
# ---------------------------------------------------------------------------------------


def qc_timeline(timelines: list, labels: list, path: Path):
    fig, ax = plt.subplots(figsize=(11, 1.1 * len(labels) + 1.2))
    for row, (tl, lab) in enumerate(zip(timelines, labels)):
        y = len(labels) - 1 - row
        for r in tl.itertuples():
            ax.barh(y, r.next_cue_s - r.cue_s, left=r.cue_s, height=0.7, color=GRID, edgecolor=SURFACE, lw=2)
            ax.barh(y, r.frame_end_s - r.frame_start_s, left=r.frame_start_s, height=0.36,
                    color=session_color(row), edgecolor=SURFACE, lw=1)
            ax.text((r.cue_s + r.next_cue_s) / 2, y + 0.42, nice(r.task), ha="center", va="bottom", fontsize=6.5,
                    color=INK2)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(list(reversed(labels)))
    ax.set_xlabel("Time from session start (s)")
    ax.set_ylim(-0.6, len(labels) - 0.1)
    n_meas = "/".join(str(int(n)) for n in sorted({int(v) for t in timelines for v in t.n_measurements}))
    ax.set_title(f"Timeline: cue window (grey, cue to next cue) and each {n_meas}-measurement frame (colour)", loc="left")
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    save(fig, path)


def _matrix_axes(ax, sites, title, n_el, distances=None):
    force, sense = distances or (1, 1)
    ax.set_xticks(range(n_el))
    ax.set_xticklabels([pair_label(sites, i, sense) for i in range(n_el)], rotation=90, fontsize=5.5)
    ax.set_yticks(range(n_el))
    ax.set_yticklabels([pair_label(sites, i, force) for i in range(n_el)], fontsize=5.5)
    ax.set_xlabel("Sense pair (S+ - S-)", fontsize=7)
    ax.set_ylabel("Drive pair (F+ -> F-)", fontsize=7)
    ax.set_title(title, fontsize=8.5)
    for sp in ax.spines.values():
        sp.set_visible(False)


def qc_baseline_maps(sessions, labels, refs, strong_all, path: Path, strong_counts=50.0):
    n = len(sessions)
    s0 = sessions[0]
    fig, axes = plt.subplots(3, n, figsize=(4.4 * n, 13), constrained_layout=True, squeeze=False)
    vmax = max(np.abs(r).max() for r in refs)
    for c, (s, ref, lab) in enumerate(zip(sessions, refs, labels)):
        im = axes[0, c].imshow(np.ma.masked_invalid(to_matrix(np.abs(ref), s.seq, s.n_el)), cmap=SEQ, norm=LogNorm(1, vmax))
        _matrix_axes(axes[0, c], s.sites, f"|V_rest| (counts, log) - {lab}", s.n_el, s.ring_distances)
        if c == 0:
            mat = to_matrix(strong_all.astype(float), s.seq, s.n_el)
            im2 = axes[1, 0].imshow(np.ma.masked_invalid(mat), cmap=SEQ, vmin=0, vmax=1.4)
            _matrix_axes(axes[1, 0], s.sites, f"Strong in all sessions: n={int(strong_all.sum())}", s.n_el,
                         s.ring_distances)
        else:
            ratio = np.log2(np.abs(ref) / np.abs(refs[0]))
            im2 = axes[1, c].imshow(np.ma.masked_invalid(to_matrix(ratio, s.seq, s.n_el)), cmap=DIV, norm=TwoSlopeNorm(0, -1, 1))
            _matrix_axes(axes[1, c], s.sites, f"log2 |V_rest| ratio {lab} / {labels[0]}", s.n_el, s.ring_distances)
        dphi = np.degrees(np.angle(ref * np.exp(-1j * np.median(np.angle(ref)))))
        dphi[~(np.abs(ref) >= strong_counts)] = np.nan
        im3 = axes[2, c].imshow(np.ma.masked_invalid(to_matrix(dphi, s.seq, s.n_el)), cmap=DIV, norm=TwoSlopeNorm(0, -180, 180))
        _matrix_axes(axes[2, c], s.sites, f"Rest phase - session median (deg, strong) - {lab}", s.n_el,
                     s.ring_distances)
    fig.colorbar(im, ax=axes[0, :], shrink=0.7, label="|V_rest| counts")
    if n > 1:
        fig.colorbar(im2, ax=axes[1, 1:], shrink=0.7, label="log2 ratio (+1 = doubled)")
    fig.colorbar(im3, ax=axes[2, :], shrink=0.7, label="deg (+-180 = sign flip)")
    fig.suptitle(f"Rest maps: {s0.n_el} drive pairs x {s0.n_el} sense positions (grey = touches drive or masked)",
                 x=0.01, ha="left")
    save(fig, path)


# ---------------------------------------------------------------------------------------
# Relative change
# ---------------------------------------------------------------------------------------


def dz_heatmap(sessions, labels, aggs, masks, tasks, path: Path, vmax=10.0, slide=False):
    n = len(sessions)
    s0 = sessions[0]
    size = (9.4, 1.45 * n) if slide else (14, 2.5 * n)
    fig, axes = plt.subplots(n, 1, figsize=size, sharex=True, constrained_layout=True, squeeze=False)
    for ax, s, lab, agg, strong in zip(axes[:, 0], sessions, labels, aggs, masks):
        mat = np.array([100 * np.abs(agg[t]) if t in agg else np.full(s.n_pat, np.nan) for t in tasks])
        mat[:, ~strong] = np.nan
        im = ax.imshow(np.ma.masked_invalid(mat), aspect="auto", cmap=SEQ, vmin=0, vmax=vmax, interpolation="none")
        ax.set_yticks(range(len(tasks)))
        ax.set_yticklabels([nice(t) for t in tasks], fontsize=7)
        if slide:
            ax.set_ylabel(lab, fontsize=9, rotation=0, ha="right", va="center", labelpad=6)
        else:
            ax.set_title(f"{lab}  (grey = |V_rest| < threshold, n weak = {int((~strong).sum())})", loc="left", fontsize=8.5)
        per = s.n_pat // s.n_el
        for g in range(1, s.n_el):
            ax.axvline(g * per - 0.5, color=SURFACE, lw=0.8 if slide else 1)
        for sp in ax.spines.values():
            sp.set_visible(False)
    per = s0.n_pat // s0.n_el
    axes[-1, 0].set_xticks([g * per + per // 2 for g in range(s0.n_el)])
    force0 = s0.ring_distances[0] if s0.ring_distances else 1
    axes[-1, 0].set_xticklabels([pair_label(s0.sites, g, force0) for g in range(s0.n_el)], rotation=90, fontsize=7)
    axes[-1, 0].set_xlabel("Measurements grouped by drive pair (scan order)")
    cb = fig.colorbar(im, ax=axes[:, 0], shrink=0.85 if slide else 0.6, extend="max", pad=0.01)
    cb.set_label("|relative change| vs rest (%)\ngrey = weak channel", fontsize=8)
    if not slide:
        fig.suptitle("|dz| = |(V_task - V_rest) / V_rest| per measurement, same colour scale for all panels", x=0.01, ha="left")
    save(fig, path, dpi=220 if slide else 160)


def dz_re_vs_im(labels, aggs, masks, tasks, path: Path):
    ncol = 3
    nrow = int(np.ceil(len(tasks) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(13, 4 * nrow), sharex=True, sharey=True, constrained_layout=True,
                             squeeze=False)
    for ax, t in zip(axes.flat, tasks):
        for i, (lab, agg, strong) in enumerate(zip(labels, aggs, masks)):
            if t in agg:
                d = 100 * agg[t][strong]
                ax.scatter(d.real, d.imag, s=14, color=session_color(i), edgecolor=SURFACE, lw=0.6,
                           label=f"{lab} (n={int(strong.sum())})", alpha=0.9)
        ax.axhline(0, color=INK2, lw=0.6)
        ax.axvline(0, color=INK2, lw=0.6)
        ax.set_title(nice(t))
        ax.grid(color=GRID, lw=0.5)
        ax.set_axisbelow(True)
    for ax in axes.flat[len(tasks):]:
        ax.axis("off")
    for ax in axes[-1]:
        ax.set_xlabel("Re(dz) %  (~ relative amplitude change)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Im(dz) %  (~ phase change; 1% = 0.57 deg)")
    axes[0, 0].legend(frameon=False, fontsize=7.5)
    fig.suptitle("Amplitude vs phase component of dz, strong measurements", x=0.01, ha="left")
    save(fig, path)


def session_effect(labels, aggs, masks, tasks, path: Path):
    fig, axes = plt.subplots(1, len(tasks), figsize=(2.5 * len(tasks), 3.4), sharey=True, constrained_layout=True,
                             squeeze=False)
    xs = np.arange(len(labels))
    for ax, t in zip(axes[0], tasks):
        med, q1, q3 = [], [], []
        for agg, strong in zip(aggs, masks):
            d = 100 * np.abs(agg[t][strong]) if t in agg else np.array([np.nan])
            med.append(np.median(d))
            q1.append(np.percentile(d, 25))
            q3.append(np.percentile(d, 75))
        ax.fill_between(xs, q1, q3, color="#cde2fb", lw=0)
        ax.plot(xs, med, color="#184f95", lw=2, marker="o", ms=6, mec=SURFACE, mew=1.5)
        for xi, m in zip(xs, med):
            ax.annotate(f"{m:.1f}", (xi, m), xytext=(5, 5), textcoords="offset points", fontsize=7, color=INK2)
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, fontsize=7)
        ax.set_title(nice(t), fontsize=9)
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    axes[0, 0].set_ylabel("|dz| % on strong measurements\n(line = median, band = IQR)")
    fig.suptitle("Task effect per session (each point is a different session)", x=0.01, ha="left")
    save(fig, path)


def lateralization(lat, labels, tasks, path: Path, slide=False):
    n = len(labels)
    fig, axes = plt.subplots(1, n, figsize=(9.4, 3.0) if slide else (4.4 * n, 3.8), sharey=True,
                             constrained_layout=True, squeeze=False)
    x = np.arange(len(tasks))
    top = max(lat.L_median_abs_dz_pct.max(), lat.R_median_abs_dz_pct.max())
    for ax, lab in zip(axes[0], labels):
        d = lat[lat.label == lab].set_index("task").reindex(tasks)
        ax.bar(x - 0.2, d.L_median_abs_dz_pct, 0.38, color=SIDE_COLORS["L"], label="Left-only electrode measurements")
        ax.bar(x + 0.2, d.R_median_abs_dz_pct, 0.38, color=SIDE_COLORS["R"], label="Right-only electrode measurements")
        for xi, li in zip(x, d.LI):
            ax.text(xi, top * 1.07, f"{li:+.2f}", ha="center", fontsize=7.5 if slide else 7, color=INK2)
        ax.set_ylim(0, top * 1.17)
        ax.set_xticks(x)
        ax.set_xticklabels([t.replace("_", "\n").title() for t in tasks], fontsize=7.5 if slide else 7)
        ax.set_title(f"{lab}  (numbers = LI)", fontsize=9)
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.set_axisbelow(True)
    axes[0, 0].set_ylabel("median |dz| vs rest (%)")
    if slide:
        fig.legend(*axes[0, 0].get_legend_handles_labels(), frameon=False, fontsize=8, loc="lower center", ncol=2,
                   bbox_to_anchor=(0.5, -0.08))
    else:
        fig.legend(*axes[0, 0].get_legend_handles_labels(), frameon=False, fontsize=8, loc="upper right", ncol=2)
        fig.suptitle("Lateralisation: measurements using only left vs only right electrodes; LI = (L-R)/(L+R)",
                     x=0.01, ha="left")
    save(fig, path, dpi=220 if slide else 160)


def _corr_heatmap(ax, mat, names, annotate=True, fs=7):
    im = ax.imshow(mat, cmap=DIV, norm=TwoSlopeNorm(0, -1, 1))
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=90, fontsize=fs)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=fs)
    for sp in ax.spines.values():
        sp.set_visible(False)
    if annotate:
        for i in range(len(names)):
            for j in range(len(names)):
                ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", fontsize=fs - 1.5,
                        color=SURFACE if abs(mat[i, j]) > 0.6 else INK)
    return im


def task_correlation_within(labels, aggs, tasks, sel, feature_vector, path: Path):
    n = len(labels)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5), constrained_layout=True, squeeze=False)
    short = [nice(t) for t in tasks]
    for ax, lab, agg in zip(axes[0], labels, aggs):
        mat = np.corrcoef(np.array([feature_vector(agg[t], sel) for t in tasks]))
        im = _corr_heatmap(ax, mat, short, fs=8)
        ax.set_title(lab)
    fig.colorbar(im, ax=axes[0, :], shrink=0.8, label="Pearson r of [Re dz, Im dz]")
    fig.suptitle(f"Task x task correlation within each session (n={int(sel.sum())} measurements strong in all sessions)",
                 x=0.01, ha="left")
    save(fig, path)


def task_correlation_across(names, mat, n_sessions, path: Path, slide=False):
    shown = [f"{nice(n.split('|')[0])}  {n.split('|')[1]}" for n in names]
    fig, ax = plt.subplots(figsize=(5.4, 4.5) if slide else (11, 10), constrained_layout=True)
    im = _corr_heatmap(ax, mat, shown, annotate=not slide, fs=6.5 if slide else 7)
    for k in range(1, len(names) // max(n_sessions, 1)):
        ax.axhline(n_sessions * k - 0.5, color=SURFACE, lw=1.8)
        ax.axvline(n_sessions * k - 0.5, color=SURFACE, lw=1.8)
    cb = fig.colorbar(im, ax=ax, shrink=0.8 if slide else 0.7, pad=0.02)
    cb.set_label("Pearson r of change patterns", fontsize=8)
    if not slide:
        ax.set_title("Correlation of dz (task x session); diagonal blocks = same task in different sessions", loc="left")
    save(fig, path, dpi=220 if slide else 160)


def electrode_involvement(inv, labels, tasks, sites, path: Path):
    xy = ring_xy(len(sites))
    vmax = np.nanmax(inv[sites].to_numpy(float))
    fig, axes = plt.subplots(len(labels), len(tasks), figsize=(2.8 * len(tasks), 3 * len(labels)),
                             constrained_layout=True, squeeze=False)
    for r, lab in enumerate(labels):
        for c, t in enumerate(tasks):
            ax = axes[r, c]
            row = inv[(inv.label == lab) & (inv.task == t)]
            vals = row[sites].to_numpy(float)[0] if len(row) else np.full(len(sites), np.nan)
            ax.plot(np.r_[xy[:, 0], xy[0, 0]], np.r_[xy[:, 1], xy[0, 1]], color=GRID, lw=1, zorder=0)
            sc = ax.scatter(xy[:, 0], xy[:, 1], c=vals, cmap=SEQ, vmin=0, vmax=vmax, s=170, edgecolor=INK2, lw=0.6)
            for i, (x, y) in enumerate(xy):
                ax.text(1.28 * x, 1.28 * y, sites[i], ha="center", va="center", fontsize=6, color=INK2)
            ax.text(-1.45, 0, "L", fontsize=9, color=SIDE_COLORS["L"], ha="center", va="center", weight="bold")
            ax.text(1.45, 0, "R", fontsize=9, color=SIDE_COLORS["R"], ha="center", va="center", weight="bold")
            ax.set_xlim(-1.6, 1.6)
            ax.set_ylim(-1.45, 1.45)
            ax.set_aspect("equal")
            ax.axis("off")
            if r == 0:
                ax.set_title(nice(t), fontsize=9)
            if c == 0:
                ax.text(-1.75, 0, lab, rotation=90, va="center", ha="center", fontsize=9)
    fig.colorbar(sc, ax=axes, shrink=0.6, label="mean |dz| % of strong measurements using that electrode")
    fig.suptitle("Electrode involvement HEURISTIC (ring schematic; subject's left drawn left; top = forehead, "
                 "bottom = chin). NOT muscle localisation.", x=0.01, ha="left")
    save(fig, path)


def recognition_confusion(res, tasks, groups, path: Path):
    fig, ax = plt.subplots(figsize=(6.2, 5.4), constrained_layout=True)
    conf = res["confusion"]
    im = ax.imshow(conf, cmap=SEQ, vmin=0, vmax=max(1, conf.max()))
    for i in range(len(tasks)):
        for j in range(len(tasks)):
            ax.text(j, i, str(conf[i, j]), ha="center", va="center", color=SURFACE if conf[i, j] >= conf.max() * 0.6 else INK)
    ax.set_xticks(range(len(tasks)))
    ax.set_xticklabels([nice(t) for t in tasks], rotation=45, ha="right", fontsize=7.5)
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([nice(t) for t in tasks], fontsize=7.5)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Cued task")
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title(f"Leave-one-group-out nearest centroid ({len(groups)} groups)\n"
                 f"accuracy {res['accuracy']:.2f} (chance {res['chance']:.2f}), label-permutation p = {res['perm_p']:.4f}"
                 f"\n{res.get('caveat', '')}", loc="left", fontsize=8.5)
    fig.colorbar(im, ax=ax, shrink=0.7, label="count")
    save(fig, path)


# ---------------------------------------------------------------------------------------
# Reconstruction
# ---------------------------------------------------------------------------------------


def draw_disk(ax, solvers, algo, values, norm, label_sites=None, lim=1.35):
    if algo == "GREIT":
        grid = values.copy()
        grid[solvers.gmask] = np.nan
        grid = grid.reshape(solvers.xg.shape)
        im = ax.imshow(np.ma.masked_invalid(grid), origin="lower", cmap=DIV_CLEAR, norm=norm, interpolation="none",
                       extent=[solvers.xg.min(), solvers.xg.max(), solvers.yg.min(), solvers.yg.max()])
    elif algo == "JAC":
        im = ax.tripcolor(solvers.tri, facecolors=values, cmap=DIV, norm=norm, shading="flat")
    else:
        im = ax.tripcolor(solvers.tri, values, cmap=DIV, norm=norm, shading="gouraud")
    el = solvers.xy[solvers.mesh.el_pos]
    ax.scatter(el[:, 0], el[:, 1], s=6, color=INK, zorder=3)
    if label_sites is not None:
        for i, (x, y) in enumerate(el):
            ax.text(1.22 * x, 1.22 * y, label_sites[i], ha="center", va="center", fontsize=5.5, color=INK2)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.axis("off")
    return im


def algo_norms(images: dict) -> dict:
    norms = {}
    for a in ALGOS:
        vals = [np.abs(v) for (alg, _, _), v in images.items() if alg == a]
        lim = float(np.percentile(np.concatenate(vals), 99))
        norms[a] = TwoSlopeNorm(0, -lim, lim)
    return norms


def recon_compare_by_session(solvers, images, labels, tasks, path: Path, row_labels=True, clean=False):
    """Rows grouped by session (BP, JAC, GREIT for each), columns = tasks; one colour scale per algorithm."""
    norms = algo_norms(images)
    heights = []
    for gi in range(len(labels)):
        heights += [1] * len(ALGOS) + ([0.25] if gi < len(labels) - 1 else [])
    if row_labels:
        heights += [0.12, 0.1]
    ncols = max(len(tasks), len(ALGOS)) if row_labels else len(tasks)  # room for the three colour bars
    fig = plt.figure(figsize=(2 * ncols + (1.4 if row_labels else 0), 2 * sum(heights) + 0.5))
    gs = fig.add_gridspec(len(heights), ncols, height_ratios=heights, wspace=0.05, hspace=0.05)
    row = 0
    for lab in labels:
        for a in ALGOS:
            for ci, t in enumerate(tasks):
                ax = fig.add_subplot(gs[row, ci])
                if (a, lab, t) in images:
                    draw_disk(ax, solvers, a, images[(a, lab, t)], norms[a], lim=1.08)
                else:
                    ax.axis("off")
                if row == 0:
                    ax.set_title(nice(t), fontsize=14)
                if row_labels and ci == 0:
                    ax.text(-1.25, 0, f"{a}\n{lab}", ha="right", va="center", fontsize=13)
            row += 1
        row += 1
    if row_labels:
        for k, a in enumerate(ALGOS):
            span = max(1, ncols // len(ALGOS))
            cax = fig.add_subplot(gs[len(heights) - 1, span * k:span * k + span])
            cb = fig.colorbar(ScalarMappable(norm=norms[a], cmap=DIV), cax=cax, orientation="horizontal")
            cb.ax.tick_params(labelsize=9)
            cb.ax.set_title(a, fontsize=11)
    save(fig, path, dpi=200, transparent=clean, pad_inches=0.05)


def recon_known_target(solvers, kt, sites, path: Path):
    fig, axes = plt.subplots(2, 4, figsize=(11, 6), constrained_layout=True)
    for r, (key, label) in enumerate([("clean", "no noise"), ("noisy", "+ measured-level noise")]):
        tlim = float(np.abs(kt["perm"] - 1.0).max()) or 0.5
        draw_disk(axes[r, 0], solvers, "JAC", kt["perm"] - 1.0, TwoSlopeNorm(0, -tlim, tlim),
                  label_sites=sites if r == 0 else None)
        axes[r, 0].set_title(f"truth: conductivity blob\n({label})", fontsize=8)
        for c, a in enumerate(ALGOS, start=1):
            lim = np.abs(kt["clean"][a]).max()
            draw_disk(axes[r, c], solvers, a, kt[key][a], TwoSlopeNorm(0, -lim, lim))
            axes[r, c].set_title(a, fontsize=9)
    fig.suptitle("Known-target check on the same disk, electrode ring and channel mask as the first session\n"
                 f"median |change| of this blob on kept channels = {kt['median_abs_change_pct']:.2f}%",
                 x=0.01, ha="left", fontsize=9)
    save(fig, path)


def slide_algorithms(solvers, images, metrics, lab, tasks, path: Path):
    snr = metrics.set_index(["algorithm", "label", "task"])["image_to_noise"]
    norms = algo_norms(images)
    fig, axes = plt.subplots(3, len(tasks), figsize=(9.4, 4.45), constrained_layout=True, squeeze=False)
    for ri, a in enumerate(ALGOS):
        for ci, t in enumerate(tasks):
            ax = axes[ri, ci]
            im = draw_disk(ax, solvers, a, images[(a, lab, t)], norms[a])
            ax.set_xlim(-1.6, 1.6)
            ax.set_ylim(-1.75, 1.6)
            ax.text(0, -1.68, f"img/noise {snr[(a, lab, t)]:.1f}", ha="center", va="center", fontsize=6.5, color=INK2)
            if ri == 0:
                ax.set_title(nice(t), fontsize=9)
            if ci == 0:
                ax.text(-2.0, 0, a, ha="right", va="center", fontsize=10, weight="bold")
                if ri == 0:
                    _orientation(ax)
        cb = fig.colorbar(im, ax=axes[ri, :], shrink=0.85, pad=0.01, aspect=12)
        cb.ax.tick_params(labelsize=6)
    fig.text(0.5, -0.045, COLOR_NOTE + "; one scale per algorithm", ha="center", fontsize=7.5, color=INK2)
    save(fig, path, dpi=220)


def slide_greit_sessions(solvers, images, metrics, labels, tasks, path: Path):
    snr = metrics.set_index(["algorithm", "label", "task"])["image_to_noise"]
    norm = algo_norms(images)["GREIT"]
    fig, axes = plt.subplots(len(labels), len(tasks), figsize=(9.4, 1.48 * len(labels)), constrained_layout=True,
                             squeeze=False)
    for ri, lab in enumerate(labels):
        for ci, t in enumerate(tasks):
            ax = axes[ri, ci]
            im = draw_disk(ax, solvers, "GREIT", images[("GREIT", lab, t)], norm)
            ax.set_xlim(-1.6, 1.6)
            ax.set_ylim(-1.75, 1.6)
            ax.text(0, -1.68, f"img/noise {snr[('GREIT', lab, t)]:.1f}", ha="center", va="center", fontsize=6.5,
                    color=INK2)
            if ri == 0:
                ax.set_title(nice(t), fontsize=9)
            if ci == 0:
                ax.text(-2.0, 0, lab, ha="right", va="center", fontsize=10, weight="bold")
                if ri == 0:
                    _orientation(ax)
    cb = fig.colorbar(im, ax=axes, shrink=0.7, pad=0.01, aspect=25)
    cb.set_label("GREIT d(sigma) vs rest, a.u.", fontsize=7.5)
    cb.ax.tick_params(labelsize=6)
    fig.text(0.5, -0.045, COLOR_NOTE + "; NOT anatomy", ha="center", fontsize=7.5, color=INK2)
    save(fig, path, dpi=220)


def _orientation(ax):
    kw = dict(ha="center", va="center", fontsize=6.5, color=INK2)
    ax.text(-1.5, 0, "L", **kw)
    ax.text(1.5, 0, "R", **kw)
    ax.text(0, 1.45, "forehead", **kw)
    ax.text(0, -1.45, "chin", **kw)


def clean_images(solvers, images, labels, tasks, out: Path):
    """Label-free images: single disks, grids and colour bars (transparent background)."""
    norms = algo_norms(images)
    for (a, lab, t), vals in images.items():
        fig = plt.figure(figsize=(2, 2))
        draw_disk(fig.add_axes([0, 0, 1, 1]), solvers, a, vals, norms[a], lim=1.08)
        p = out / a / f"{slug(lab)}_{t}.png"
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, dpi=300, transparent=True)
        plt.close(fig)
    for a in ALGOS:
        fig = plt.figure(figsize=(0.55, 3))
        cax = fig.add_axes([0.05, 0.03, 0.3, 0.94])
        cb = fig.colorbar(ScalarMappable(norm=norms[a], cmap=DIV), cax=cax)
        cb.ax.tick_params(labelsize=8)
        save(fig, out / f"colorbar_{a}.png", dpi=300, transparent=True)
    recon_compare_by_session(solvers, images, labels, tasks, out / "compare_by_session_tasks_only.png",
                             row_labels=False, clean=True)
    lines = [
        "Label-free reconstructions: change of each task relative to rest (time-difference), 2-D disk model.",
        "Orientation: subject's left drawn on the left; top = forehead (L1/R1); bottom = chin (L8/R8).",
        "Colour: blue = less conductive than at rest, red = more conductive (in the 2-D model); arbitrary units.",
        "One colour scale per algorithm, shared by all sessions and tasks (symmetric, 99th percentile).",
        "",
        f"Columns (left to right): {', '.join(tasks)}",
        "compare_by_session_tasks_only.png rows (top to bottom, gap between sessions): "
        + "; ".join(f"BP, JAC, GREIT at {lab}" for lab in labels),
        "",
        "Colour-scale limits (+/-):",
    ] + [f"  {a}: {norms[a].vmax:.4g}" for a in ALGOS]
    (out / "README.txt").write_text("\n".join(lines) + "\n")
