"""Measurement tab: configuration column (left, 280 px) + large guided-task panel (right).

Step 4 of docs/architecture.md: read-only. The column shows what the backend reports about the settings and
the study design in the data folder; connecting, editing and running sessions come in later steps.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout,
                               QWidget)

from app.services import configuration

from ...theme import CONFIG_COLUMN_PX, tabular


def _label(text: str, name: str = "", wrap: bool = True) -> QLabel:
    lab = QLabel(text)
    if name:
        lab.setObjectName(name)
    lab.setWordWrap(wrap)
    lab.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return lab


class Section(QWidget):
    """Titled block of label/value rows inside the configuration column."""

    def __init__(self, title: str):
        super().__init__()
        self.box = QVBoxLayout(self)
        self.box.setContentsMargins(0, 0, 0, 0)
        self.box.setSpacing(4)
        self.box.addWidget(_label(title.upper(), "SectionTitle"))

    def row(self, name: str, value: str) -> QLabel:
        lab = _label(f"{name}: <b>{value}</b>")
        lab.setTextFormat(Qt.RichText)
        self.box.addWidget(lab)
        return lab

    def note(self, text: str, name: str = "SectionNote") -> QLabel:
        lab = _label(text, name)
        self.box.addWidget(lab)
        return lab


class ConfigColumn(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("ConfigColumn")
        self.setFixedWidth(CONFIG_COLUMN_PX)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(20)
        self.device = self._device_section()
        self.measurement = Section("Measurement settings")
        self.design = Section("Study design")
        for w in (self.device, self.measurement, self.design):
            lay.addWidget(w)
        lay.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidget(inner)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self.refresh()

    def _device_section(self) -> Section:
        sec = Section("Device")
        sec.row("Status", "Disconnected")
        self.connect_button = QPushButton("Connect")
        self.connect_button.setEnabled(False)
        self.connect_button.setToolTip("Connecting comes with the demo device (architecture step 8) "
                                       "and the real board (step 11).")
        sec.box.addWidget(self.connect_button)
        return sec

    def refresh(self):
        """Ask the backend what the data folder contains and show it (no computation here)."""
        files = configuration.list_measurement_files()
        if not files:
            self.measurement.note("No measurement settings found in data/hardware/ (measurement-*.json).", "Problem")
            self.design.note("Needs measurement settings first.")
            return
        m = configuration.describe_measurement(files[0])
        self.measurement.note(m["file"])
        s = m.get("settings", {})
        if s:
            self.measurement.row("Electrodes", s["n_electrodes"])
            self.measurement.row("Drive / sense distance", f"{s['force_distance']} / {s['sense_distance']}")
            self.measurement.row("Frequency", f"{s['excitation_frequency_hz'] / 1000:g} kHz")
            self.measurement.row("Amplitude (firmware command)", f"{s['excitation_amplitude']:g}")
            self.measurement.row("Mode", s["measurement_mode"])
        if "n_measurements" in m:
            self.measurement.row("Measurements per frame", m["n_measurements"])
            self.measurement.row("One frame", f"{m['frame_s']:.1f} s")
        for p in m["problems"]:
            self.measurement.note(p, "Problem")
        designs = configuration.list_design_files()
        if not designs:
            self.design.note("No study design found in data/protocols/.", "Problem")
            return
        d = configuration.describe_design(designs[0], files[0])
        self.design.note(d["file"])
        if "n_tasks" in d:
            self.design.row("Tasks × rounds", f"{d['n_tasks']} × {d['rounds']}")
            self.design.row("Seed", d["seed"])
        if not d["problems"] and "n_blocks" in d:
            self.design.row("Blocks", d["n_blocks"])
            self.design.row("HOLD per task", f"{d['task_hold_s']:.1f} s")
            self.design.row("Session length", f"{d['total_s'] / 60:.1f} min")
        for p in d["problems"]:
            self.design.note(p, "Problem")
        self.design.note("Editing settings and designs comes in steps 5 and 7.")


class GuidancePanel(QFrame):
    """The large guided-task area. Without a session it shows an honest empty state, never a fake timer."""

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(48, 40, 48, 40)
        lay.setSpacing(16)
        self.stage = _label("NO ACTIVE SESSION", "StageLabel")
        self.instruction = _label("Connect the device and choose a study design to start a measurement.",
                                  "Instruction")
        self.instruction.setMinimumHeight(90)  # room for 2–3 lines: no layout jump when text changes
        self.countdown = tabular(_label("--:--", "Countdown", wrap=False))
        self.countdown.setAlignment(Qt.AlignCenter)
        self.countdown_caption = _label("Time remaining for this step", "Muted")
        self.countdown_caption.setAlignment(Qt.AlignCenter)
        self.next_step = _label("Next: —", "Muted")
        self.start_button = QPushButton("Start measurement")
        self.start_button.setObjectName("Primary")
        self.start_button.setEnabled(False)
        self.start_button.setToolTip("Needs a connected device and a valid study design (later steps).")
        self.start_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        for w in (self.stage, self.instruction):
            lay.addWidget(w)
        lay.addStretch(1)
        lay.addWidget(self.countdown)
        lay.addWidget(self.countdown_caption)
        lay.addStretch(1)
        lay.addWidget(self.next_step)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(self.start_button)
        lay.addLayout(bottom)


class MeasurementPage(QWidget):
    def __init__(self):
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        self.config = ConfigColumn()
        self.guidance = GuidancePanel()
        row.addWidget(self.config)
        row.addWidget(self.guidance, 1)
