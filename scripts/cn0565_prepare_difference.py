"""Select complete rest/task frames from a CN0565 capture and form v0/v1.

This script does not perform image reconstruction. Choose frame IDs only after
checking cue/video timing and excluding transitional or visibly bad frames.

Example:
    python3 scripts/cn0565_prepare_difference.py \
        --input-prefix data/raw/bench-01 --rest-frames 1,2,3 \
        --task-frames 7,8,9 --output data/processed/bench-01-trial-01.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path


def parse_frame_ids(value: str) -> list[int]:
    try:
        ids = [int(part.strip()) for part in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Frame IDs must be comma-separated integers") from exc
    if not ids or any(number < 0 for number in ids) or len(ids) != len(set(ids)):
        raise argparse.ArgumentTypeError("Frame IDs must be unique nonnegative integers")
    return ids


def load_selected_frames(prefix: Path, selected: set[int], sequence: list[list[int]]) -> dict[int, list[tuple[float, float]]]:
    pattern_count = len(sequence)
    frames: dict[int, dict[int, tuple[float, float]]] = {frame_id: {} for frame_id in selected}
    with Path(f"{prefix}.voltages.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            frame_id = int(row["frame_id"])
            if frame_id not in selected:
                continue
            pattern_id = int(row["pattern_id"])
            if not 0 <= pattern_id < pattern_count:
                raise ValueError(f"Out-of-range pattern {pattern_id} in frame {frame_id}")
            if pattern_id in frames[frame_id]:
                raise ValueError(f"Duplicate pattern {pattern_id} in frame {frame_id}")
            observed = [int(row[key]) for key in (
                "f_plus_index", "s_plus_index", "s_minus_index", "f_minus_index"
            )]
            if observed != sequence[pattern_id]:
                raise ValueError(f"Pattern order mismatch in frame {frame_id}, pattern {pattern_id}")
            real, imag = float(row["real_raw"]), float(row["imag_raw"])
            if not (math.isfinite(real) and math.isfinite(imag)):
                raise ValueError(f"Nonfinite voltage in frame {frame_id}, pattern {pattern_id}")
            frames[frame_id][pattern_id] = (real, imag)
    for frame_id, patterns in frames.items():
        if len(patterns) != pattern_count:
            raise ValueError(f"Frame {frame_id} has {len(patterns)} of {pattern_count} patterns")
    return {
        frame_id: [patterns[index] for index in range(pattern_count)]
        for frame_id, patterns in frames.items()
    }


def median_vector(frames: dict[int, list[tuple[float, float]]], frame_ids: list[int]) -> list[list[float]]:
    count = len(frames[frame_ids[0]])
    return [
        [statistics.median(frames[frame_id][pattern_id][component] for frame_id in frame_ids)
         for component in (0, 1)]
        for pattern_id in range(count)
    ]


def rms_difference(vector: list[list[float]], reference: list[list[float]]) -> float:
    """RMS complex voltage difference across patterns, in uncalibrated raw units."""
    return math.sqrt(sum(
        (value[0] - ref[0]) ** 2 + (value[1] - ref[1]) ** 2
        for value, ref in zip(vector, reference)
    ) / len(reference))


def prepare(prefix: Path, rest_ids: list[int], task_ids: list[int],
            post_rest_ids: list[int] | None = None) -> dict:
    post_rest_ids = post_rest_ids or []
    if not rest_ids or not task_ids:
        raise ValueError("Rest and task selections must be nonempty")
    if set(rest_ids) & set(task_ids):
        raise ValueError("Rest and task frame sets overlap")
    if set(post_rest_ids) & (set(rest_ids) | set(task_ids)):
        raise ValueError("Post-rest frame set overlaps rest or task")
    meta = json.loads(Path(f"{prefix}.meta.json").read_text(encoding="utf-8"))
    if meta["status"] != "complete":
        raise ValueError("Capture is incomplete; inspect files before analysis")
    sequence = meta["switch_sequence"]
    selected = set(rest_ids) | set(task_ids) | set(post_rest_ids)
    frames = load_selected_frames(prefix, selected, sequence)
    v0 = median_vector(frames, rest_ids)
    v1 = median_vector(frames, task_ids)
    result = {
        "source_prefix": str(prefix.resolve()),
        "layout_id": meta["mapping"]["layout_id"],
        "sequence_order": meta["sequence_order"],
        "switch_sequence": sequence,
        "rest_frame_ids": rest_ids,
        "task_frame_ids": task_ids,
        "post_rest_frame_ids": post_rest_ids,
        "aggregation": "componentwise median of selected complete frames",
        "v0_real_imag_raw": v0,
        "v1_real_imag_raw": v1,
        "delta_real_imag_raw": [[task[0] - rest[0], task[1] - rest[1]] for rest, task in zip(v0, v1)],
        "inverse_status": "not reconstructed; exact geometry, protocol sign and calibration still required",
    }
    result["descriptive_metrics"] = {
        "task_minus_rest_rms_raw": rms_difference(v1, v0),
        "rest_frame_distance_from_baseline_rms_raw": {
            str(frame_id): rms_difference(frames[frame_id], v0) for frame_id in rest_ids
        },
        "interpretation": "Descriptive distances, not significance tests or muscle activation percentages. Baseline residuals use the same frames as the baseline and may underestimate variation; use a separate rest-rest control.",
    }
    if post_rest_ids:
        post = median_vector(frames, post_rest_ids)
        result["post_rest_real_imag_raw"] = post
        result["post_rest_minus_rest_real_imag_raw"] = [
            [value[0] - ref[0], value[1] - ref[1]] for value, ref in zip(post, v0)
        ]
        result["descriptive_metrics"]["post_rest_minus_rest_rms_raw"] = rms_difference(post, v0)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input-prefix", type=Path, required=True)
    parser.add_argument("--rest-frames", type=parse_frame_ids, required=True)
    parser.add_argument("--task-frames", type=parse_frame_ids, required=True)
    parser.add_argument("--post-rest-frames", type=parse_frame_ids,
                        help="Optional independent recovery/rest-control frames")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error(f"Refusing to overwrite: {args.output}")
    result = prepare(args.input_prefix, args.rest_frames, args.task_frames, args.post_rest_frames)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(f"Saved {len(result['v0_real_imag_raw'])} aligned patterns to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
