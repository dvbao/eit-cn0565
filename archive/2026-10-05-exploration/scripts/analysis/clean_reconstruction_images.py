r"""Label-free BP / JAC / GREIT images for the 10 / 50 / 80 kHz sessions (for manual layout).

Same reconstruction as ``algorithm_comparison.py`` (time-difference vs REST, pyEIT
settings of ``eit_sim_playground.py``, weak channels removed). No titles, labels,
img/noise or colour bars on the images; transparent background; electrode dots kept.
One colour scale per algorithm, shared by all frequencies and tasks.

Output: data/processed/pilot/three-frequency-20261005/algorithms/clean/
    <ALGO>/<freq>kHz_<TASK>.png    54 single disks
    grid_<freq>kHz.png             rows BP, JAC, GREIT; columns = tasks
    grid_<ALGO>.png                rows 10, 50, 80 kHz; columns = tasks
    colorbar_<ALGO>.png            colour scale (numbers only)
    README.txt                     row/column order and scale limits

macOS/Linux:  .venv-sim/bin/python scripts/analysis/clean_reconstruction_images.py
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import ScalarMappable

import algorithm_comparison as ac
import three_frequency_report as r

OUT = r.REPO / "data/processed/pilot/three-frequency-20261005/algorithms/clean"
LIM = 1.08  # axis half-width: disk radius 1 plus the electrode dots


def disk(ax, solvers, algo, values, norm):
    ac.draw(ax, solvers, algo, values, norm)
    ax.set_xlim(-LIM, LIM)
    ax.set_ylim(-LIM, LIM)


def single(solvers, algo, values, norm, path):
    fig = plt.figure(figsize=(2, 2))
    disk(fig.add_axes([0, 0, 1, 1]), solvers, algo, values, norm)
    fig.savefig(path, dpi=300, transparent=True)
    plt.close(fig)


def grid(solvers, rows, images, norms, path):
    """rows: list of (algo, freq); columns are the six tasks."""
    fig, axes = plt.subplots(len(rows), len(r.TASKS), figsize=(2 * len(r.TASKS), 2 * len(rows)),
                             gridspec_kw={"wspace": 0.05, "hspace": 0.05})
    for ri, (a, f) in enumerate(rows):
        for ci, t in enumerate(r.TASKS):
            disk(axes[ri, ci], solvers, a, images[(a, f, t)], norms[a])
    fig.savefig(path, dpi=200, transparent=True, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def grid_all(solvers, freqs, images, norms, path, labels=False):
    """9 rows (BP, JAC, GREIT x 10/50/80 kHz) x 6 task columns, with a gap between algorithms."""
    heights = []
    for gi in range(len(ac.ALGOS)):
        heights += [1] * len(freqs) + ([0.25] if gi < len(ac.ALGOS) - 1 else [])
    fig = plt.figure(figsize=(2 * len(r.TASKS) + (1.6 if labels else 0), 2 * sum(heights) + (0.5 if labels else 0)))
    gs = fig.add_gridspec(len(heights), len(r.TASKS) + (1 if labels else 0), height_ratios=heights,
                          width_ratios=[1] * len(r.TASKS) + ([0.08] if labels else []), wspace=0.05, hspace=0.05)
    row = 0
    for gi, a in enumerate(ac.ALGOS):
        for fi, f in enumerate(freqs):
            for ci, t in enumerate(r.TASKS):
                ax = fig.add_subplot(gs[row, ci])
                disk(ax, solvers, a, images[(a, f, t)], norms[a])
                if labels and row == 0:
                    ax.set_title(t.replace("_", " ").title(), fontsize=13)
                if labels and ci == 0:
                    ax.text(-1.25, 0, f"{a}\n{f // 1000} kHz", ha="right", va="center", fontsize=13)
            row += 1
        if labels:
            cax = fig.add_subplot(gs[row - len(freqs):row, len(r.TASKS)])
            cb = fig.colorbar(ScalarMappable(norm=norms[a], cmap=r.DIV), cax=cax)
            cb.ax.tick_params(labelsize=9)
        row += 1
    fig.savefig(path, dpi=200, transparent=not labels, bbox_inches="tight", pad_inches=0.05,
                facecolor=None if not labels else "white")
    plt.close(fig)


def grid_by_frequency(solvers, freqs, images, norms, path, row_labels=True):
    """Rows grouped by frequency (BP, JAC, GREIT at 10 kHz, then 50, then 80); task names on top.

    ``row_labels`` also adds algorithm/frequency labels and three colour bars at the bottom.
    """
    heights = []
    for gi in range(len(freqs)):
        heights += [1] * len(ac.ALGOS) + ([0.25] if gi < len(freqs) - 1 else [])
    if row_labels:
        heights += [0.12, 0.1]
    fig = plt.figure(figsize=(2 * len(r.TASKS) + (1.4 if row_labels else 0), 2 * sum(heights) + 0.5))
    gs = fig.add_gridspec(len(heights), len(r.TASKS), height_ratios=heights, wspace=0.05, hspace=0.05)
    row = 0
    for f in freqs:
        for a in ac.ALGOS:
            for ci, t in enumerate(r.TASKS):
                ax = fig.add_subplot(gs[row, ci])
                disk(ax, solvers, a, images[(a, f, t)], norms[a])
                if row == 0:
                    ax.set_title(t.replace("_", " ").title(), fontsize=14)
                if row_labels and ci == 0:
                    ax.text(-1.25, 0, f"{a}\n{f // 1000} kHz", ha="right", va="center", fontsize=13)
            row += 1
        row += 1
    if row_labels:
        for k, a in enumerate(ac.ALGOS):
            cax = fig.add_subplot(gs[len(heights) - 1, 2 * k:2 * k + 2])
            cb = fig.colorbar(ScalarMappable(norm=norms[a], cmap=r.DIV), cax=cax, orientation="horizontal")
            cb.ax.tick_params(labelsize=9)
            cb.ax.set_title(a, fontsize=11)
    fig.savefig(path, dpi=200, transparent=not row_labels, bbox_inches="tight", pad_inches=0.05,
                facecolor="white" if row_labels else None)
    plt.close(fig)


def colorbar(norm, path):
    fig = plt.figure(figsize=(0.55, 3))
    cax = fig.add_axes([0.05, 0.03, 0.3, 0.94])
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=r.DIV), cax=cax)
    cb.ax.tick_params(labelsize=8)
    fig.savefig(path, dpi=300, transparent=True, bbox_inches="tight")
    plt.close(fig)


def main():
    sessions = sorted((r.load_session(r.resolve_session(n)) for n in r.SESSION_NAMES), key=lambda s: s["freq"])
    freqs = [s["freq"] for s in sessions]
    solvers = ac.Solvers()
    images, _ = ac.compute(sessions, solvers)
    norms = ac.algo_norms(images, freqs)
    for a in ac.ALGOS:
        (OUT / a).mkdir(parents=True, exist_ok=True)
        for f in freqs:
            for t in r.TASKS:
                single(solvers, a, images[(a, f, t)], norms[a], OUT / a / f"{f // 1000}kHz_{t}.png")
        grid(solvers, [(a, f) for f in freqs], images, norms, OUT / f"grid_{a}.png")
        colorbar(norms[a], OUT / f"colorbar_{a}.png")
    for f in freqs:
        grid(solvers, [(a, f) for a in ac.ALGOS], images, norms, OUT / f"grid_{f // 1000}kHz.png")
    grid_all(solvers, freqs, images, norms, OUT / "compare_all.png")
    grid_all(solvers, freqs, images, norms, OUT.parent / "compare_all_labeled.png", labels=True)
    grid_by_frequency(solvers, freqs, images, norms, OUT.parent / "compare_by_frequency_labeled.png")
    grid_by_frequency(solvers, freqs, images, norms, OUT / "compare_by_frequency_tasks.png", row_labels=False)

    tasks = ", ".join(r.TASKS)
    lines = [
        "Label-free reconstructions: change of each task relative to REST (time-difference), 2-D disk model.",
        "Orientation: subject's left drawn on the left; top = forehead (L1/R1); bottom = chin (L8/R8).",
        "Colour: blue = less conductive than at REST, red = more conductive (in the 2-D model); arbitrary units.",
        "One colour scale per algorithm, shared by all frequencies and tasks (symmetric, 99th percentile).",
        "",
        f"Columns of every grid (left to right): {tasks}",
        "grid_<freq>kHz.png rows (top to bottom): BP, JAC, GREIT",
        "grid_<ALGO>.png rows (top to bottom): 10 kHz, 50 kHz, 80 kHz",
        "compare_all.png rows (top to bottom, gap between algorithms): BP 10/50/80 kHz, JAC 10/50/80 kHz, "
        "GREIT 10/50/80 kHz",
        "(a labelled copy with colour bars is ../compare_all_labeled.png)",
        "compare_by_frequency_tasks.png rows (top to bottom, gap between frequencies): BP, JAC, GREIT at 10 kHz; "
        "BP, JAC, GREIT at 50 kHz; BP, JAC, GREIT at 80 kHz; task names on top",
        "(a copy with row labels and colour bars is ../compare_by_frequency_labeled.png)",
        "",
        "Colour-scale limits (+/-):",
    ]
    lines += [f"  {a}: {norms[a].vmax:.4g}" for a in ac.ALGOS]
    (OUT / "README.txt").write_text("\n".join(lines) + "\n")
    print(f"written to {OUT}")


if __name__ == "__main__":
    main()
