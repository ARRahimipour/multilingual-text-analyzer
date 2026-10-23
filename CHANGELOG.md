# Changelog

## 2.0.0 — Session 2 through slide 17

- Added opt-in task-specific text preprocessing and step-by-step audit statistics.
- Added HTML/entity/script/style handling, URL/email/mention/hashtag processing,
  Unicode NFKC/Persian characters/digits, invisible control cleanup, emojis,
  punctuation, elongated letters and optional Persian-PII masking.
- Retained sentence boundaries before destructive punctuation cleaning and kept
  original Session 1 counts unchanged in raw mode.
- Added dataset cleaning for CSV/TSV/JSONL, script/length filters, post-cleaning
  exact and heuristic near-deduplication, and atomic output writing.
- Extended CLI, desktop controls, cleaned preview, HTML/text/JSON audit export,
  per-slide documentation and unit/integration tests.
- 86 tests; 10 Qt integration tests require PySide6 and were skipped when
  unavailable in the current check environment.

## 1.3.2

- Fixed RTL paragraphs being visually left-aligned by using absolute edge alignment.
- Added geometry tests for short lines and wrapped paragraphs after resizing.
- Verified all 62 tests and refreshed the desktop preview.

## 1.3.1

- Added a project-local virtual environment setup helper.
- Added a launcher that always uses the project's `.venv` interpreter.
- Pinned the Qt runtime and binding package to the tested 6.8.3 release.
- Reworked the README around installation, normal use, counting examples, and troubleshooting.
- Added development notes for dependency changes, tests, and Git identity.
- Re-ran all 60 tests inside the isolated environment.

## Earlier changes

The Git history records the initial analyzer, CLI/report exports, desktop interface, author details, removal of the 300-word target, and subsequent text-display fixes. The important behavior fixes were quoted-punctuation sentence boundaries and the move from Tk to Qt for Persian/Arabic layout. See `git log` for the original commit dates and messages.
