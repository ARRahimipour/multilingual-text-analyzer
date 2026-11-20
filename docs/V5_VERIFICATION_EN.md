# LEXIS Research Studio v5 — Verification Note

## Changes reviewed

- The six-stage navigator uses six selectable native Qt push buttons in a responsive, multirow grid rather than a constrained side list.
- Both desktop windows derive their initial size from the active screen's available geometry and expose vertically scrollable page content to prevent inaccessible sections on laptop displays.
- Nine curated UTF-8 cases (eight Persian and one English) can be selected from the pipeline. Each case is paired with an English description and a suggested language/cleaning profile.
- The handout pipeline keeps all six inspectable stages, a before/after normalization audit, token summaries and full JSON output. Source text remains unchanged.
- Conservative punctuation spacing now preserves punctuation runs such as `!!!` instead of inserting a space between every repeated mark.

## Automated tests in the packaging environment

Command:

```bash
python -m unittest tests.test_cli tests.test_core tests.test_direction tests.test_gui tests.test_preprocessing tests.test_six_stage_pipeline tests.test_spacing_studio tests.test_persian_demo_suite tests.test_studio_responsive_gui -q
```

**Result: 111 tests discovered; 97 passed; 14 skipped; no failures in the selected suites.** The skips arise from optional GUI/model-backed dependencies not present in this environment. The nine demo inputs were also each processed end-to-end in a six-stage, regex-tokenized, conservative-spacing, morphology-disabled smoke configuration. See `outputs/academic_case_smoke_results.json`.

A full legacy run also has dependency-related errors involving the unavailable `hazm` and `tokenizers` packages; it is not being represented as a complete suite pass. PySide6 was not installable in this environment, so the updated graphical windows could not be rendered or clicked here. The project includes optional offscreen Qt geometry tests that will execute when PySide6 is installed on the target computer.

## How to validate the real Windows UI

```bash
python setup_env.py
python run_gui.py
python -m unittest tests.test_studio_responsive_gui -v
```

Open the six-stage screen, resize it to a small laptop-like size, and check that the six stage buttons remain visible in two columns. Scroll vertically to reach the output and status. At a wider size, confirm that the navigator changes to three columns. Review all nine cases in the **Test case** selector.

## Caveats

The application is intended as an inspectable research teaching aid. Rules for informal Persian writing, PDF repair, lemmatization and named-entity privacy are deliberately not presented as universally correct transformations. Prefer direct output inspection and follow-up linguistic evaluation.
