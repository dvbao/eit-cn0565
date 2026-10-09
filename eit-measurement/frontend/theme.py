"""ONE source of design tokens (AGENTS.md §5), turned into a Qt stylesheet."""

TOKENS = {
    "background": "#FFFFFF",
    "surface": "#F9FAFB",
    "foreground": "#111827",
    "muted": "#6B7280",
    "border": "#E5E7EB",
    "primary": "#2563EB",
    "success": "#16A34A",
    "warning": "#D97706",
    "danger": "#DC2626",
}
FONT_FAMILY = '"Inter", "Geist", "Segoe UI", "Helvetica Neue", "Arial"'
CONFIG_COLUMN_PX = 280  # 260–300 px in AGENTS.md


def tabular(widget):
    """Tabular (equal-width) digits for timers, so a countdown does not jiggle (Qt has no CSS for this)."""
    from PySide6.QtGui import QFont

    font = widget.font()
    font.setFeature(QFont.Tag("tnum"), 1)
    widget.setFont(font)
    return widget


def stylesheet() -> str:
    t = TOKENS
    return f"""
    QWidget {{ background: {t['background']}; color: {t['foreground']}; font-family: {FONT_FAMILY}; font-size: 14px; }}
    QLabel#AppTitle {{ font-size: 18px; font-weight: 600; }}
    QLabel#Muted, QLabel#SectionNote {{ color: {t['muted']}; font-size: 12px; }}
    QLabel#SectionTitle {{ font-size: 13px; font-weight: 600; color: {t['muted']}; }}
    QLabel#Status[state="disconnected"] {{ color: {t['muted']}; }}
    QLabel#Status[state="connected"] {{ color: {t['success']}; }}
    QLabel#Status[state="error"] {{ color: {t['danger']}; }}
    QLabel#Clock {{ color: {t['muted']}; }}
    QLabel#Problem {{ color: {t['danger']}; font-size: 12px; }}
    QFrame#Header {{ border-bottom: 1px solid {t['border']}; }}
    QFrame#ConfigColumn {{ background: {t['surface']}; border-right: 1px solid {t['border']}; }}
    QFrame#ConfigColumn QLabel, QFrame#ConfigColumn QWidget {{ background: {t['surface']}; }}
    QLabel#StageLabel {{ font-size: 18px; font-weight: 600; color: {t['muted']}; }}
    QLabel#Instruction {{ font-size: 32px; font-weight: 600; }}
    QLabel#Countdown {{ font-size: 96px; font-weight: 500; }}
    QLabel#EmptyTitle {{ font-size: 20px; font-weight: 600; }}
    QTabWidget::pane {{ border: none; border-top: 1px solid {t['border']}; }}
    QTabBar::tab {{ padding: 8px 16px; color: {t['muted']}; border: none; }}
    QTabBar::tab:selected {{ color: {t['foreground']}; border-bottom: 2px solid {t['primary']}; }}
    QPushButton {{ border: 1px solid {t['border']}; border-radius: 6px; padding: 6px 12px; background: {t['background']}; }}
    QPushButton#Primary {{ background: {t['primary']}; color: white; border: none; }}
    QPushButton:disabled, QPushButton#Primary:disabled {{ color: {t['muted']}; background: {t['surface']};
        border: 1px solid {t['border']}; }}
    QStatusBar {{ color: {t['muted']}; font-size: 12px; border-top: 1px solid {t['border']}; }}
    """
