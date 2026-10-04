"""
Professional Lucide Vector Icon Suite for CopyPasta.
Provides crisp, modern, pixel-perfect SVG icons with High-DPI support and instant caching.
"""

from typing import Dict, Tuple
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt, QByteArray

LUCIDE_SVGS = {
    "clipboard": """<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>""",
    "copy": """<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>""",
    "zap": """<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>""",
    "shield_check": """<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>""",
    "key": """<path d="m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"/><path d="m21 2-9.6 9.6"/><circle cx="7.5" cy="15.5" r="5.5"/>""",
    "pin": """<path d="m15 4.5 4.5 4.5-2 2-1-1-4 4 1 1-1.5 1.5L8 12.5l-4 4-1.5-1.5 4-4-4-4 1.5-1.5 1 1 4-4-1-1 2-2Z"/><path d="m3 21 6-6"/>""",
    "pin_filled": """<path fill="currentColor" d="m15 4.5 4.5 4.5-2 2-1-1-4 4 1 1-1.5 1.5L8 12.5l-4 4-1.5-1.5 4-4-4-4 1.5-1.5 1 1 4-4-1-1 2-2Z"/><path d="m3 21 6-6"/>""",
    "settings": """<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>""",
    "grip_vertical": """<circle cx="9" cy="12" r="1.5" fill="currentColor"/><circle cx="9" cy="5" r="1.5" fill="currentColor"/><circle cx="9" cy="19" r="1.5" fill="currentColor"/><circle cx="15" cy="12" r="1.5" fill="currentColor"/><circle cx="15" cy="5" r="1.5" fill="currentColor"/><circle cx="15" cy="19" r="1.5" fill="currentColor"/>""",
    "expand": """<polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" x2="14" y1="3" y2="10"/><line x1="3" x2="10" y1="21" y2="14"/>""",
    "collapse": """<polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="14" x2="21" y1="10" y2="3"/><line x1="3" x2="10" y1="21" y2="14"/>""",
    "minus": """<line x1="5" x2="19" y1="12" y2="12"/>""",
    "x": """<path d="M18 6 6 18"/><path d="m6 6 12 12"/>""",
    "trash": """<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/>""",
    "plus": """<path d="M5 12h14"/><path d="M12 5v14"/>""",
    "link": """<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>""",
    "code": """<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>""",
    "mail": """<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>""",
    "file_text": """<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>""",
    "check": """<polyline points="20 6 9 17 4 12"/>""",
    "search": """<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>""",
    "star": """<polygon fill="currentColor" points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>""",
    "clock": """<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>""",
    "sparkles": """<path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/>""",
    "dot": """<circle cx="12" cy="12" r="4" fill="currentColor"/>""",
    "corner_down_left": """<polyline points="9 10 4 15 9 20"/><path d="M20 4v7a4 4 0 0 1-4 4H4"/>""",
}


class AppIconsMeta(type):
    def __getattr__(cls, name: str):
        if name in LUCIDE_SVGS:
            return lambda size=16, color="#ffffff", stroke_width=1.75, fill="none": cls.get(name, size, color, stroke_width, fill)
        raise AttributeError(f"type object '{cls.__name__}' has no attribute '{name}'")


class AppIcons(metaclass=AppIconsMeta):
    _pixmap_cache: Dict[Tuple[str, int, str, float, str], QPixmap] = {}
    _icon_cache: Dict[Tuple[str, int, str, float, str], QIcon] = {}

    @classmethod
    def pixmap(cls, name: str, size: int = 24, color: str = "#ffffff", stroke_width: float = 1.75, fill: str = "none") -> QPixmap:
        """Render a high-definition, anti-aliased SVG icon pixmap with High-DPI super-sampling and caching."""
        scale = 3  # 3x super-sampling for crystal-clear retina rendering
        cache_key = (name, size, color, stroke_width, fill)
        if cache_key in cls._pixmap_cache:
            return cls._pixmap_cache[cache_key]

        inner_svg = LUCIDE_SVGS.get(name, LUCIDE_SVGS["clipboard"])
        actual_fill = color if fill == "currentColor" else fill
        svg_xml = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24" fill="{actual_fill}" stroke="{color}" stroke-width="{stroke_width}" '
            f'stroke-linecap="round" stroke-linejoin="round">{inner_svg}</svg>'
        )

        renderer = QSvgRenderer(QByteArray(svg_xml.encode("utf-8")))
        pix = QPixmap(size * scale, size * scale)
        pix.fill(Qt.transparent)

        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        renderer.render(painter)
        painter.end()

        pix.setDevicePixelRatio(scale)
        cls._pixmap_cache[cache_key] = pix
        return pix

    @classmethod
    def get(cls, name: str, size: int = 24, color: str = "#ffffff", stroke_width: float = 1.75, fill: str = "none") -> QIcon:
        """Return a QIcon wrapping the rendered high-definition vector icon."""
        cache_key = (name, size, color, stroke_width, fill)
        if cache_key in cls._icon_cache:
            return cls._icon_cache[cache_key]

        pix = cls.pixmap(name, size, color, stroke_width, fill)
        icon = QIcon(pix)
        cls._icon_cache[cache_key] = icon
        return icon

    # Standard Semantic Helpers
    @classmethod
    def clipboard(cls, size: int = 20, color: str = "#38bdf8") -> QIcon:
        return cls.get("clipboard", size, color)

    @classmethod
    def copy_icon(cls, size: int = 16, color: str = "#ffffff") -> QIcon:
        return cls.get("copy", size, color)

    @classmethod
    def zap(cls, size: int = 16, color: str = "#ffffff") -> QIcon:
        return cls.get("zap", size, color)

    @classmethod
    def shield_check(cls, size: int = 16, color: str = "#38bdf8") -> QIcon:
        return cls.get("shield_check", size, color)

    @classmethod
    def key_icon(cls, size: int = 16, color: str = "#38bdf8") -> QIcon:
        return cls.get("shield_check", size, color)

    @classmethod
    def pin_icon(cls, size: int = 16, color: str = "#f59e0b", filled: bool = False) -> QIcon:
        if filled:
            return cls.get("pin_filled", size, color, stroke_width=1.6, fill=color)
        return cls.get("pin", size, color, stroke_width=1.6, fill="none")

    @classmethod
    def drag_grip(cls, size: int = 18, color: str = "#94a3b8") -> QIcon:
        return cls.get("grip_vertical", size, color)

    @classmethod
    def expand(cls, size: int = 16, color: str = "#38bdf8") -> QIcon:
        return cls.get("expand", size, color)

    @classmethod
    def collapse(cls, size: int = 16, color: str = "#94a3b8") -> QIcon:
        return cls.get("minus", size, color)

    @classmethod
    def close_cross(cls, size: int = 16, color: str = "#94a3b8") -> QIcon:
        return cls.get("x", size, color)

    @classmethod
    def trash(cls, size: int = 16, color: str = "#f43f5e") -> QIcon:
        return cls.get("trash", size, color, stroke_width=1.6)

    @classmethod
    def plus(cls, size: int = 16, color: str = "#38bdf8") -> QIcon:
        return cls.get("plus", size, color)

    @classmethod
    def link(cls, size: int = 14, color: str = "#38bdf8") -> QIcon:
        return cls.get("link", size, color)

    @classmethod
    def code(cls, size: int = 14, color: str = "#c084fc") -> QIcon:
        return cls.get("code", size, color)

    @classmethod
    def mail(cls, size: int = 14, color: str = "#f59e0b") -> QIcon:
        return cls.get("mail", size, color)

    @classmethod
    def file_text(cls, size: int = 14, color: str = "#94a3b8") -> QIcon:
        return cls.get("file_text", size, color)

    @classmethod
    def check(cls, size: int = 14, color: str = "#10b981") -> QIcon:
        return cls.get("check", size, color)

    @classmethod
    def search(cls, size: int = 16, color: str = "#94a3b8") -> QIcon:
        return cls.get("search", size, color)

    @classmethod
    def settings(cls, size: int = 16, color: str = "#94a3b8") -> QIcon:
        return cls.get("settings", size, color)

    @classmethod
    def star(cls, size: int = 14, color: str = "#f59e0b") -> QIcon:
        return cls.get("star", size, color)

    @classmethod
    def sparkles(cls, size: int = 16, color: str = "#00f59b") -> QIcon:
        return cls.get("sparkles", size, color)

    @classmethod
    def dot(cls, size: int = 16, color: str = "#00f59b") -> QIcon:
        return cls.get("dot", size, color)

