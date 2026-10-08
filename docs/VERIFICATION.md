# Verification record — v1.3.0

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
