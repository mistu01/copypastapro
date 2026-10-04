"""
Toast notification popup widget for sleek in-app feedback.
"""

from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint


class Toast(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)

        self.label = QLabel(self)
        self.label.setStyleSheet("""
            background-color: rgba(8, 16, 12, 0.96);
            color: #f0fdf4;
            border: 1px solid rgba(0, 245, 155, 0.45);
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 12px;
            font-weight: 600;
        """)
        layout.addWidget(self.label)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._fade_out)

    def show_message(self, text: str, duration_ms: int = 1400, pos: QPoint = None):
        self.label.setText(text)
        self.adjustSize()
        self.opacity_effect.setOpacity(1.0)

        if pos:
            self.move(pos)
        elif self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + parent_rect.height() - self.height() - 40
            self.move(x, y)

        self.show()
        self.raise_()
        self.timer.start(duration_ms)

    def _fade_out(self):
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        self.anim.finished.connect(self.hide)
        self.anim.start()
