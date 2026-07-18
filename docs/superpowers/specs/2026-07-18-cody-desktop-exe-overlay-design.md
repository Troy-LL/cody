# Cody desktop `.exe` overlay — Notion hotkey slice

**Date:** 2026-07-18  
**Status:** Approved (user proceed)  
**Demo target file:** `%USERPROFILE%\Downloads\Notion Installer.exe` (from user’s Downloads screenshot)

## Goal

Ship a Windows app you can double-click: transparent desktop overlay with Cody companion cursor; **Ctrl+Shift+C** reveals and points at Notion Installer in Downloads.

## Behavior

1. Launch → fullscreen click-through overlay; Cody follows mouse (lower-right slot).
2. **Ctrl+Shift+C** → resolve `Notion Installer*` under Downloads → `reveal(path)` → animate Cody to Explorer icon center (UI Automation). Caption: “I think this is Notion Installer.”
3. Soft-fail: if icon bounds unavailable, Explorer select still happens; caption notes soft-fail; Cody may point near Explorer window center.
4. **Esc** → follow mode again. Quit via tray or Ctrl+Shift+Q.

## Architecture

```
overlay/app.py          # entry + hotkeys
overlay/cursor_window.py
overlay/find_target.py  # Downloads / Notion Installer*
overlay/icon_bounds.py  # UIA (optional soft-fail)
reveal.reveal           # existing explorer /select
```

Stack: PySide6, existing `reveal/`, PyInstaller → `Cody.exe`. No Codex/voice in this slice.

## Out of scope

Voice, matcher, multi-file search UI, macOS.
