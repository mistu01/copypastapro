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

import math
import time
from typing import List, Optional, Tuple, Dict, Any

from PySide6.QtCore import Qt, QRect, QPoint, QPointF, QSize, Signal
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPolygonF, QPainterPath,
    QPixmap, QImage, QCursor, QGuiApplication
)
from PySide6.QtWidgets import (
    QWidget, QApplication, QFileDialog, QLineEdit, QFrame,
    QHBoxLayout, QVBoxLayout, QPushButton, QLabel
)

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
    def __init__(self, rect: QRect, color: QColor, width: int = 3):
        self.rect = rect
        self.color = color
        self.width = width

    def draw(self, painter: QPainter):
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(self.color, self.width, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        painter.setPen(pen)
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
    PALETTE_COLORS = [
        ("#ef4444", "Red"),
        ("#10b981", "Emerald"),
        ("#38bdf8", "Sky Blue"),
        ("#facc15", "Yellow"),
        ("#a855f7", "Purple"),
        ("#ffffff", "White"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
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

        # Copy button (Primary Action)
        self.copy_btn = QPushButton(" Copy")
        self.copy_btn.setIcon(AppIcons.check(14, "#00f59b"))
        self.copy_btn.setToolTip("Copy to clipboard & close (Ctrl + C / Enter / Double-click)")
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setStyleSheet("color: #00f59b; font-weight: bold;")
        self.copy_btn.clicked.connect(self.copy_screenshot)
        act_layout.addWidget(self.copy_btn)

        # Cancel / Close button
        self.cancel_btn = QPushButton()
        self.cancel_btn.setObjectName("CloseBtn")
        self.cancel_btn.setIcon(AppIcons.close_cross(14, "#f43f5e"))
        self.cancel_btn.setToolTip("Cancel & close (Esc)")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.close_overlay)
        act_layout.addWidget(self.cancel_btn)

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
            ("rect", "Rectangle", AppIcons.square(16, "#f0fdf4")),
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

    def capture_screen(self):
        """Grabs full desktop across all displays and shows the interactive overlay."""
        screens = QGuiApplication.screens()
        if not screens:
            return

        # Calculate bounding rectangle of all screens
        self.virtual_rect = QRect()
        for s in screens:
            self.virtual_rect = self.virtual_rect.united(s.geometry())

        # Grab and composite across all monitors
        self.desktop_pixmap = QPixmap(self.virtual_rect.size())
        self.desktop_pixmap.fill(Qt.black)

        painter = QPainter(self.desktop_pixmap)
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

        else:
            # Full screen dimmed mask when no selection exists yet
            painter.fillRect(0, 0, self.width(), self.height(), mask_color)

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
            rect_ann = RectAnnotation(r, self.active_color)
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
                    self.annotations.append(RectAnnotation(QRect(p1, p2).normalized(), self.active_color))
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

    # Final composite pixmap generator
    def render_result_pixmap(self) -> Optional[QPixmap]:
        if not self.desktop_pixmap or not self.selection_rect.isValid() or self.selection_rect.isEmpty():
            return None

        sel = self.selection_rect.normalized()
        # Crop desktop
        cropped = self.desktop_pixmap.copy(sel)

        # Draw annotations with relative coordinates onto the cropped pixmap
        painter = QPainter(cropped)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.translate(-sel.x(), -sel.y())

        for ann in self.annotations:
            ann.draw(painter)
        painter.end()

        return cropped

    def copy_screenshot(self):
        pixmap = self.render_result_pixmap()
        if pixmap:
            QApplication.clipboard().setPixmap(pixmap)
            self.screenshot_captured.emit(pixmap)
        self.close_overlay()

    def save_screenshot(self):
        pixmap = self.render_result_pixmap()
        if not pixmap:
            return

        default_name = f"Screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot",
            default_name,
            "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;All Files (*.*)"
        )
        if filepath:
            pixmap.save(filepath)
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
        else:
            super().keyPressEvent(event)
