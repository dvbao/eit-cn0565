"""Results tab (step 12). Until then it states where results come from; it never shows invented data."""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ResultsPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(48, 40, 48, 40)
        title = QLabel("No session selected")
        title.setObjectName("EmptyTitle")
        text = QLabel("QC, signals and BP/JAC/GREIT images of a recorded session will appear here "
                      "(architecture step 12). Until then use the command line: python -m app check / study.")
        text.setObjectName("Muted")
        text.setWordWrap(True)
        lay.addWidget(title)
        lay.addWidget(text)
        lay.addStretch(1)
