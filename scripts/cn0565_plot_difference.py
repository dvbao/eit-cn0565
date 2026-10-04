"""Plot complete-frame voltage changes; this is not an EIT anatomical image.

First select stable frames with cn0565_prepare_difference.py, then:
    python3 scripts/cn0565_plot_difference.py --comparison trial.json --output trial.png
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from cn0565_prepare_difference import load_selected_frames, rms_difference


def plot_comparison(comparison_path: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite: {output}")
    result = json.loads(comparison_path.read_text(encoding="utf-8"))
    prefix = Path(result["source_prefix"])
    with Path(f"{prefix}.frames.csv").open(newline="", encoding="utf-8") as stream:
        timing = list(csv.DictReader(stream))
    if not timing:
        raise ValueError("No complete frames found")
    ids = [int(row["frame_id"]) for row in timing]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate frame IDs in timing file")
    frames = load_selected_frames(prefix, set(ids), result["switch_sequence"])
    baseline = result["v0_real_imag_raw"]
    delta = result["delta_real_imag_raw"]
    if len(baseline) != len(result["switch_sequence"]) or len(delta) != len(baseline):
        raise ValueError("Comparison vector length does not match sequence")
    origin = int(timing[0]["start_monotonic_ns"])
    midpoint, half_span = [], []
    for row in timing:
        start, end = int(row["start_monotonic_ns"]), int(row["end_monotonic_ns"])
        if end < start:
            raise ValueError("Invalid frame interval")
        midpoint.append(((start - origin) + (end - origin)) / 2e9)
        half_span.append((end - start) / 2e9)
    distance = [rms_difference(frames[frame_id], baseline) for frame_id in ids]
    if not all(math.isfinite(value) for value in distance):
        raise ValueError("Invalid comparison baseline")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(3, 1, figsize=(11, 9), constrained_layout=True)
    axes[0].errorbar(midpoint, distance, xerr=half_span, fmt=".", color="0.65",
                     alpha=0.8, label="All complete frames; bars = acquisition intervals")
    for label, key, color in (
        ("Selected pre-rest", "rest_frame_ids", "#1976a3"),
        ("Selected task", "task_frame_ids", "#b94b18"),
        ("Selected post-rest/control", "post_rest_frame_ids", "#348448"),
    ):
        selected = set(result.get(key, []))
        if not selected <= set(ids):
            raise ValueError(f"Missing frames for {label}")
        positions = [i for i, frame_id in enumerate(ids) if frame_id in selected]
        if positions:
            axes[0].scatter([midpoint[i] for i in positions], [distance[i] for i in positions],
                            color=color, label=label, zorder=3, s=25)
    axes[0].set(xlabel="Time since first frame start (s)", ylabel="RMS complex difference (raw units)",
                title="Frame-by-frame distance from selected pre-rest baseline")
    axes[0].legend(fontsize=8, loc="best")
    post_delta = result.get("post_rest_minus_rest_real_imag_raw")
    for component, ax in enumerate(axes[1:]):
        ax.plot(range(len(delta)), [value[component] for value in delta],
                color="#b94b18", linewidth=1.2, label="Task median - pre-rest median")
        if post_delta:
            ax.plot(range(len(delta)), [value[component] for value in post_delta],
                    color="#348448", linewidth=1.0, label="Post-rest median - pre-rest median")
        ax.axhline(0, color="0.4", linewidth=0.7)
        ax.set(xlabel="Four-terminal measurement pattern ID (not a face location)",
               ylabel=f"{'Real' if component == 0 else 'Imaginary'} difference (raw units)")
        ax.legend(fontsize=8)
    for ax in axes:
        ax.grid(alpha=0.18)
    fig.suptitle("Rest-task voltage comparison | no spatial or muscle-specific inference", fontsize=12)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(output, dpi=150)
    finally:
        plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    plot_comparison(args.comparison, args.output)
    print(f"Saved {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
