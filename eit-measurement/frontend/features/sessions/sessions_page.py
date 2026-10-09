"""Sessions tab (step 12): the list of recorded sessions will appear here."""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SessionsPage(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(48, 40, 48, 40)
        title = QLabel("Session history")
        title.setObjectName("EmptyTitle")
        text = QLabel("Recorded sessions (data/sessions/) will be listed here with date, study design, "
                      "duration and status (architecture step 12).")
        text.setObjectName("Muted")
        text.setWordWrap(True)
        lay.addWidget(title)
        lay.addWidget(text)
        lay.addStretch(1)
