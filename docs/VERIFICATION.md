# Verification record

Validation date: 2026-10-08.

## Executed

- Python 3.12.14 on Linux: `python -m unittest discover -s tests -v` — 54 tests passed.
- `python main.py examples/english_300.txt` — exit code 0, 300 words, 26 sentences, 207 unique vocabulary items.
- The sample also contains exactly 300 whitespace-separated items.
- CLI subprocess tests cover literal strings, stdin, input files, output files, JSON parsing, arbitrary text lengths, missing files, invalid UTF-8, and overwrite protection.
- Word-count invariants and multilingual subcases pass under the stated counting policy.
- Python compilation succeeds for the package, including the GUI module.
- Exported HTML escapes input and contains a sentence audit and vocabulary. JSON contains the full analysis.

The captured automated test output is in `test-results.txt`.

## Version 1.1 checks

- Input lengths of 0, 1, 298, 300, 301, and 10,000 tokens return successful CLI results with exact counts.
- Removed target fields and PASS/CHECK messages are checked in exported results.
- An independently counted multilingual fixture verifies total, unique, singleton, and frequency calculations.
- A Persian fixture verifies that enabling numeric tokens adds exactly two tokens for the years ۱۴۰۵ and ۲۰۲۶.
- Author details and email/website hyperlinks are verified in report outputs.

## Not executed in this environment

The Tk desktop interface could not be launched because the execution environment lacks a working Tk library and graphical display. It is supplied as source; only syntax compilation was checked. Desktop layout, clipboard behavior, file dialogs, and operating-system-specific font shaping need a local smoke test. The generated HTML report was not visually browser-verified here. Python 3.10/3.11 and Windows/macOS were not separately run.

## Local GUI smoke test

1. Run `python main.py --gui` on a graphical desktop with Tk installed.
2. Select **Load sample** and confirm 26 / 300 / 207 / 166 with no target status.
3. Paste Persian text and toggle normalization; verify the intended vocabulary merge.
4. Clear the editor; confirm all metrics return to zero.
5. Export each report format and open it in a browser, text editor, or spreadsheet viewer.
6. Resize the window and confirm the editor and frequency table remain usable.

A passing test suite validates these explicit rules and cases, not every language or an unknown grading system.

## Version 1.1.1 sentence-boundary fix

The uploaded Persian report exposed two false boundaries inside quoted punctuation examples. Balanced quotations containing only symbols now protect those symbols from sentence splitting. Real quoted sentences keep their normal boundaries. The source text reconstructed from the uploaded report is included as `examples/persian_regression.txt`.

Verified against this full text:

| Numbers | Sentences | Words | Unique | Singletons |
| --- | ---: | ---: | ---: | ---: |
| Excluded | 19 | 298 | 181 | 130 |
| Included | 19 | 300 | 183 | 132 |

Additional regression tests cover several quote styles, actual quoted speech, and unmatched quotes. The desktop title displays v1.1.1 so users can identify the corrected release.

## Version 1.2.0 automatic alignment

Direction detection tests cover Persian, Arabic, English, numbers, mixed text, and ties. Mock-widget checks verify paragraph tags, clearing/reset behavior, and no text/cursor mutation. HTML checks verify explicit direction and logical alignment. These checks do not replace an actual desktop visual test; Tk remains unavailable in this environment.

## Version 1.2.1 readability update

Replaced the small table font with a 15-point installed-font preference, dynamic row height, cell padding, and alternating row backgrounds. Added bounded text-size controls and fixed-width numeric columns. The 54 existing analysis/report tests still pass and Python compilation succeeds. Desktop font availability and actual Windows/Tk rendering must be checked locally; no visual desktop verification was possible here.
