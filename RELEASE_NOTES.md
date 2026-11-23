### What's Changed in v1.3.39
- **Large Screenshot `Ctrl + V` Fix**: Eliminated duplicate clipboard writes and 4× redundant PNG encoding on screenshot capture so large screenshots paste cleanly with `Ctrl + V` just like the floating pill bar.
- **Faster & Cleaner Image Clipboard**: Normalized screenshots to `Format_RGB32`, reused cached PNG bytes directly, and added clipboard lock retry before `setMimeData`.
