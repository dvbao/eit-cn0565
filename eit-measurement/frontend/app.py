"""Start the desktop application: one QApplication, the theme, the main window."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from . import APP_NAME, __version__
from .main_window import MainWindow
from .theme import stylesheet


def create_app(argv=None) -> QApplication:
    app = QApplication.instance() or QApplication(list(argv if argv is not None else sys.argv))
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setStyleSheet(stylesheet())
    return app


def main(argv=None) -> int:
    app = create_app(argv)
    window = MainWindow()
    window.show()
    return app.exec()
