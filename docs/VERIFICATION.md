# Verification record — v1.3.2

> This historical log describes the Session 1 release. Version 2 session-two
> checks are recorded in `docs/SESSION2_TO_SLIDE17.md` and the newer tests.

Date: 2026-10-08. Python 3.12.14, Linux, PySide6 Essentials 6.8.3.

## Executed

- All **60 tests passed**, including six real Qt integration tests with `QT_QPA_PLATFORM=offscreen`.
- A Qt window was rendered at 1400 × 950 and visually inspected with the supplied Persian regression text. Paragraph starts and the right margin were visible and complete. See `qt-preview.png`.
- The actual editor preserves source text and selected text when applying paragraph direction.
- Persian and English paragraph directions are verified independently.
- Wrapped Persian lines are checked to remain within the editor viewport.
- The actual GUI produces 19 sentences, 300 words, 183 unique words, and 132 singleton words when both Persian normalization and numbers are enabled.
- Without numbers, the normalized Persian fixture produces 19 / 298 / 181 / 130.
- Clear, sample loading, table output, and text zoom limits pass.
- Existing CLI, counting, export, quoted-punctuation, Unicode, and arbitrary-length tests still pass.
- Python compilation and Git whitespace checks pass.

## Reproduce

```bash
python -m pip install -r requirements-gui.txt
python -m unittest discover -s tests -v
```

Without Qt installed, the six Qt integration tests are skipped. The CLI still runs independently.

## Remaining scope

The actual Windows/macOS desktop has not been run here. Font availability, native file dialogs, clipboard integration, and monitor scaling still depend on the local operating system. The rendered preview is from Linux offscreen Qt, not a Windows screenshot. The previous Tk GUI is replaced; v1.3.0 does not depend on Tk. Sentence segmentation remains a documented heuristic, not universal linguistic understanding.

## Qt reference

https://doc.qt.io/qtforpython-6.8/PySide6/QtGui/QTextBlockFormat.html

The editor uses block layout direction and alignment plus document and block margins. Formatting accompanies the preceding edit in undo history.

## Isolated-environment verification

For v1.3.1, a fresh `.venv` was created with `setup_env.py` and the pinned requirements were installed there. No system-site-packages option was used.

- `.venv/bin/python` reported `sys.prefix != sys.base_prefix` as `True`.
- PySide6 Essentials and shiboken6 both installed at 6.8.3.
- `python -m pip check` reported no broken requirements.
- All 60 tests passed using the environment's interpreter.
- Both setup and launcher files compiled successfully.
- Re-running setup with `--cli-only` reused the existing environment.
- `run_gui.py` launched the real Qt event loop from a different working directory in offscreen mode.
- `.venv` is ignored by Git and excluded from the archive.

Windows PowerShell/CMD commands have been reviewed but not executed on Windows. Existing commit timestamps are retained. New commits use the actual commit time and the requested author/committer identity.

## Version 1.3.2: physical right-edge alignment

The earlier tests checked RTL direction and clipping but missed physical alignment. A short Persian sentence reproduced the bug: its rendered text began at the left edge despite RTL block direction. Qt mirrors relative AlignRight in an RTL block. The fix combines AlignAbsolute with the desired edge.

Two new geometry tests measure the rendered text rectangle against the available line rectangle: short Persian/Arabic lines reach the right edge, English reaches the left edge, and the last line of a wrapped Persian paragraph stays right-aligned at two window widths. All 62 tests passed inside .venv, including eight Qt tests. A rendered mixed-language preview was inspected: Persian/Arabic appeared on the right and English on the left. Windows remains untested directly.

Reference: https://doc.qt.io/qt-6/qt.html#AlignmentFlag-enum
