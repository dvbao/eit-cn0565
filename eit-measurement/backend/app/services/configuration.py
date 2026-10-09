"""Configuration service for the interface: which settings and study designs exist, and what they imply.

The interface calls these functions and shows the result; the rules live in schemas/models.py and
services/protocol_runner.py.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from ..core.config import data_path
from ..schemas.models import load_design, load_measurement, load_wiring
from .protocol_runner import schedule_summary


def list_measurement_files() -> list:
    return sorted(data_path("hardware").glob("measurement-*.json"))


def list_design_files() -> list:
    return sorted(p for p in data_path("protocols").glob("*.json"))


def describe_measurement(path: Path) -> dict:
    """Settings, derived values and problems (empty list = usable) of one measurement-settings file."""
    try:
        mc = load_measurement(path)
    except (OSError, ValueError, TypeError) as exc:
        return {"file": Path(path).name, "problems": [f"cannot read {Path(path).name}: {exc}"]}
    problems = []
    wiring = None
    if mc.wiring:
        try:
            wiring = load_wiring(mc.wiring_file())
        except (OSError, ValueError, KeyError) as exc:
            problems.append(f"wiring file {mc.wiring!r} cannot be read: {exc}")
    problems += mc.validate(wiring)
    out = {"file": Path(path).name, "settings": asdict(mc), "problems": problems, "config": mc,
           "wiring_layout": wiring.get("layout_id") if wiring else None}
    if not any("between" in p for p in problems):  # the sequence is computable
        out.update(mc.summary())
    return out


def describe_design(design_path: Path, measurement_path: Path) -> dict:
    """Study design checked against a measurement configuration (schedule size, length, problems)."""
    measurement = describe_measurement(measurement_path)
    if measurement["problems"]:
        return {"file": Path(design_path).name, "problems": ["fix the measurement settings first"]}
    try:
        design = load_design(design_path)
    except (OSError, ValueError, TypeError) as exc:
        return {"file": Path(design_path).name, "problems": [f"cannot read {Path(design_path).name}: {exc}"]}
    return {"file": Path(design_path).name, **schedule_summary(design, measurement["config"])}
