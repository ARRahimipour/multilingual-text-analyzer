# v5 — Responsive NLP Research Workbench

- Replaced the narrow stage navigation list with a responsive 2-column / 3-column grid of six explicitly selectable stage buttons.
- Made the main application and the six-stage dialog fit the primary display's available geometry and scroll vertically as needed; removed unnecessarily large fixed minimum sizes.
- Introduced nine labeled UTF-8 case studies (eight Persian, one English), accessible from the pipeline's Test case selector, with English-language instructions for professors.
- Rewrote the six-stage guide in English and refreshed the README. Persian sample strings are retained only as linguistic data.
- Added regression tests for case availability, preprocessing invariants, Unicode half-spaces and English stage metadata.

## Research Studio UI / Persian spacing update (2026-11-20)

- Added a standalone, focused English six-stage experiment window: clear step navigation, output/audit/JSON views, simple English guides, presets, inline tooltips, stage counts and export controls.
- Styled the main UI and research lab with a dark navy/teal theme, more readable metric cards and a primary six-stage action; moved advanced cleaning into an opt-in panel.
- Renamed all six pipeline stage titles in English, explicitly labeling the final stage **Stemming / Lemmatization**.
- Added a display-only Unicode inspector distinguishing U+0020 (space), U+200C (ZWNJ), U+200D (ZWJ), and NBSP; shows before/after spacing counts.
- Improved conservative Persian spacing for malformed ZWNJ sequences, separated suffixes/prefixes and **limited high-confidence** unspaced plural/verb forms; avoids blanket changes to words like «تنها».
- Added guided English handout, Persian spacing fixture and script, reproducible English and Persian sample JSON reports, and regression tests.
- Limitations: Hazm, NLTK resources, Qt and subword packages require local installation. Full GUI was not executable in the headless verification environment.

## Six-stage preprocessing upgrade (handout pages 27–99)

- Added `six_stages` operation with six independent stage snapshots: Raw Text, Cleaning, Normalization, Tokenization, Stopwords and one Stem/Lemma path.
- Added real Hazm/NLTK pipeline backends, regex alternative, sentence-boundary preservation, negation-safe stopword configuration and audit of morphology mappings.
- Added a dedicated six-stage course button, six per-stage GUI output tabs, CLI support, two configurations, demo script and Persian guide.
- Added eleven focused tests, including the handout's 9→4 English example; optional Persian/Hazm integration is skipped if Hazm is unavailable.
- Original operations, API and archive contents retained for compatibility.

# v3.1.1 reconstruction — 2026-11-16

Restores expanded handout activities after temporary release files expired: stopword policies and word-label learning, four-stage frequency comparison, actual library pipelines, sparse representations, textbook TF-IDF, retrieval and classifier comparisons. Adds configuration UI, Persian examples, tests and documentation. Existing repository history is preserved; new commits use real timestamps.

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
