"""Main window: global header (title, session, device status, wall clock) and exactly three tabs."""

from __future__ import annotations

from PySide6.QtCore import QTime, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QTabWidget, QVBoxLayout, QWidget

from app.core.config import data_root

from . import APP_NAME, __version__
from .features.measurement.measurement_page import MeasurementPage
from .features.results.results_page import ResultsPage
from .features.sessions.sessions_page import SessionsPage
from .theme import tabular

TABS = ("Measurement", "Results", "Sessions")  # AGENTS.md §1: exactly three tabs


class AppHeader(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Header")
        row = QHBoxLayout(self)
        row.setContentsMargins(16, 10, 16, 10)
        title = QLabel(APP_NAME)
        title.setObjectName("AppTitle")
        self.session = QLabel("No active session")
        self.session.setObjectName("Muted")
        self.device = QLabel()
        self.device.setObjectName("Status")
        self.clock = tabular(QLabel())
        self.clock.setObjectName("Clock")
        row.addWidget(title)
        row.addSpacing(24)
        row.addWidget(self.session)
        row.addStretch(1)
        row.addWidget(self.device)
        row.addSpacing(24)
        row.addWidget(self.clock)
        self.set_device_state("disconnected")
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._tick()

    def set_device_state(self, state: str):
        """Shows only what the backend confirmed: disconnected | connecting | connected | error."""
        self.device.setText({"disconnected": "● Disconnected", "connecting": "● Connecting…",
                             "connected": "● Connected", "error": "● Error"}[state])
        self.device.setProperty("state", state)
        self.device.style().unpolish(self.device)
        self.device.style().polish(self.device)

    def _tick(self):
        self.clock.setText(QTime.currentTime().toString("HH:mm:ss"))  # wall clock only, not experiment time


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {__version__}")
        self.resize(1366, 820)
        central = QWidget()
        column = QVBoxLayout(central)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        self.header = AppHeader()
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.measurement = MeasurementPage()
        for name, page in zip(TABS, (self.measurement, ResultsPage(), SessionsPage())):
            self.tabs.addTab(page, name)
        column.addWidget(self.header)
        column.addWidget(self.tabs, 1)
        self.setCentralWidget(central)
        self.statusBar().showMessage(f"Data folder: {data_root()}  ·  Research use only, not a medical device")
