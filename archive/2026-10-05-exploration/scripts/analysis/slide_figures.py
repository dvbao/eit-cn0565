r"""Slide-sized versions of the three-frequency figures (Week 7 weekly report).

Same data and computations as ``three_frequency_report.py`` and
``algorithm_comparison.py``; only the layout is sized for a 10 x 5.63 in slide
(Arial, larger fonts). Output: data/processed/pilot/three-frequency-20261005/slides/

macOS/Linux:  .venv-sim/bin/python scripts/analysis/slide_figures.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

import algorithm_comparison as ac
import three_frequency_report as r

OUT = r.REPO / "data/processed/pilot/three-frequency-20261005/slides"
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9,
                     "xtick.labelsize": 8, "ytick.labelsize": 8})
SHORT = {t: t.replace("_", " ").title() for t in r.TASKS}


def save(fig, name):
    fig.savefig(OUT / name, dpi=220, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def s1_dz_heatmap(sessions):
    sites = sessions[0]["sites"]
    fig, axes = plt.subplots(3, 1, figsize=(9.4, 4.3), sharex=True, constrained_layout=True)
    for ax, s in zip(axes, sessions):
        strong = r.strong_mask(s)
        mat = np.array([100 * np.abs(r.dz_of(s, t)) for t in r.TASKS])
        mat[:, ~strong] = np.nan
        im = ax.imshow(np.ma.masked_invalid(mat), aspect="auto", cmap=r.SEQ, vmin=0, vmax=10, interpolation="none")
        ax.set_yticks(range(len(r.TASKS)))
        ax.set_yticklabels([SHORT[t] for t in r.TASKS], fontsize=7)
        ax.set_ylabel(r.freq_label(s["freq"]), fontsize=9, rotation=0, ha="right", va="center", labelpad=6)
        for g in range(1, r.N_EL):
            ax.axvline(g * 13 - 0.5, color=r.SURFACE, lw=0.8)
        for sp in ax.spines.values():
            sp.set_visible(False)
    axes[-1].set_xticks([g * 13 + 6 for g in range(r.N_EL)])
    axes[-1].set_xticklabels([f"{r.pair_label(sites, g)}" for g in range(r.N_EL)], rotation=90, fontsize=7)
    axes[-1].set_xlabel("208 measurements, grouped by current-drive pair (scan order)", fontsize=8.5)
    cb = fig.colorbar(im, ax=axes, shrink=0.85, extend="max", pad=0.01)
    cb.set_label("|relative change| vs REST (%)\ngrey = weak channel (|V| < 50 counts)", fontsize=8)
    save(fig, "S1_relative_change_heatmap.png")


def s2_lateralization(sessions, timings):
    t3 = r.table_t3(sessions, timings)
    freqs = [s["freq"] for s in sessions]
    fig, axes = plt.subplots(1, 3, figsize=(9.4, 3.0), sharey=True, constrained_layout=True)
    x = np.arange(len(r.TASKS))
    top = max(t3.L_median_abs_dz_pct.max(), t3.R_median_abs_dz_pct.max())
    for ax, f in zip(axes, freqs):
        d = t3[t3.freq_hz == f].set_index("task").loc[list(r.TASKS)]
        ax.bar(x - 0.2, d.L_median_abs_dz_pct, 0.38, color=r.SIDE_COLORS["L"], label="Left-only electrode patterns")
        ax.bar(x + 0.2, d.R_median_abs_dz_pct, 0.38, color=r.SIDE_COLORS["R"], label="Right-only electrode patterns")
        for xi, li in zip(x, d.LI):
            ax.text(xi, top * 1.07, f"{li:+.2f}", ha="center", fontsize=7.5, color=r.INK2)
        ax.set_ylim(0, top * 1.17)
        ax.set_xticks(x)
        ax.set_xticklabels([t.replace("_", "\n").title() for t in r.TASKS], fontsize=7.5)
        ax.set_title(f"{r.freq_label(f)}  (numbers = LI)", fontsize=9)
        ax.grid(axis="y", color=r.GRID, lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("median |change| vs REST (%)")
    fig.legend(*axes[0].get_legend_handles_labels(), frameon=False, fontsize=8, loc="lower center", ncol=2,
               bbox_to_anchor=(0.5, -0.08))
    save(fig, "S2_lateralization.png")


def s3_correlation(sessions):
    sel = r.common_strong(sessions)
    labels, feats = [], []
    for t in r.TASKS:
        for s in sessions:
            labels.append(f"{SHORT[t]}  {s['freq'] // 1000}k")
            feats.append(r.feature_vector(s, t, sel))
    mat = np.corrcoef(np.array(feats))
    fig, ax = plt.subplots(figsize=(5.4, 4.5), constrained_layout=True)
    im = ax.imshow(mat, cmap=r.DIV, norm=TwoSlopeNorm(0, -1, 1))
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=90, fontsize=6.5)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=6.5)
    for k in range(1, len(r.TASKS)):
        ax.axhline(3 * k - 0.5, color=r.SURFACE, lw=1.8)
        ax.axvline(3 * k - 0.5, color=r.SURFACE, lw=1.8)
    for sp in ax.spines.values():
        sp.set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cb.set_label("Pearson r of change patterns", fontsize=8)
    save(fig, "S3_task_frequency_correlation.png")


def disk_axes_labels(ax):
    kw = dict(ha="center", va="center", fontsize=6.5, color=r.INK2)
    ax.text(-1.5, 0, "L", **kw)
    ax.text(1.5, 0, "R", **kw)
    ax.text(0, 1.45, "forehead", **kw)
    ax.text(0, -1.45, "chin", **kw)


def s4_algorithms(sessions, solvers, images, metrics, freq=50000):
    snr = metrics.set_index(["algorithm", "freq_hz", "task"])["image_to_noise"]
    norms = ac.algo_norms(images, [s["freq"] for s in sessions])
    fig, axes = plt.subplots(3, len(r.TASKS), figsize=(9.4, 4.45), constrained_layout=True)
    for ri, a in enumerate(ac.ALGOS):
        for ci, t in enumerate(r.TASKS):
            ax = axes[ri, ci]
            im = ac.draw(ax, solvers, a, images[(a, freq, t)], norms[a])
            ax.set_xlim(-1.6, 1.6)
            ax.set_ylim(-1.75, 1.6)
            ax.text(0, -1.68, f"img/noise {snr[(a, freq, t)]:.1f}", ha="center", va="center", fontsize=6.5,
                    color=r.INK2)
            if ri == 0:
                ax.set_title(SHORT[t], fontsize=9)
            if ci == 0:
                ax.text(-2.0, 0, a, ha="right", va="center", fontsize=10, weight="bold")
                if ri == 0:
                    disk_axes_labels(ax)
        cb = fig.colorbar(im, ax=axes[ri, :], shrink=0.85, pad=0.01, aspect=12)
        cb.ax.tick_params(labelsize=6)
    fig.text(0.5, -0.045, "blue = less conductive than at REST, red = more conductive (2-D disk model, arbitrary units; "
             "one scale per algorithm)", ha="center", fontsize=7.5, color=r.INK2)
    save(fig, f"S4_bp_jac_greit_{freq // 1000}kHz.png")


def s5_greit_frequencies(sessions, solvers, images, metrics):
    snr = metrics.set_index(["algorithm", "freq_hz", "task"])["image_to_noise"]
    norm = ac.algo_norms(images, [s["freq"] for s in sessions])["GREIT"]
    fig, axes = plt.subplots(3, len(r.TASKS), figsize=(9.4, 4.45), constrained_layout=True)
    for ri, s in enumerate(sessions):
        f = s["freq"]
        for ci, t in enumerate(r.TASKS):
            ax = axes[ri, ci]
            im = ac.draw(ax, solvers, "GREIT", images[("GREIT", f, t)], norm)
            ax.set_xlim(-1.6, 1.6)
            ax.set_ylim(-1.75, 1.6)
            ax.text(0, -1.68, f"img/noise {snr[('GREIT', f, t)]:.1f}", ha="center", va="center", fontsize=6.5,
                    color=r.INK2)
            if ri == 0:
                ax.set_title(SHORT[t], fontsize=9)
            if ci == 0:
                ax.text(-2.0, 0, r.freq_label(f), ha="right", va="center", fontsize=10, weight="bold")
                if ri == 0:
                    disk_axes_labels(ax)
    cb = fig.colorbar(im, ax=axes, shrink=0.7, pad=0.01, aspect=25)
    cb.set_label("GREIT d(sigma) vs REST, a.u.", fontsize=7.5)
    cb.ax.tick_params(labelsize=6)
    fig.text(0.5, -0.045, "blue = less conductive than at REST, red = more conductive (2-D disk model, NOT anatomy)",
             ha="center", fontsize=7.5, color=r.INK2)
    save(fig, "S5_greit_three_frequencies.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sessions = sorted((r.load_session(r.resolve_session(n)) for n in r.SESSION_NAMES), key=lambda s: s["freq"])
    timings = {s["name"]: r.timing(s) for s in sessions}
    s1_dz_heatmap(sessions)
    s2_lateralization(sessions, timings)
    s3_correlation(sessions)
    solvers = ac.Solvers()
    images, metrics = ac.compute(sessions, solvers)
    s4_algorithms(sessions, solvers, images, metrics)
    s5_greit_frequencies(sessions, solvers, images, metrics)
    print(f"written to {OUT}")


if __name__ == "__main__":
    main()
