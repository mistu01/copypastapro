### What's Changed in v1.3.40
- **Startup Hotfix**: Added missing `Any` typing import in `app/paste_helper.py` that prevented `v1.3.39` from launching.
- **Large Screenshot `Ctrl + V` Fix**: Unified screenshot copy via `PasteHelper.set_clipboard_image`, eliminated 4× redundant PNG encoding, and normalized to `Format_RGB32`.
