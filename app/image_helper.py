"""
CopyPasta - Image Helper Module.
Handles loading, caching, thumbnailing, and metadata extraction for all standard
Windows clipboard image formats (PNG, JPG, BMP, GIF, WEBP, TIFF, ICO, SVG, etc.).
"""

import os
import hashlib
import json
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImage, QPixmap

from app.database import get_media_dir

SUPPORTED_IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp",
    ".tiff", ".tif", ".ico", ".svg", ".jfif", ".avif"
}


def is_image_file(file_path: str) -> bool:
    """Check if the given local path points to a known supported image file."""
    if not file_path or not isinstance(file_path, str):
        return False
    _, ext = os.path.splitext(file_path)
    return ext.lower() in SUPPORTED_IMAGE_EXTENSIONS and os.path.isfile(file_path)


def format_file_size(size_bytes: int) -> str:
    """Format bytes into human-readable string (B, KB, MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def save_image_from_qimage(qimg: QImage, source_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Save a QImage from clipboard or screen capture to the local media directory.
    Generates a unique content hash and a fast-rendering thumbnail.
    """
    if qimg.isNull() or qimg.width() <= 0 or qimg.height() <= 0:
        return None

    media_dir = get_media_dir()
    os.makedirs(media_dir, exist_ok=True)

    # Encode to PNG bytes in memory for deterministic hashing
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    qimg.save(buf, "PNG")
    buf.close()

    raw_bytes = bytes(ba)
    if not raw_bytes:
        return None

    img_hash = hashlib.sha256(raw_bytes).hexdigest()[:16]
    image_filename = f"{img_hash}.png"
    thumb_filename = f"{img_hash}_thumb.png"

    image_path = os.path.join(media_dir, image_filename)
    thumb_path = os.path.join(media_dir, thumb_filename)

    # Write full image if not already cached
    if not os.path.isfile(image_path):
        try:
            with open(image_path, "wb") as f:
                f.write(raw_bytes)
        except Exception as e:
            print(f"[ImageHelper] Error saving image: {e}")
            return None

    # Generate crisp thumbnail (max 260w × 130h, keeping aspect ratio)
    if not os.path.isfile(thumb_path):
        try:
            thumb = qimg.scaled(260, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            thumb.save(thumb_path, "PNG")
        except Exception:
            thumb_path = image_path

    fmt = "PNG"
    if source_path:
        _, ext = os.path.splitext(source_path)
        if ext:
            fmt = ext.lstrip(".").upper()

    return {
        "hash": img_hash,
        "image_path": image_path,
        "thumb_path": thumb_path,
        "width": qimg.width(),
        "height": qimg.height(),
        "size_bytes": len(raw_bytes),
        "format": fmt,
        "source_path": source_path or ""
    }


def save_image_from_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load an image from a local file path, cache it in the media directory,
    and generate its thumbnail and metadata.
    """
    if not is_image_file(file_path):
        return None

    try:
        qimg = QImage(file_path)
        if qimg.isNull():
            pix = QPixmap(file_path)
            if not pix.isNull():
                qimg = pix.toImage()

        if qimg.isNull():
            return None

        meta = save_image_from_qimage(qimg, source_path=file_path)
        if meta and os.path.isfile(file_path):
            try:
                meta["size_bytes"] = os.path.getsize(file_path)
            except Exception:
                pass
        return meta
    except Exception as e:
        print(f"[ImageHelper] Error reading image file {file_path}: {e}")
        return None
