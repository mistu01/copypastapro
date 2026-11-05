"""
CopyPasta - Lightshot-Style Screenshot Capture & Annotation Overlay.
Provides instant screen snipping on PrintScreen key interception:
- Fullscreen virtual desktop capture across all monitors
- Click-and-drag rectangular area selection
- 8-point resize handles and selection movement
- Full annotation suite: Pen, Marker, Line, Arrow, Rectangle, Text
- Color palette selector & Undo (Ctrl+Z)
- Actions: Copy to clipboard (Enter / Ctrl+C / double-click), Save to file (Ctrl+S), Close (Esc)
"""

import os
import math
import time
from typing import List, Optional, Tuple, Dict, Any

from PySide6.QtCore import Qt, QRect, QPoint, QPointF, QSize, Signal, QTimer, QByteArray, QBuffer, QIODevice, QMimeData
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPolygonF, QPainterPath,
    QPixmap, QImage, QCursor, QGuiApplication, QClipboard
)
from PySide6.QtWidgets import (
    QWidget, QApplication, QFileDialog, QLineEdit, QFrame,
    QHBoxLayout, QVBoxLayout, QPushButton, QLabel
)


def get_default_screenshot_dir() -> str:
    """Return the user Desktop directory as the default screenshot save location."""
    user_profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    desktop_dir = os.path.join(user_profile, "Desktop")
    if os.path.exists(desktop_dir):
        return desktop_dir
    pictures_dir = os.path.join(user_profile, "Pictures")
    if os.path.exists(pictures_dir):
        return pictures_dir
    return user_profile


from app.icons import AppIcons


# Annotation models
class BaseAnnotation:
    def draw(self, painter: QPainter):
        raise NotImplementedError


class PenAnnotation(BaseAnnotation):
    def __init__(self, points: List[QPoint], color: QColor, width: int = 3):
        self.points = list(points)
        self.color = color
        self.width = width

    def draw(self, painter: QPainter):
        if len(self.points) < 2:
            if self.points:
                painter.setPen(QPen(self.color, self.width, Qt.SolidLine, Qt.RoundCap))
                painter.drawPoint(self.points[0])
            return
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(self.color, self.width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        for i in range(len(self.points) - 1):
            painter.drawLine(self.points[i], self.points[i + 1])


class MarkerAnnotation(BaseAnnotation):
    def __init__(self, points: List[QPoint], color: QColor, width: int = 14):
        self.points = list(points)
        self.color = QColor(color.red(), color.green(), color.blue(), 90)
        self.width = width

    def draw(self, painter: QPainter):
        if len(self.points) < 2:
            return
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(self.color, self.width, Qt.SolidLine, Qt.SquareCap, Qt.RoundJoin)
        painter.setPen(pen)
        for i in range(len(self.points) - 1):
            painter.drawLine(self.points[i], self.points[i + 1])


class LineAnnotation(BaseAnnotation):
    def __init__(self, start: QPoint, end: QPoint, color: QColor, width: int = 3):
        self.start = start
        self.end = end
        self.color = color
        self.width = width

    def draw(self, painter: QPainter):
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(self.color, self.width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.drawLine(self.start, self.end)


class ArrowAnnotation(BaseAnnotation):
    def __init__(self, start: QPoint, end: QPoint, color: QColor, width: int = 3):
        self.start = start
        self.end = end
        self.color = color
        self.width = width

    def draw(self, painter: QPainter):
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(self.color, self.width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.drawLine(self.start, self.end)

        # Arrowhead calculation
        dx = self.end.x() - self.start.x()
        dy = self.end.y() - self.start.y()
        length = math.hypot(dx, dy)
        if length < 5:
            return

        angle = math.atan2(dy, dx)
        head_len = max(14, self.width * 4)
        head_angle = math.pi / 6  # 30 degrees

        p1 = QPointF(
            self.end.x() - head_len * math.cos(angle - head_angle),
            self.end.y() - head_len * math.sin(angle - head_angle)
        )
        p2 = QPointF(
            self.end.x() - head_len * math.cos(angle + head_angle),
            self.end.y() - head_len * math.sin(angle + head_angle)
        )

        painter.setBrush(QBrush(self.color))
        painter.drawPolygon(QPolygonF([QPointF(self.end), p1, p2]))


class RectAnnotation(BaseAnnotation):
    def __init__(self, rect: QRect, color: QColor, width: int = 3, fill_mode: str = "none"):
        self.rect = rect
        self.color = color
        self.width = width
        self.fill_mode = fill_mode  # "none", "semi", "solid"

    def draw(self, painter: QPainter):
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(self.color, self.width, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        painter.setPen(pen)
        if self.fill_mode == "semi":
            # Translucent tint: ~28% alpha highlight fill
            tint = QColor(self.color.red(), self.color.green(), self.color.blue(), 72)
            painter.setBrush(QBrush(tint))
        elif self.fill_mode == "solid":
            # Solid opaque fill: 100% opacity for masking / redaction
            painter.setBrush(QBrush(self.color))
        else:
            painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.rect)


class TextAnnotation(BaseAnnotation):
    def __init__(self, pos: QPoint, text: str, color: QColor, font_size: int = 14):
        self.pos = pos
        self.text = text
        self.color = color
        self.font = QFont("Segoe UI", font_size, QFont.Bold)

    def draw(self, painter: QPainter):
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setFont(self.font)
        painter.setPen(self.color)
        painter.drawText(self.pos.x(), self.pos.y(), self.text)


class ScreenshotOverlay(QWidget):
    screenshot_captured = Signal(QPixmap)
    screenshot_saved = Signal(str)
    closed = Signal()

    HANDLE_SIZE = 8
    DPI_300 = 11811  # 300 DPI in dots per meter: round(300 / 0.0254)
    PALETTE_COLORS = [
        ("#ef4444", "Red"),
        ("#10b981", "Emerald"),
        ("#38bdf8", "Sky Blue"),
        ("#facc15", "Yellow"),
        ("#a855f7", "Purple"),
        ("#ffffff", "White"),
    ]

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.dpi_mode = self.db.get_setting("screenshot_dpi_mode", "300_ultra") if self.db else "300_ultra"
        self.rect_fill_mode: str = "none"  # "none", "semi", "solid"
        self._overlay_toast_text: str = ""
        self._overlay_toast_time: float = 0.0
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setMouseTracking(True)

        self.desktop_pixmap: Optional[QPixmap] = None
        self.virtual_rect = QRect()

        # Selection state
        self.selection_rect = QRect()
        self.is_selecting = False
        self.is_resizing = False
        self.is_moving = False
        self.is_drawing = False

        self.active_handle = None
        self.drag_start = QPoint()
        self.rect_start = QRect()

        # Annotation tools
        self.active_tool: Optional[str] = None  # None (move/select), 'pen', 'line', 'arrow', 'rect', 'marker', 'text'
        self.active_color = QColor("#ef4444")
        self.annotations: List[BaseAnnotation] = []
        self.current_points: List[QPoint] = []

        # Floating toolbars
        self._init_floating_bars()

        # In-place text input
        self.text_editor = QLineEdit(self)
        self.text_editor.setStyleSheet("""
            QLineEdit {
                background: rgba(15, 23, 42, 0.95);
                color: #ef4444;
                border: 1px solid #38bdf8;
                border-radius: 4px;
                padding: 4px 8px;
                font-family: 'Segoe UI', Arial;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.text_editor.hide()
        self.text_editor.returnPressed.connect(self._commit_text)
        self.text_editor.editingFinished.connect(self._commit_text)

    def _init_floating_bars(self):
        # Action Toolbar (Bottom / Horizontal)
        self.action_bar = QFrame(self)
        self.action_bar.setObjectName("ScreenshotActionBar")
        self.action_bar.setStyleSheet("""
            QFrame#ScreenshotActionBar {
                background-color: rgba(9, 14, 11, 0.96);
                border: 1px solid rgba(16, 185, 129, 0.45);
                border-radius: 6px;
                padding: 2px 4px;
            }
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                color: #f0fdf4;
                font-family: 'Segoe UI', Arial;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(5, 150, 105, 0.4);
                color: #00f59b;
            }
            QPushButton#CloseBtn:hover {
                background-color: rgba(244, 63, 94, 0.4);
                color: #f43f5e;
            }
            QPushButton#DpiBtn {
                background-color: rgba(56, 189, 248, 0.14);
                border: 1px solid rgba(56, 189, 248, 0.45);
                color: #38bdf8;
                font-size: 10px;
                padding: 3px 6px;
                border-radius: 4px;
            }
            QPushButton#DpiBtn:hover {
                background-color: rgba(56, 189, 248, 0.3);
                border-color: #38bdf8;
                color: #ffffff;
            }
        """)
        act_layout = QHBoxLayout(self.action_bar)
        act_layout.setContentsMargins(4, 2, 4, 2)
        act_layout.setSpacing(4)

        # Save button
        self.save_btn = QPushButton(" Save")
        self.save_btn.setIcon(AppIcons.save(14, "#38bdf8"))
        self.save_btn.setToolTip("Save screenshot to file (Ctrl + S)")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self.save_screenshot)
        act_layout.addWidget(self.save_btn)

        # Copy button (Primary Action, right beside Save!)
        self.copy_btn = QPushButton(" Copy")
        self.copy_btn.setIcon(AppIcons.copy_icon(14, "#00f59b"))
        self.copy_btn.setToolTip("Copy to clipboard & history (Ctrl + C / Enter / Double-click)")
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setStyleSheet("color: #00f59b; font-weight: bold; background-color: rgba(0, 245, 155, 0.15); border: 1px solid rgba(0, 245, 155, 0.4);")
        self.copy_btn.clicked.connect(self.copy_screenshot)
        act_layout.addWidget(self.copy_btn)

        # Cancel / Close button
        self.cancel_btn = QPushButton(" Close")
        self.cancel_btn.setObjectName("CloseBtn")
        self.cancel_btn.setIcon(AppIcons.close_cross(14, "#f43f5e"))
        self.cancel_btn.setToolTip("Cancel & close (Esc)")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.close_overlay)
        act_layout.addWidget(self.cancel_btn)

        # 300 DPI Resolution Indicator / Toggle
        self.dpi_btn = QPushButton(" 300 DPI")
        self.dpi_btn.setObjectName("DpiBtn")
        self.dpi_btn.setIcon(AppIcons.sparkles(13, "#38bdf8"))
        self.dpi_btn.setToolTip("Screenshot Quality: 300 DPI Ultra (Click to toggle 300 DPI Ultra / 300 DPI Native 1:1)")
        self.dpi_btn.setCursor(Qt.PointingHandCursor)
        self.dpi_btn.clicked.connect(self._toggle_dpi_mode)
        act_layout.addWidget(self.dpi_btn)

        self.action_bar.hide()

        # Annotation Toolbar (Right / Vertical)
        self.draw_bar = QFrame(self)
        self.draw_bar.setObjectName("ScreenshotDrawBar")
        self.draw_bar.setStyleSheet("""
            QFrame#ScreenshotDrawBar {
                background-color: rgba(9, 14, 11, 0.96);
                border: 1px solid rgba(16, 185, 129, 0.45);
                border-radius: 6px;
                padding: 4px 2px;
            }
            QPushButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px;
                min-width: 24px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: rgba(5, 150, 105, 0.35);
            }
            QPushButton[checked="true"] {
                background-color: rgba(0, 245, 155, 0.25);
                border: 1px solid #00f59b;
            }
            QPushButton#RectFillBtn {
                border: 1px dashed rgba(56, 189, 248, 0.45);
                background-color: rgba(15, 23, 42, 0.7);
                border-radius: 4px;
                min-width: 22px;
                min-height: 22px;
                padding: 2px;
                margin-top: -2px;
            }
            QPushButton#RectFillBtn:hover {
                background-color: rgba(56, 189, 248, 0.25);
                border-color: #38bdf8;
            }
            QPushButton#RectFillBtn[active="true"] {
                border: 1px solid #00f59b;
                background-color: rgba(0, 245, 155, 0.25);
            }
        """)
        draw_layout = QVBoxLayout(self.draw_bar)
        draw_layout.setContentsMargins(3, 4, 3, 4)
        draw_layout.setSpacing(4)

        # Tools: Pen, Line, Arrow, Rect, Marker, Text
        self.tool_buttons: Dict[str, QPushButton] = {}
        tool_defs = [
            ("pen", "Pen (Freehand)", AppIcons.pen(16, "#f0fdf4")),
            ("line", "Line", AppIcons.get("minus", 16, "#f0fdf4")),
            ("arrow", "Arrow", AppIcons.arrow(16, "#f0fdf4")),
            ("rect", "Square / Rectangle Indicator (Click or Right-Click for Fill)", AppIcons.square(16, "#f0fdf4")),
            ("marker", "Highlighter", AppIcons.highlighter(16, "#f0fdf4")),
            ("text", "Text", AppIcons.type(16, "#f0fdf4")),
        ]

        for tool_name, tooltip, icon in tool_defs:
            btn = QPushButton()
            btn.setIcon(icon)
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, t=tool_name: self._toggle_tool(t))
            draw_layout.addWidget(btn)
            self.tool_buttons[tool_name] = btn

            # Dedicated Fill option for the Square indicator
            if tool_name == "rect":
                self.rect_fill_btn = QPushButton()
                self.rect_fill_btn.setObjectName("RectFillBtn")
                self.rect_fill_btn.setCursor(Qt.PointingHandCursor)
                self.rect_fill_btn.clicked.connect(self._cycle_rect_fill_mode)
                draw_layout.addWidget(self.rect_fill_btn)
                self._update_fill_button_icon()

        # Color palette button
        self.color_btn = QPushButton()
        self.color_btn.setToolTip("Change annotation color")
        self.color_btn.setCursor(Qt.PointingHandCursor)
        self._update_color_button_icon()
        self.color_btn.clicked.connect(self._cycle_color)
        draw_layout.addWidget(self.color_btn)

        # Undo button
        self.undo_btn = QPushButton()
        self.undo_btn.setIcon(AppIcons.undo(16, "#94a3b8"))
        self.undo_btn.setToolTip("Undo last annotation (Ctrl + Z)")
        self.undo_btn.setCursor(Qt.PointingHandCursor)
        self.undo_btn.clicked.connect(self.undo_annotation)
        draw_layout.addWidget(self.undo_btn)

        self.draw_bar.hide()

    def _update_color_button_icon(self):
        pix = QPixmap(18, 18)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setBrush(QBrush(self.active_color))
        p.setPen(QPen(QColor("#ffffff"), 1.2))
        p.drawEllipse(2, 2, 14, 14)
        p.end()
        self.color_btn.setIcon(pix)
        self._update_fill_button_icon()

    def _update_fill_button_icon(self):
        pix = QPixmap(18, 18)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(self.active_color, 1.8)
        p.setPen(pen)
        if self.rect_fill_mode == "solid":
            p.setBrush(QBrush(self.active_color))
            tip = "Square Fill: Solid Opaque (Mask / Redact) — Click or press F to toggle"
        elif self.rect_fill_mode == "semi":
            tint = QColor(self.active_color.red(), self.active_color.green(), self.active_color.blue(), 90)
            p.setBrush(QBrush(tint))
            tip = "Square Fill: Translucent Tint (Highlight) — Click or press F to toggle"
        else:
            p.setBrush(Qt.NoBrush)
            tip = "Square Fill: Outline only (No fill) — Click or press F to toggle"
        p.drawRoundedRect(2, 2, 14, 14, 2, 2)
        p.end()
        if hasattr(self, "rect_fill_btn"):
            self.rect_fill_btn.setIcon(pix)
            self.rect_fill_btn.setToolTip(tip)

    def _cycle_rect_fill_mode(self):
        modes = ["none", "semi", "solid"]
        try:
            idx = modes.index(self.rect_fill_mode)
            self.rect_fill_mode = modes[(idx + 1) % len(modes)]
        except ValueError:
            self.rect_fill_mode = "semi"

        # Auto-activate rectangle tool if another tool was active
        if self.active_tool != "rect":
            self._toggle_tool("rect")

        self._update_fill_button_icon()

        labels = {
            "none": "Square Fill: Outline only",
            "semi": "Square Fill: Translucent (Highlight Tint)",
            "solid": "Square Fill: Solid Opaque (Mask / Redact)"
        }
        self._show_overlay_toast(labels.get(self.rect_fill_mode, "Square Fill Changed"))
        self.update()

    def _toggle_dpi_mode(self):
        if self.dpi_mode == "300_ultra":
            self.dpi_mode = "300_native"
            self.dpi_btn.setText(" 300 DPI (1:1)")
            self.dpi_btn.setToolTip("Screenshot Quality: 300 DPI Native (1:1 Screen Pixels + 300 DPI Metadata)\nClick to switch to 300 DPI Ultra")
            self._show_overlay_toast("Screenshot Quality: 300 DPI Native (1:1 Pixels)")
        else:
            self.dpi_mode = "300_ultra"
            self.dpi_btn.setText(" 300 DPI")
            self.dpi_btn.setToolTip("Screenshot Quality: 300 DPI Ultra (Super-Sampled Print Quality)\nClick to switch to 300 DPI Native")
            self._show_overlay_toast("Screenshot Quality: 300 DPI Ultra (Super-Sampled)")

        if self.db:
            self.db.set_setting("screenshot_dpi_mode", self.dpi_mode)
        self.update()

    def _show_overlay_toast(self, text: str):
        self._overlay_toast_text = text
        self._overlay_toast_time = time.time()
        self.update()
        QTimer.singleShot(2100, self.update)

    def _cycle_color(self):
        hex_list = [c[0] for c in self.PALETTE_COLORS]
        cur_hex = self.active_color.name().lower()
        try:
            idx = hex_list.index(cur_hex)
            next_idx = (idx + 1) % len(hex_list)
        except ValueError:
            next_idx = 0
        self.active_color = QColor(hex_list[next_idx])
        self._update_color_button_icon()

    def _toggle_tool(self, tool_name: str):
        if self.active_tool == tool_name:
            # Uncheck
            self.active_tool = None
            self.tool_buttons[tool_name].setChecked(False)
        else:
            self.active_tool = tool_name
            for name, btn in self.tool_buttons.items():
                btn.setChecked(name == tool_name)

        if hasattr(self, "rect_fill_btn"):
            is_rect = (self.active_tool == "rect")
            self.rect_fill_btn.setProperty("active", is_rect)
            self.rect_fill_btn.style().unpolish(self.rect_fill_btn)
            self.rect_fill_btn.style().polish(self.rect_fill_btn)

    def capture_screen(self):
        """Grabs full desktop across all displays and shows the interactive overlay."""
        screens = QGuiApplication.screens()
        if not screens:
            return

        # Refresh DPI mode setting
        if self.db:
            self.dpi_mode = self.db.get_setting("screenshot_dpi_mode", "300_ultra")
            if hasattr(self, "dpi_btn"):
                if self.dpi_mode == "300_native":
                    self.dpi_btn.setText(" 300 DPI (1:1)")
                else:
                    self.dpi_btn.setText(" 300 DPI")

        # Calculate bounding rectangle of all screens
        self.virtual_rect = QRect()
        for s in screens:
            self.virtual_rect = self.virtual_rect.united(s.geometry())

        # Grab and composite across all monitors
        self.desktop_pixmap = QPixmap(self.virtual_rect.size())
        self.desktop_pixmap.fill(Qt.black)

        painter = QPainter(self.desktop_pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        for s in screens:
            geo = s.geometry()
            screen_shot = s.grabWindow(0)
            painter.drawPixmap(geo.x() - self.virtual_rect.x(), geo.y() - self.virtual_rect.y(), screen_shot)
        painter.end()

        # Reset states
        self.selection_rect = QRect()
        self.annotations.clear()
        self.current_points.clear()
        self.active_tool = None
        for btn in self.tool_buttons.values():
            btn.setChecked(False)
        self.action_bar.hide()
        self.draw_bar.hide()
        self.text_editor.hide()

        self.setGeometry(self.virtual_rect)
        self.setCursor(Qt.CrossCursor)
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    # Paint event
    def paintEvent(self, event):
        if not self.desktop_pixmap:
            return

        painter = QPainter(self)
        # Draw full desktop screenshot
        painter.drawPixmap(0, 0, self.desktop_pixmap)

        # Semi-transparent dark mask
        mask_color = QColor(0, 0, 0, 130)

        if self.selection_rect.isValid() and not self.selection_rect.isEmpty():
            sel = self.selection_rect.normalized()

            # Create path for inverse clipping (dim everything outside selection)
            path = QPainterPath()
            path.addRect(0, 0, self.width(), self.height())
            path.addRect(sel.x(), sel.y(), sel.width(), sel.height())

            painter.setBrush(QBrush(mask_color))
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)

            # Draw crisp cyan/emerald selection border
            border_pen = QPen(QColor("#00f59b"), 1.5, Qt.SolidLine)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(sel)

            # Render all completed annotations inside or on top of selection
            for ann in self.annotations:
                ann.draw(painter)

            # Render ongoing active drawing
            if self.is_drawing and self.current_points:
                self._draw_current_annotation(painter)

            # Render 8 resize handles
            self._draw_resize_handles(painter, sel)

            # Render dimensions badge
            self._draw_dimension_badge(painter, sel)

            # Render status toast if active
            self._draw_status_toast(painter, sel)

        else:
            # Full screen dimmed mask when no selection exists yet
            painter.fillRect(0, 0, self.width(), self.height(), mask_color)

    def _draw_status_toast(self, painter: QPainter, sel: QRect):
        if not self._overlay_toast_text or (time.time() - self._overlay_toast_time > 2.0):
            return

        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(self._overlay_toast_text) + 24
        th = 24
        tx = sel.center().x() - tw // 2
        ty = sel.top() + 10
        if ty + th > sel.bottom() - 10:
            ty = sel.top() - th - 8
        if ty < 4:
            ty = 4

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(QBrush(QColor(9, 14, 11, 235)))
        painter.setPen(QPen(QColor("#00f59b"), 1.2))
        painter.drawRoundedRect(tx, ty, tw, th, 4, 4)

        painter.setPen(QColor("#ffffff"))
        painter.drawText(QRect(tx, ty, tw, th), Qt.AlignCenter, self._overlay_toast_text)

    def _draw_current_annotation(self, painter: QPainter):
        if not self.current_points:
            return
        p1 = self.current_points[0]
        p2 = self.current_points[-1]

        if self.active_tool == "pen":
            pen_ann = PenAnnotation(self.current_points, self.active_color)
            pen_ann.draw(painter)
        elif self.active_tool == "marker":
            marker_ann = MarkerAnnotation(self.current_points, self.active_color)
            marker_ann.draw(painter)
        elif self.active_tool == "line":
            line_ann = LineAnnotation(p1, p2, self.active_color)
            line_ann.draw(painter)
        elif self.active_tool == "arrow":
            arrow_ann = ArrowAnnotation(p1, p2, self.active_color)
            arrow_ann.draw(painter)
        elif self.active_tool == "rect":
            r = QRect(p1, p2).normalized()
            rect_ann = RectAnnotation(r, self.active_color, fill_mode=self.rect_fill_mode)
            rect_ann.draw(painter)

    def _draw_dimension_badge(self, painter: QPainter, sel: QRect):
        txt = f"{sel.width()} × {sel.height()} px"
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        badge_w = 90
        badge_h = 22
        badge_x = sel.x()
        badge_y = sel.y() - badge_h - 4
        if badge_y < 4:
            badge_y = sel.y() + 6

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(QBrush(QColor(10, 15, 12, 220)))
        painter.setPen(QPen(QColor("#10b981"), 1.0))
        painter.drawRoundedRect(badge_x, badge_y, badge_w, badge_h, 4, 4)

        painter.setPen(QColor("#00f59b"))
        painter.drawText(QRect(badge_x, badge_y, badge_w, badge_h), Qt.AlignCenter, txt)

    def _draw_resize_handles(self, painter: QPainter, sel: QRect):
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(QPen(QColor("#047857"), 1.5))
        s = self.HANDLE_SIZE

        handles = self._get_handle_rects(sel)
        for r in handles.values():
            painter.drawRect(r)

    def _get_handle_rects(self, sel: QRect) -> Dict[str, QRect]:
        s = self.HANDLE_SIZE
        half = s // 2
        l, r = sel.left(), sel.right()
        t, b = sel.top(), sel.bottom()
        mx, my = sel.center().x(), sel.center().y()

        return {
            "tl": QRect(l - half, t - half, s, s),
            "t":  QRect(mx - half, t - half, s, s),
            "tr": QRect(r - half, t - half, s, s),
            "r":  QRect(r - half, my - half, s, s),
            "br": QRect(r - half, b - half, s, s),
            "b":  QRect(mx - half, b - half, s, s),
            "bl": QRect(l - half, b - half, s, s),
            "l":  QRect(l - half, my - half, s, s),
        }

    def _get_handle_at(self, pos: QPoint) -> Optional[str]:
        if not self.selection_rect.isValid() or self.selection_rect.isEmpty():
            return None
        sel = self.selection_rect.normalized()
        for name, rect in self._get_handle_rects(sel).items():
            if rect.contains(pos):
                return name
        return None

    # Mouse Events
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        pos = event.pos()

        # If text editor is open, commit text
        if self.text_editor.isVisible():
            self._commit_text()
            return

        # Check if clicking on an annotation tool action
        if self.active_tool and self.selection_rect.contains(pos):
            if self.active_tool == "text":
                self._open_text_editor(pos)
                return
            self.is_drawing = True
            self.current_points = [pos]
            self.update()
            return

        # Check if clicking a resize handle
        handle = self._get_handle_at(pos)
        if handle:
            self.is_resizing = True
            self.active_handle = handle
            self.drag_start = pos
            self.rect_start = QRect(self.selection_rect)
            return

        # Check if clicking inside selection to move it
        if self.selection_rect.contains(pos):
            self.is_moving = True
            self.drag_start = pos
            self.rect_start = QRect(self.selection_rect)
            return

        # Otherwise, start a brand new rectangular selection
        self.is_selecting = True
        self.drag_start = pos
        self.selection_rect = QRect(pos, pos)
        self.action_bar.hide()
        self.draw_bar.hide()
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.pos()

        if self.is_drawing:
            self.current_points.append(pos)
            self.update()
            return

        if self.is_selecting:
            self.selection_rect = QRect(self.drag_start, pos).normalized()
            self.update()
            return

        if self.is_resizing and self.active_handle:
            self._perform_resize(pos)
            self.update()
            return

        if self.is_moving:
            dx = pos.x() - self.drag_start.x()
            dy = pos.y() - self.drag_start.y()
            new_rect = self.rect_start.translated(dx, dy)
            # Bound inside virtual screen
            if new_rect.left() < 0:
                new_rect.moveLeft(0)
            if new_rect.top() < 0:
                new_rect.moveTop(0)
            if new_rect.right() > self.width():
                new_rect.moveRight(self.width())
            if new_rect.bottom() > self.height():
                new_rect.moveBottom(self.height())
            self.selection_rect = new_rect
            self._reposition_toolbars()
            self.update()
            return

        # Update hover cursor
        if self.selection_rect.isValid() and not self.selection_rect.isEmpty():
            handle = self._get_handle_at(pos)
            if handle:
                cursor_map = {
                    "tl": Qt.SizeFDiagCursor, "br": Qt.SizeFDiagCursor,
                    "tr": Qt.SizeBDiagCursor, "bl": Qt.SizeBDiagCursor,
                    "t": Qt.SizeVerCursor, "b": Qt.SizeVerCursor,
                    "l": Qt.SizeHorCursor, "r": Qt.SizeHorCursor
                }
                self.setCursor(cursor_map.get(handle, Qt.ArrowCursor))
            elif self.active_tool:
                self.setCursor(Qt.CrossCursor)
            elif self.selection_rect.contains(pos):
                self.setCursor(Qt.SizeAllCursor)
            else:
                self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.CrossCursor)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        pos = event.pos()

        if self.is_drawing:
            self.is_drawing = False
            if self.current_points:
                p1 = self.current_points[0]
                p2 = self.current_points[-1]
                if self.active_tool == "pen":
                    self.annotations.append(PenAnnotation(self.current_points, self.active_color))
                elif self.active_tool == "marker":
                    self.annotations.append(MarkerAnnotation(self.current_points, self.active_color))
                elif self.active_tool == "line":
                    self.annotations.append(LineAnnotation(p1, p2, self.active_color))
                elif self.active_tool == "arrow":
                    self.annotations.append(ArrowAnnotation(p1, p2, self.active_color))
                elif self.active_tool == "rect":
                    self.annotations.append(
                        RectAnnotation(QRect(p1, p2).normalized(), self.active_color, fill_mode=self.rect_fill_mode)
                    )
                self.current_points = []
            self.update()
            return

        if self.is_selecting or self.is_resizing or self.is_moving:
            self.is_selecting = False
            self.is_resizing = False
            self.is_moving = False
            self.active_handle = None
            self.selection_rect = self.selection_rect.normalized()

            # Ensure minimal selection size (at least 10x10 px)
            if self.selection_rect.width() >= 10 and self.selection_rect.height() >= 10:
                self._reposition_toolbars()
                self.action_bar.show()
                self.draw_bar.show()
            else:
                self.selection_rect = QRect()
                self.action_bar.hide()
                self.draw_bar.hide()
            self.update()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.selection_rect.contains(event.pos()):
                # Signature Lightshot: double-click inside selection copies & closes!
                self.copy_screenshot()

    def _perform_resize(self, pos: QPoint):
        r = QRect(self.rect_start)
        h = self.active_handle

        if "l" in h:
            r.setLeft(min(pos.x(), r.right() - 10))
        if "r" in h:
            r.setRight(max(pos.x(), r.left() + 10))
        if "t" in h:
            r.setTop(min(pos.y(), r.bottom() - 10))
        if "b" in h:
            r.setBottom(max(pos.y(), r.top() + 10))

        self.selection_rect = r.normalized()
        self._reposition_toolbars()

    def _reposition_toolbars(self):
        if not self.selection_rect.isValid():
            return
        sel = self.selection_rect.normalized()

        # Action bar: horizontally below selection bottom-right
        act_w = self.action_bar.sizeHint().width()
        act_h = self.action_bar.sizeHint().height()

        act_x = sel.right() - act_w
        act_y = sel.bottom() + 8

        # Flip action bar inside or above if too close to bottom screen edge
        if act_y + act_h > self.height() - 4:
            act_y = sel.bottom() - act_h - 8
        if act_x < 4:
            act_x = 4

        self.action_bar.setGeometry(act_x, act_y, act_w, act_h)

        # Drawing bar: vertically to the right of selection top-right
        draw_w = self.draw_bar.sizeHint().width()
        draw_h = self.draw_bar.sizeHint().height()

        draw_x = sel.right() + 8
        draw_y = sel.top()

        # Flip drawing bar inside or to the left if near right screen edge
        if draw_x + draw_w > self.width() - 4:
            draw_x = sel.right() - draw_w - 8
        if draw_y + draw_h > self.height() - 4:
            draw_y = self.height() - draw_h - 4

        self.draw_bar.setGeometry(draw_x, draw_y, draw_w, draw_h)

    # In-place text editor
    def _open_text_editor(self, pos: QPoint):
        self.text_editor_pos = pos
        self.text_editor.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(15, 23, 42, 0.95);
                color: {self.active_color.name()};
                border: 1px solid #38bdf8;
                border-radius: 4px;
                padding: 4px 8px;
                font-family: 'Segoe UI', Arial;
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        self.text_editor.setText("")
        self.text_editor.setGeometry(pos.x(), pos.y(), 180, 32)
        self.text_editor.show()
        self.text_editor.setFocus()

    def _commit_text(self):
        if not self.text_editor.isVisible():
            return
        txt = self.text_editor.text().strip()
        if txt:
            # Baseline offset for font drawing
            self.annotations.append(
                TextAnnotation(QPoint(self.text_editor_pos.x() + 4, self.text_editor_pos.y() + 22), txt, self.active_color)
            )
        self.text_editor.hide()
        self.update()

    def undo_annotation(self):
        if self.annotations:
            self.annotations.pop()
            self.update()

    # Final high-resolution 300 DPI composite image & pixmap generator
    def render_result_image(self) -> Optional[QImage]:
        if not self.desktop_pixmap or not self.selection_rect.isValid() or self.selection_rect.isEmpty():
            return None

        sel = self.selection_rect.normalized()
        cropped = self.desktop_pixmap.copy(sel)
        base_img = cropped.toImage().convertToFormat(QImage.Format_ARGB32_Premultiplied)

        # High-Quality 300 DPI Rendering
        screen = QGuiApplication.primaryScreen()
        screen_dpi = screen.logicalDotsPerInch() if screen else 96.0
        if screen_dpi <= 0:
            screen_dpi = 96.0

        if self.dpi_mode == "300_native":
            scale = 1.0
        else:
            scale = max(1.0, 300.0 / screen_dpi)

        target_w = max(1, int(round(sel.width() * scale)))
        target_h = max(1, int(round(sel.height() * scale)))

        if abs(scale - 1.0) > 0.01:
            scaled_base = base_img.scaled(
                target_w, target_h,
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )
        else:
            scaled_base = base_img

        out_img = QImage(target_w, target_h, QImage.Format_ARGB32_Premultiplied)
        out_img.setDotsPerMeterX(self.DPI_300)
        out_img.setDotsPerMeterY(self.DPI_300)

        painter = QPainter(out_img)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        painter.drawImage(0, 0, scaled_base)

        if abs(scale - 1.0) > 0.01:
            painter.scale(scale, scale)

        painter.translate(-sel.x(), -sel.y())

        for ann in self.annotations:
            ann.draw(painter)

        painter.end()

        # Guarantee at least 300 DPI metadata is retained
        out_img.setDotsPerMeterX(self.DPI_300)
        out_img.setDotsPerMeterY(self.DPI_300)
        return out_img

    def render_result_pixmap(self) -> Optional[QPixmap]:
        img = self.render_result_image()
        if img is None:
            return None
        return QPixmap.fromImage(img)

    def copy_screenshot(self):
        qimg = self.render_result_image()
        if qimg and not qimg.isNull():
            qimg.setDotsPerMeterX(self.DPI_300)
            qimg.setDotsPerMeterY(self.DPI_300)

            clipboard = QApplication.clipboard()
            mime_data = QMimeData()
            mime_data.setImageData(qimg)

            # Raw image/png payload for modern apps at 300 DPI with maximum compression quality
            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QIODevice.WriteOnly)
            qimg.save(buf, "PNG", 100)
            buf.close()
            mime_data.setData("image/png", ba)

            clipboard.setMimeData(mime_data, QClipboard.Clipboard)

            pix = QPixmap.fromImage(qimg)
            self.screenshot_captured.emit(pix)
        self.close_overlay()

    def save_screenshot(self):
        qimg = self.render_result_image()
        if not qimg or qimg.isNull():
            return

        default_name = f"Screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png"
        default_path = os.path.join(get_default_screenshot_dir(), default_name)
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot (300 DPI Quality)",
            default_path,
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;All Files (*.*)"
        )
        if filepath:
            qimg.setDotsPerMeterX(self.DPI_300)
            qimg.setDotsPerMeterY(self.DPI_300)
            ext = os.path.splitext(filepath)[1].lower()
            if ext in ('.jpg', '.jpeg'):
                qimg.save(filepath, "JPEG", 100)
            else:
                qimg.save(filepath, "PNG", 100)
            self.screenshot_saved.emit(filepath)
            self.close_overlay()

    def close_overlay(self):
        self.hide()
        self.closed.emit()

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key_Escape:
            self.close_overlay()
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            self.copy_screenshot()
        elif key == Qt.Key_C and (modifiers & Qt.ControlModifier):
            self.copy_screenshot()
        elif key == Qt.Key_S and (modifiers & Qt.ControlModifier):
            self.save_screenshot()
        elif key == Qt.Key_Z and (modifiers & Qt.ControlModifier):
            self.undo_annotation()
        elif key == Qt.Key_F:
            self._cycle_rect_fill_mode()
        elif key == Qt.Key_D:
            self._toggle_dpi_mode()
        else:
            super().keyPressEvent(event)
