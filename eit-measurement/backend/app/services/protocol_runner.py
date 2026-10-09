"""Protocol runner: turns a study design into the planned session schedule (seeded, reproducible).

A study design (data/protocols/*.json, model in app.schemas.models) lists the tasks with their instructions and the stage timing.
``expand`` turns it into the ordered blocks of one session: REST (measured baseline) -> TASK -> REST ...,
randomised per round from the seed, each block with its guidance stages

    [PREPARE (optional manual gate)] -> GET READY -> HOLD (frames are measured here) -> RELEASE

The HOLD length depends on the hardware configuration: one frame is n_measurements measurements taken one
after another, so HOLD >= settle + frames x frame duration + margin. With 16 electrodes (208 measurements,
~20.6 s per frame) one frame already needs ~23 s of HOLD; with 8 electrodes (40 measurements) ~4 s.

The acquisition software runs the cues; this module plans and validates them.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from ..schemas.models import (CONTROL, INSTRUCTIONS, PILOT_FRAMES_PER_PHASE, PILOT_TASK_HOLD_CAP_S, REST,  # noqa: F401
                              StageTiming, StudyDesign, TaskSpec, load_design)


def hold_needed_s(frames: int, frame_s: float, timing: StageTiming) -> float:
    """Shortest HOLD that contains ``frames`` sequential frames."""
    return timing.settle_s + frames * frame_s + timing.hold_margin_s


def max_frames_per_hold(frame_s: float, timing: StageTiming) -> int:
    return max(0, math.floor((timing.hold_cap_s - timing.settle_s - timing.hold_margin_s) / frame_s + 1e-9))


def expand(design: StudyDesign, frame_s: float) -> pd.DataFrame:
    """Ordered blocks of one session with their stage durations and planned start/end times.

    ``frame_s`` comes from the measurement configuration (protocol.frame_duration_s). A REST run longer
    than the HOLD cap is split into consecutive one-HOLD REST blocks (the analysis merges consecutive REST
    frames); a task block that does not fit the cap is an error (see ``validate``).
    """
    tm = design.timing
    rng = np.random.default_rng(design.seed)
    per_hold = max(1, max_frames_per_hold(frame_s, tm))
    blocks = []

    def add(rnd, spec: TaskSpec, kind: str, frames: int):
        chunks = [frames] if kind != "rest" else [min(per_hold, frames - k) for k in range(0, frames, per_hold)]
        for n in chunks:
            hold = spec.hold_s if spec.hold_s is not None else hold_needed_s(n, frame_s, tm)
            # no GET READY between consecutive REST blocks: the participant simply stays at rest
            ready = 0.0 if kind == "rest" and blocks and blocks[-1]["kind"] == "rest" else tm.ready_s
            blocks.append({"round": rnd, "task": spec.name, "kind": kind, "frames": n, "text": spec.text(),
                           "ready_s": ready, "hold_s": float(hold), "release_s": tm.release_s,
                           "hold_needed_s": hold_needed_s(n, frame_s, tm)})

    add(0, design.rest, "rest", design.initial_rest_frames)
    for r in range(1, design.rounds + 1):
        items = [(t, "task") for t in design.tasks]
        if design.control is not None:
            items += [(design.control, "control")] * design.controls_per_round
        order = rng.permutation(len(items)) if design.randomize else range(len(items))
        for k in order:
            spec, kind = items[k]
            if design.rest_between_tasks and blocks[-1]["kind"] != "rest":
                add(r, design.rest, "rest", 1)
            add(r, spec, kind, spec.frames or design.frames_per_task)
    if blocks[-1]["kind"] != "rest":
        add(design.rounds, design.rest, "rest", 1)

    t = tm.start_countdown_s
    rows = []
    for i, b in enumerate(blocks, start=1):
        start = t
        t += b["ready_s"] + b["hold_s"] + b["release_s"]
        rows.append({"block": i, "round": b["round"], "task": b["task"], "kind": b["kind"], "frames": b["frames"],
                     "instruction": b["text"]["hold"], "ready_instruction": b["text"]["ready"],
                     "release_instruction": b["text"]["release"], "prepare_manual": tm.prepare_manual,
                     "ready_s": b["ready_s"], "hold_s": round(b["hold_s"], 2), "release_s": b["release_s"],
                     "hold_needed_s": round(b["hold_needed_s"], 2),
                     "est_start_s": round(start, 1), "est_end_s": round(t, 1), "seed": design.seed})
    df = pd.DataFrame(rows)
    df.attrs.update(seed=design.seed, frame_s=frame_s, name=design.name)
    return df


def validate(design: StudyDesign, frame_s: float) -> list:
    """Problems that make the design unusable with this hardware configuration (empty list = OK)."""
    tm = design.timing
    problems = []
    if not design.tasks:
        problems.append("the design has no tasks")
    names = [t.name for t in design.tasks]
    if len(set(names)) != len(names):
        problems.append(f"task names must be unique: {names}")
    if design.rest.name in names or (design.control and design.control.name in names):
        problems.append("REST / control names must differ from the task names")
    for name, v in (("rounds", design.rounds), ("frames_per_task", design.frames_per_task),
                    ("initial_rest_frames", design.initial_rest_frames)):
        if v < 1:
            problems.append(f"{name} must be >= 1, got {v}")
    for name in ("ready_s", "settle_s", "hold_margin_s", "release_s", "start_countdown_s"):
        if getattr(tm, name) < 0:
            problems.append(f"timing.{name} must be >= 0")
    if max_frames_per_hold(frame_s, tm) < 1:
        problems.append(f"one frame ({frame_s:.1f} s) does not fit in the HOLD cap of {tm.hold_cap_s:g} s "
                        f"(settle {tm.settle_s:g} s + margin {tm.hold_margin_s:g} s); use fewer electrodes "
                        f"or measurements, or raise the cap after review")
    if problems:
        return problems
    df = expand(design, frame_s)
    short = df[df.hold_s + 1e-9 < df.hold_needed_s]
    for r in short.drop_duplicates("task").itertuples():
        problems.append(f"{r.task}: HOLD {r.hold_s:g} s is shorter than the {r.hold_needed_s:g} s needed for "
                        f"{r.frames} frame(s) of {frame_s:.1f} s")
    long = df[(df.kind != "rest") & (df.hold_s > tm.hold_cap_s + 1e-9)]
    for r in long.drop_duplicates("task").itertuples():
        problems.append(f"{r.task}: HOLD {r.hold_s:g} s exceeds the cap of {tm.hold_cap_s:g} s "
                        f"({r.frames} frame(s) x {frame_s:.1f} s); reduce frames per task")
    return problems


def make_design(tasks, rounds=2, seed=1, controls_per_round=1, initial_rest_frames=3, frames_per_task=1,
                frame_s=20.6, settle_s=2.0) -> pd.DataFrame:
    """Shortcut used by the command line: a StudyDesign with default instructions, expanded.

    REST x initial_rest_frames (noise floor), then per round a random order of tasks and REST_CONTROL
    blocks, each preceded and followed by a REST block, ending with REST. REST_CONTROL is analysed like a
    task: its change from rest estimates the no-task null (noise + drift) under identical cue timing.
    """
    design = StudyDesign(name="command-line", tasks=list(tasks), rounds=rounds, seed=seed,
                         controls_per_round=controls_per_round, initial_rest_frames=initial_rest_frames,
                         frames_per_task=frames_per_task, control=TaskSpec(CONTROL) if controls_per_round else None,
                         timing=StageTiming(settle_s=settle_s))
    return expand(design, frame_s)


def design_markdown(df: pd.DataFrame, seed: int) -> str:
    total = df.est_end_s.max()
    frame_s = df.attrs.get("frame_s")
    lines = [f"# Session design (seed {seed})", "",
             f"Estimated duration {total / 60:.1f} min ({len(df)} blocks"
             + (f", {frame_s:.1f} s per frame" if frame_s else "") + "). Each block: GET READY -> HOLD (measured) -> "
             "RELEASE. Times are estimates; the acquisition software's own timing is authoritative.", "",
             "| # | round | task | frames | ready (s) | HOLD (s) | release (s) | instruction | est. start (s) |",
             "|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| {r.block} | {r.round} | {r.task} | {r.frames} | {r.ready_s:g} | {r.hold_s:g} | {r.release_s:g} | "
              f"{r.instruction} | {r.est_start_s} |" for r in df.itertuples()]
    if (df.frames > PILOT_FRAMES_PER_PHASE).any() or (df.hold_s > PILOT_TASK_HOLD_CAP_S).any():
        lines += ["", f"Pilot software limits (meta.json): frames_per_phase = {PILOT_FRAMES_PER_PHASE}, "
                  f"task_hold_cap_s = {PILOT_TASK_HOLD_CAP_S:g}. A multi-frame block needs multi-frame phases in "
                  "the acquisition software; entered as separate trials, each task frame would count as its own "
                  "repetition (consecutive REST frames are merged by the analysis)."]
    return "\n".join(lines) + "\n"


def schedule_summary(design: StudyDesign, measurement) -> dict:
    """What the interface shows about a study design under a measurement configuration (one call, no UI logic).

    ``measurement`` is a ``MeasurementConfig``. Returns the derived frame timing, the problems that make the
    design unusable (empty when valid) and, when valid, the size and length of the session schedule.
    """
    frame_s = measurement.frame_s
    problems = validate(design, frame_s)
    out = {"design": design.name, "n_tasks": len(design.tasks), "rounds": design.rounds, "seed": design.seed,
           "n_measurements": measurement.n_measurements, "frame_s": frame_s, "problems": problems}
    if not problems:
        df = expand(design, frame_s)
        out.update({"n_blocks": int(len(df)), "total_s": float(df.est_end_s.max()),
                    "task_hold_s": float(df[df.kind != "rest"].hold_s.max())})
    return out
