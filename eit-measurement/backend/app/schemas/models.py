"""Data contracts of the studio: measurement configuration, wiring and study design.

These are the objects the user edits (as JSON files in data/hardware/ and data/protocols/, later through the
interface). They hold the settings and their validation; the quantities derived from them (measurement
sequence, frame duration) come from the scientific package ``app.eit``. Planning and running a session
from a study design is done by ``app.services.protocol_runner``.

Plain dataclasses for now; they become the Pydantic models of the API when the FastAPI backend is added.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from ..eit.protocol import frame_duration_s, make_sequence

# ---------------------------------------------------------------------------------------
# Measurement configuration (hardware settings) and wiring
# ---------------------------------------------------------------------------------------

# The board routes electrodes through two ADG2128 crosspoint switches: 24 X lines in total (P1 X0..X23).
# The driver's electrode_count_available() lists (8, 16, 32), but 32 cannot be wired on this board.
BOARD_X_LINES = 24
MODES = ("voltage", "impedance")


@dataclass
class MeasurementConfig:
    n_electrodes: int = 16
    force_distance: int = 1           # electrodes between F+ and F- (1 = adjacent)
    sense_distance: int = 1           # electrodes between S+ and S- (1 = adjacent)
    excitation_frequency_hz: int = 50000
    # Firmware command value (driver-native units). The pilot recorded it as "amplitude_mvpp", but the
    # physical meaning is not verified: never present it as mVpp at the electrodes.
    excitation_amplitude: float = 600.0
    measurement_mode: str = "voltage"  # voltage: raw DFT counts of S+ - S-; impedance: Z = V/I (current measured)
    magnitude_mode: bool = False
    # Time of one measurement including switching and transport; 0.099 s measured on the 2026-10-05 pilot
    # (serial proxy, 10 ms delay). Re-measure with the timing benchmark when the setup changes.
    seconds_per_measurement: float = 0.099
    wiring: str = ""                   # wiring file (data/hardware/*.json): logical ring -> board lines -> sites

    @property
    def sequence(self) -> np.ndarray:
        """(A, B, M, N) on the logical ring = (F+, F-, S+, S-)."""
        return make_sequence(self.n_electrodes, self.force_distance, self.sense_distance)

    @property
    def n_measurements(self) -> int:
        return len(self.sequence)

    @property
    def frame_s(self) -> float:
        return frame_duration_s(self.n_measurements, self.seconds_per_measurement)

    def wiring_file(self):
        """Path of the wiring file. Relative names are looked up in the data folder (data/hardware/), so the
        same configuration works in the repository and in an installed app."""
        if not self.wiring:
            return None
        from ..core.config import data_root

        path = Path(self.wiring)
        if path.is_absolute():
            return path
        if path.parts and path.parts[0] == "data":
            path = Path(*path.parts[1:])
        return data_root() / path if len(path.parts) > 1 else data_root() / "hardware" / path

    def summary(self) -> dict:
        """Derived values to show read-only next to the editable settings."""
        return {"n_measurements": self.n_measurements, "frame_s": round(self.frame_s, 2)}

    def validate(self, wiring: dict | None = None) -> list:
        problems = []
        if not 4 <= self.n_electrodes <= BOARD_X_LINES:
            problems.append(f"electrode count must be between 4 and {BOARD_X_LINES} (board X lines), "
                            f"got {self.n_electrodes}")
        for name in ("force_distance", "sense_distance"):
            d = getattr(self, name)
            if not 1 <= d < self.n_electrodes:
                problems.append(f"{name} must be between 1 and {self.n_electrodes - 1}, got {d}")
        if self.excitation_frequency_hz <= 0:
            problems.append("excitation frequency must be positive")
        if self.excitation_amplitude <= 0:
            problems.append("excitation amplitude must be positive")
        if self.magnitude_mode:
            problems.append("magnitude_mode must be False (otherwise the real/imaginary parts are lost)")
        if self.measurement_mode not in MODES:
            problems.append(f"measurement mode must be one of {MODES}")
        if self.seconds_per_measurement <= 0:
            problems.append("seconds_per_measurement must be positive")
        if wiring is not None:
            n_wired = len(wiring.get("logical_to_physical", []))
            if n_wired != self.n_electrodes:
                problems.append(f"wiring '{wiring.get('layout_id', '?')}' defines {n_wired} electrodes, "
                                f"configuration asks for {self.n_electrodes}")
        return problems

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def load_measurement(path) -> MeasurementConfig:
    return MeasurementConfig(**json.loads(Path(path).read_text()))


def load_wiring(path) -> dict:
    """Wiring file: layout_id, logical_to_physical (board X line per logical ring index) and channels
    (index = board X line, site name, skin landmark, wire colour ...)."""
    wiring = json.loads(Path(path).read_text())
    l2p = wiring["logical_to_physical"]
    if len(set(l2p)) != len(l2p):
        raise ValueError(f"{path}: logical_to_physical repeats a board line")
    known = {c["index"] for c in wiring["channels"]}
    missing = [p for p in l2p if p not in known]
    if missing:
        raise ValueError(f"{path}: board lines {missing} have no channel entry")
    return wiring


def wired_sites(wiring: dict) -> list:
    """Site name of every logical ring index (e.g. L1 ... L8, R8 ... R1)."""
    site = {c["index"]: c["site"] for c in wiring["channels"]}
    return [site[p] for p in wiring["logical_to_physical"]]


# ---------------------------------------------------------------------------------------
# Study design (what the participant does): tasks, instructions, stage timing
# ---------------------------------------------------------------------------------------

REST = "REST"
CONTROL = "REST_CONTROL"
INSTRUCTIONS = {
    REST: "Remain relaxed. Keep the same resting head, jaw and lip pose.",
    CONTROL: "Remain relaxed (control: no task). Keep the same resting pose.",
    "SMILE_LEFT": "Smile with the LEFT mouth corner; keep your head still.",
    "SMILE_RIGHT": "Smile with the RIGHT mouth corner; keep your head still.",
    "SMILE_BOTH": "Smile with BOTH mouth corners; keep your head still.",
    "PUFF_LEFT": "Gently inflate the LEFT cheek with air; do not blow out.",
    "PUFF_RIGHT": "Gently inflate the RIGHT cheek with air; do not blow out.",
    "PUFF_BOTH": "Gently inflate BOTH cheeks with air; do not blow out.",
    "TONGUE_CHEEK_LEFT": "Push the tongue into the LEFT cheek (bulge without air); keep your head still.",
    "TONGUE_CHEEK_RIGHT": "Push the tongue into the RIGHT cheek (bulge without air); keep your head still.",
}

# Limits of the pilot acquisition software as recorded in meta.json of the 2026-10-05 sessions.
PILOT_FRAMES_PER_PHASE = 1
PILOT_TASK_HOLD_CAP_S = 30.0


@dataclass
class TaskSpec:
    """One task (or REST / control) as the participant sees it."""
    name: str                       # label written with every frame, e.g. "SMILE_LEFT"
    instruction: str = ""           # HOLD instruction (large text); default from INSTRUCTIONS
    ready_instruction: str = ""     # GET READY text; default "Get ready: <instruction>"
    release_instruction: str = ""   # RELEASE text; default "Relax."
    frames: int | None = None       # frames measured during HOLD; None = design default
    hold_s: float | None = None     # HOLD length; None = shortest that fits the frames

    def text(self) -> dict:
        hold = self.instruction or INSTRUCTIONS.get(self.name, f"Perform {self.name}.")
        return {"hold": hold, "ready": self.ready_instruction or f"Get ready: {hold}",
                "release": self.release_instruction or "Relax."}


@dataclass
class StageTiming:
    """Durations in seconds. Stages with 0 s are skipped (except HOLD, which is always present)."""
    prepare_manual: bool = False    # wait for the operator's "I'm ready" before each block
    ready_s: float = 3.0            # GET READY countdown, not measured (pilot cue warning: 3 s)
    settle_s: float = 2.0           # HOLD start -> first frame start, not measured (pilot transition_s: 2 s)
    hold_margin_s: float = 0.5      # HOLD time left after the last frame ends
    release_s: float = 0.0          # RELEASE after HOLD, not measured
    start_countdown_s: float = 10.0  # once, before the first block (pilot countdown_s: 10 s)
    hold_cap_s: float = PILOT_TASK_HOLD_CAP_S  # longest HOLD allowed (comfort; pilot cap 30 s)


@dataclass
class StudyDesign:
    name: str
    tasks: list                     # TaskSpec (or dicts / names when loading)
    rest: TaskSpec = field(default_factory=lambda: TaskSpec(REST))
    control: TaskSpec | None = field(default_factory=lambda: TaskSpec(CONTROL))  # None: no control blocks
    rounds: int = 2
    seed: int = 1
    randomize: bool = True          # shuffle tasks (and controls) within each round from the seed
    controls_per_round: int = 1
    initial_rest_frames: int = 3    # noise floor: consecutive REST frames before the first task
    frames_per_task: int = 1
    rest_between_tasks: bool = True  # REST -> TASK -> REST (the REST after a task is the one before the next)
    timing: StageTiming = field(default_factory=StageTiming)

    def __post_init__(self):
        self.tasks = [_task(t) for t in self.tasks]
        self.rest = _task(self.rest)
        self.control = _task(self.control) if self.control is not None else None
        if isinstance(self.timing, dict):
            self.timing = StageTiming(**self.timing)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def _task(t) -> TaskSpec:
    if isinstance(t, TaskSpec):
        return t
    if isinstance(t, str):
        return TaskSpec(t)
    return TaskSpec(**t)


def load_design(path) -> StudyDesign:
    return StudyDesign(**json.loads(Path(path).read_text()))
