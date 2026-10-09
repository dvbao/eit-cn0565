"""Study configuration: JSON file merged over documented defaults."""

from __future__ import annotations

import copy
import json
from pathlib import Path

# Project root = the eit-measurement/ folder (backend/app/eit/config.py -> parents[3]).
# Relative data paths (data/sessions, data/results, ...) are relative to it.
REPO = Path(__file__).resolve().parents[3]

DEFAULTS = {
    "study_id": None,
    "title": "",
    "raw_root": "data/sessions",
    "out_root": "data/results",
    # [{"dir": "<session folder>", "label": "<short name used in tables and figures>"}]
    "sessions": [],
    # Frames whose task equals this label (or whose state is a rest state) are references.
    "rest_label": "REST",
    # Optional explicit task list: sets the order in tables/figures AND filters them (recorded tasks not
    # listed are left out, with a warning). None = every recorded task, in order of first appearance.
    "tasks": None,
    # initial_rest | preceding_rest | bracketing_rest (see features.reference_for_block)
    "baseline": "initial_rest",
    # preceding/bracketing only: use the k rest frames closest to the task (None = whole rest block)
    "rest_reference_frames": None,
    # Task frames to skip at the start of each task block (transition frames).
    "drop_first_task_frames": 0,
    # |V_rest| below this many counts = noise-dominated channel, excluded from features/images.
    "strong_counts": 50.0,
    # Noise SD (counts) of one frame-to-frame difference, along the rest phasor (the part that enters Re(dz)).
    # Used for image/noise and the known-target check; always taken from here (no automatic fallback).
    # Measured value: qc_summary rest_rest_inphase_rms_counts (= rest_rest_rms_counts / sqrt(2) for circular noise).
    "noise_counts": 2.0,
    # Upper end of the measured complex REST->REST RMS; task_features counts |dv| > 3 x this value.
    "noise_counts_max": 2.9,
    "rel_thresholds_pct": [1.0, 2.0],
    "recognition": {"permutations": 2000, "seed": 0},
    "reconstruction": {
        "enabled": True,
        "h0": 0.08,
        "p": 0.5,
        "lambda": 0.01,
        "jac_method": "kotre",
        "bp_weight": "none",
        "greit_n": 32,
        "greit_s": 20.0,
        "greit_ratio": 0.1,
        "noise_draws": 200,
        "noise_seed": 11,
        # Ring drawing: electrode 0 just left of the top, counter-clockwise (left side drawn left).
        "ring_start_deg": None,
        # Sanity check: a known conductivity blob (contrast = sigma_blob / sigma_background) forward-simulated
        # in the disk and reconstructed; center/radius in disk units (radius 1).
        "known_target": {"center": [-0.45, -0.45], "radius": 0.25, "contrast": 1.5, "seed": 5},
    },
    "outputs": {"report_figures": True, "slide_figures": True, "clean_images": True},
}


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path) -> dict:
    path = resolve(path)
    cfg = _merge(DEFAULTS, json.loads(path.read_text()))
    if not cfg["study_id"]:
        raise ValueError(f"{path}: 'study_id' is required")
    if not cfg["sessions"]:
        raise ValueError(f"{path}: 'sessions' must list at least one session")
    cfg["config_path"] = str(path.resolve())
    return cfg


def resolve_out(path_like) -> Path:
    """Output path: a relative path is taken from the project root (a leading "eit-measurement/" is accepted),
    so `--out data/...` lands in eit-measurement/data/... whichever folder the command is run from."""
    path = Path(path_like)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == REPO.name:
        path = Path(*path.parts[1:])
    return REPO / path


def resolve(path_like) -> Path:
    """Absolute path; a relative path is taken from the current folder if it exists there, otherwise from the
    project root, so commands work both from eit-measurement/ and from the repository root."""
    path = Path(path_like)
    if path.is_absolute():
        return path
    return path.resolve() if path.exists() else REPO / path
