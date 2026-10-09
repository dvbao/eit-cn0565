"""Log complete CN0565 voltage frames and frame-boundary cues.

Bench/fixture logger, not a human-use safety approval or a face reconstruction.
One row in *.voltages.csv is one sequential four-terminal configuration.
The API returns a complete frame at once, so only frame-level timestamps are
available here; it does not expose acquisition time for each configuration.

Dry run (no board, no excitation):
    python3 scripts/cn0565_capture.py --mock --frames 3 --output-prefix /tmp/cn0565-demo

Live bench example (values must come from an approved bench configuration):
    python3 scripts/cn0565_capture.py --uri 'serial:/dev/ttyACM0,230400,8n1n' \
        --frequency-hz FREQ --amplitude-mv AMPLITUDE --frames 20 \
        --output-prefix eit-measurement/data/bench/bench-01
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MAPPING = (
    Path(__file__).resolve().parents[1]
    / "docs/protocols/c16r-p1-wiring-proposal.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_mapping(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    channels = sorted(document["channels"], key=lambda item: item["index"])
    if len(channels) != 16 or [item["index"] for item in channels] != list(range(16)):
        raise ValueError("Mapping must contain exactly software indices 0..15")
    if len({item["site"] for item in channels}) != 16:
        raise ValueError("Mapping has duplicate site names")
    if len({item["p1_pin"] for item in channels}) != 16:
        raise ValueError("Mapping has duplicate P1 pins")
    for item in channels:
        index = item["index"]
        expected_pin = index + 3 if index < 12 else index + 5
        if item["x_line"] != f"X{index}" or item["p1_pin"] != expected_pin:
            raise ValueError(f"P1/X mismatch at software index {index}")
    return document, channels


def make_sequence(n_el: int = 16, force_distance: int = 1, sense_distance: int = 1):
    return [
        (f_plus, s_plus, (s_plus + sense_distance) % n_el, (f_plus + force_distance) % n_el)
        for f_plus in range(n_el)
        for s_plus in range(n_el)
        if s_plus not in (f_plus, (f_plus + force_distance) % n_el)
        and (s_plus + sense_distance) % n_el
        not in (f_plus, (f_plus + force_distance) % n_el)
    ]


class MockBoard:
    """Deterministic shape/serialization check; not simulated tissue physics."""

    def __init__(self):
        self.switch_sequence = make_sequence()
        self.frame_number = 0

    @property
    def all_voltages(self):
        self.frame_number += 1
        return [[float(i + self.frame_number), float(-i)] for i in range(len(self.switch_sequence))]


def load_blocks(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.frames is not None:
        if args.frames < 1:
            raise ValueError("--frames must be positive")
        return [{"label": "unlabeled", "frames": args.frames}]
    blocks = json.loads(args.schedule.read_text(encoding="utf-8"))["blocks"]
    if not blocks:
        raise ValueError("Schedule must contain at least one block")
    for block in blocks:
        if not isinstance(block.get("label"), str) or not block["label"].strip():
            raise ValueError("Each block needs a nonempty label")
        if type(block.get("frames")) is not int or block["frames"] < 1:
            raise ValueError("Each block needs a positive integer frame count")
    return blocks


def read_frame(board: Any, sequence: list[tuple[int, int, int, int]]):
    start_ns = time.monotonic_ns()
    start_utc = utc_now()
    frame = board.all_voltages
    end_ns = time.monotonic_ns()
    end_utc = utc_now()
    if len(frame) != len(sequence):
        raise ValueError(f"Incomplete frame: got {len(frame)}, expected {len(sequence)}")
    values = []
    for pattern_id, pair in enumerate(frame):
        if len(pair) != 2:
            raise ValueError(f"Pattern {pattern_id} did not return real and imaginary values")
        real, imag = float(pair[0]), float(pair[1])
        if not (math.isfinite(real) and math.isfinite(imag)):
            raise ValueError(f"Nonfinite voltage at pattern {pattern_id}")
        values.append((real, imag))
    return start_ns, end_ns, start_utc, end_utc, values


def percentile_nearest_rank(values: list[float], percentile: float) -> float:
    ranked = sorted(values)
    return ranked[max(0, math.ceil(percentile / 100 * len(ranked)) - 1)]


def capture(
    board: Any,
    mapping_document: dict[str, Any],
    channels: list[dict[str, Any]],
    blocks: list[dict[str, Any]],
    prefix: Path,
    configuration: dict[str, Any],
) -> dict[str, Any]:
    sequence = [tuple(int(value) for value in row) for row in board.switch_sequence]
    if not sequence or any(len(row) != 4 or any(not 0 <= index < 16 for index in row) for row in sequence):
        raise ValueError("Invalid switch sequence")
    if len(sequence) != len(set(sequence)):
        raise ValueError("Duplicate four-terminal configurations")
    if len(sequence) != 208:
        raise ValueError(f"This collector expects the 208-pattern adjacent protocol; got {len(sequence)}")

    paths = {kind: Path(f"{prefix}.{kind}.{ext}") for kind, ext in (
        ("voltages", "csv"), ("frames", "csv"), ("events", "csv"), ("meta", "json")
    )}
    existing = [str(path) for path in paths.values() if path.exists()]
    if existing:
        raise FileExistsError(f"Refusing to overwrite: {existing}")
    prefix.parent.mkdir(parents=True, exist_ok=True)

    summary = {
        "status": "incomplete",
        "started_utc": utc_now(),
        "completed_utc": None,
        "configuration": configuration,
        "mapping": mapping_document,
        "sequence_order": "(force_plus, sense_plus, sense_minus, force_minus)",
        "switch_sequence": [list(row) for row in sequence],
        "patterns_per_frame": len(sequence),
        "completed_frames": 0,
        "timing_note": "Only frame start/end times, not per-pattern timestamps; cues mark block boundaries, not actual movement onset.",
        "voltage_note": "Raw voltage-channel real/imaginary values; physical units, current and transfer impedance have not been independently calibrated.",
    }
    durations: list[float] = []
    frame_intervals: list[float] = []
    previous_start_ns = None
    try:
        with (
            paths["voltages"].open("x", newline="", encoding="utf-8") as voltage_file,
            paths["frames"].open("x", newline="", encoding="utf-8") as frame_file,
            paths["events"].open("x", newline="", encoding="utf-8") as event_file,
        ):
            voltage_writer = csv.writer(voltage_file)
            frame_writer = csv.writer(frame_file)
            event_writer = csv.writer(event_file)
            voltage_writer.writerow((
                "frame_id", "block_label", "pattern_id",
                "f_plus_index", "f_plus_site", "f_plus_p1_pin",
                "s_plus_index", "s_plus_site", "s_plus_p1_pin",
                "s_minus_index", "s_minus_site", "s_minus_p1_pin",
                "f_minus_index", "f_minus_site", "f_minus_p1_pin",
                "real_raw", "imag_raw"
            ))
            frame_writer.writerow((
                "frame_id", "block_label", "start_monotonic_ns", "end_monotonic_ns",
                "start_utc", "end_utc", "duration_s", "pattern_count"
            ))
            event_writer.writerow(("block_label", "cue_monotonic_ns", "cue_utc", "first_frame_id"))

            for block in blocks:
                cue_ns, cue_utc = time.monotonic_ns(), utc_now()
                first_frame_id = summary["completed_frames"]
                event_writer.writerow((block["label"], cue_ns, cue_utc, first_frame_id))
                event_file.flush()
                print(f"CUE {block['label']} | next complete frame: {first_frame_id}", flush=True)
                for _ in range(block["frames"]):
                    frame_id = summary["completed_frames"]
                    start_ns, end_ns, start_utc, end_utc, values = read_frame(board, sequence)
                    if previous_start_ns is not None:
                        frame_intervals.append((start_ns - previous_start_ns) / 1e9)
                    previous_start_ns = start_ns
                    duration_s = (end_ns - start_ns) / 1e9
                    frame_writer.writerow((
                        frame_id, block["label"], start_ns, end_ns, start_utc,
                        end_utc, f"{duration_s:.9f}", len(values)
                    ))
                    for pattern_id, ((fp, sp, sm, fm), (real, imag)) in enumerate(zip(sequence, values)):
                        voltage_writer.writerow((
                            frame_id, block["label"], pattern_id,
                            fp, channels[fp]["site"], channels[fp]["p1_pin"],
                            sp, channels[sp]["site"], channels[sp]["p1_pin"],
                            sm, channels[sm]["site"], channels[sm]["p1_pin"],
                            fm, channels[fm]["site"], channels[fm]["p1_pin"],
                            real, imag
                        ))
                    frame_file.flush()
                    voltage_file.flush()
                    durations.append(duration_s)
                    summary["completed_frames"] += 1
                    print(f"frame {frame_id}: {duration_s:.3f} s, {len(values)} patterns", flush=True)
        summary["status"] = "complete"
    finally:
        summary["completed_utc"] = utc_now()
        if durations:
            summary["frame_duration_median_s"] = statistics.median(durations)
            summary["frame_duration_p95_s"] = percentile_nearest_rank(durations, 95)
            summary["frame_duration_max_s"] = max(durations)
        if frame_intervals:
            summary["frame_start_interval_median_s"] = statistics.median(frame_intervals)
            summary["frame_start_interval_p95_s"] = percentile_nearest_rank(frame_intervals, 95)
            summary["frame_start_interval_max_s"] = max(frame_intervals)
        with paths["meta"].open("x", encoding="utf-8") as meta_file:
            json.dump(summary, meta_file, indent=2, ensure_ascii=False)
            meta_file.write("\n")
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--mock", action="store_true", help="No hardware or excitation; test file format only")
    source.add_argument("--uri", help="pyadi-iio URI of CN0565; bench use until full human-use review")
    duration = parser.add_mutually_exclusive_group(required=True)
    duration.add_argument("--frames", type=int, help="Number of complete frames to log")
    duration.add_argument("--schedule", type=Path, help="JSON with blocks [{label, frames}, ...]; terminal cues occur between frames")
    parser.add_argument("--output-prefix", type=Path, required=True, help="Creates .voltages.csv, .frames.csv, .events.csv and .meta.json; never overwrites")
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--frequency-hz", type=int, help="Required for live board; no suggested human value")
    parser.add_argument("--amplitude-mv", type=float, help="Required for live board; no suggested human value")
    args = parser.parse_args(argv)
    if args.uri and (
        args.frequency_hz is None or args.frequency_hz <= 0
        or args.amplitude_mv is None or args.amplitude_mv <= 0
    ):
        parser.error("Live board requires explicit positive --frequency-hz and --amplitude-mv from the approved bench configuration")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    mapping_document, channels = load_mapping(args.mapping)
    blocks = load_blocks(args)
    if args.mock:
        board = MockBoard()
    else:
        import adi  # Lazy import keeps --mock usable without pyadi-iio.

        board = adi.cn0565(uri=args.uri)
        board.electrode_count = 16
        board.force_distance = 1
        board.sense_distance = 1
        board.excitation_frequency = args.frequency_hz
        board.excitation_amplitude = args.amplitude_mv
        board.magnitude_mode = False
    summary = capture(
        board, mapping_document, channels, blocks, args.output_prefix,
        {"source": "mock" if args.mock else "cn0565", "uri": args.uri,
         "frequency_hz": args.frequency_hz, "amplitude_mv": args.amplitude_mv,
         "force_distance": 1, "sense_distance": 1, "python": sys.version},
    )
    print(f"Saved {summary['completed_frames']} frames; T95={summary['frame_duration_p95_s']:.3f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
