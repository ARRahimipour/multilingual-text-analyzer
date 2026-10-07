# Verification record

Validation date: 2026-10-07.

## Executed

- Python 3.12.14 on Linux: `python -m unittest discover -s tests -v` — 39 tests passed.
- `python main.py examples/english_300.txt --strict` — exit code 0, 300 words, 26 sentences, 207 unique vocabulary items.
- The sample also contains exactly 300 whitespace-separated items.
- CLI subprocess tests cover literal strings, stdin, input files, output files, JSON parsing, strict failure, missing files, invalid UTF-8, and overwrite protection.
- Word-count invariants and multilingual subcases pass under the stated counting policy.
- Python compilation succeeds for the package, including the GUI module.
- Exported HTML escapes input and contains a sentence audit and vocabulary. JSON contains the full analysis.

The captured automated test output is in `test-results.txt`.

## Not executed in this environment

The Tk desktop interface could not be launched because the execution environment lacks a working Tk library and graphical display. It is supplied as source; only syntax compilation was checked. Desktop layout, clipboard behavior, file dialogs, and operating-system-specific font shaping need a local smoke test. The generated HTML report was not visually browser-verified here. Python 3.10/3.11 and Windows/macOS were not separately run.

## Local GUI smoke test

1. Run `python main.py --gui` on a graphical desktop with Tk installed.
2. Select **Load 300-word sample** and confirm 26 / 300 / 207 / 166 plus PASS.
3. Paste Persian text and toggle normalization; verify the intended vocabulary merge.
4. Clear the editor; confirm all metrics return to zero.
5. Export each report format and open it in a browser, text editor, or spreadsheet viewer.
6. Resize the window and confirm the editor and frequency table remain usable.

A passing test suite validates these explicit rules and cases, not every language or an unknown grading system.
