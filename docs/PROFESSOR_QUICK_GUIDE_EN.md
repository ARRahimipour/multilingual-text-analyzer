# LEXIS Research Studio — Six-Stage NLP Pipeline

**Purpose:** Reproduce the preprocessing workflow from the course handout (Session 2, PDF page 27). The pipeline saves all intermediate results, so every transformation is inspectable. It works with Persian and English and does not call a cloud service.

## Run the desktop

From the extracted project folder (Python 3.10+):

```shell
python setup_env.py
python run_gui.py
```

Click **06 / Six-stage pipeline**, choose one of nine named test cases, then click **Load case** and **Run all 6 stages**. The six stage buttons appear in a responsive multirow grid. To use your own material, paste Unicode text into the editor. Use **Export JSON** for a reproducible lab report.

## Six steps in plain English

| Step | Description | Evidence in the interface |
|---|---|---|
| 01 — Raw input | The untouched original text | Characters, UTF-8 bytes, raw source |
| 02 — Cleaning | Remove irrelevant markup, URLs, and optional noise | Change flags and character counts |
| 03 — Normalization | Standardize Persian yeh/kaf, numbers, diacritics, spaces and ZWNJ | Per-operation changes, before/after spacing counts, idempotence |
| 04 — Tokenization | Split into sentences and word tokens | Sentence boundaries, token counts, unique types |
| 05 — Stopwords | Optionally filter frequent functional words | Removed tokens, protected negation, top frequencies |
| 06 — Stemming / Lemmatization | Map lexical variants to stems **or** dictionary-like base forms | Method, backend and token-to-result mappings |

**The sixth stage is in English in both the current desktop and the legacy Course Lab.** The user selects *Stem*, *Lemma* or *None* before the experiment. The entire window fits the available screen area and its main content scrolls vertically when necessary.

## What the controls mean

- **Language** switches Persian/Hazm vs English/NLTK behavior.
- **Cleaning profile:** *General* is a reasonable demo; *Sentiment* preserves emojis; *NER* preserves entities; *Topic* removes more text noise.
- **Tokenizer:** *Automatic* uses Hazm for Persian and NLTK for English. *Regex* is a simpler model-free inspection option.
- **Persian spacing:** *Hazm* applies a language-aware normalizer; *Conservative* repairs common, high-confidence patterns; *Off* does not repair spacing.
- **Stage 6 / morphology:** *Stem* is a heuristic reduction; *Lemma* attempts a canonical base and can depend on POS.
- **Digit format:** ASCII, Persian or unchanged.
- **Filter stopwords** is optional. **Keep negation** prevents known negative words from being thrown away. **Stopword source** selects the Hazm/NLTK dictionary or an explicit custom list; **Protected terms** stay intact.
- **Show spaces & ZWNJ:** a *display-only* Unicode inspector; it never modifies the source, tokens or exported report.

## Why Persian half-spaces matter

| Input | Typical normalized example | Comment |
|---|---|---|
| `مي روم` | `می‌روم` | Arabic yeh standardized; normal space → ZWNJ |
| `كتاب ها` | `کتاب‌ها` | Arabic kaf standardized; suffix attached using ZWNJ |
| `كتابها` | `کتاب‌ها` | Conservative mode supports common known base words; Hazm handles more forms |
| `ميروم` | `می‌روم` | Safe common verb pattern |
| `تنها` | `تنها` | Must **not** be split into `تن‌ها` |

A regular space is **U+0020**; Persian half-space is **U+200C (ZERO WIDTH NON-JOINER)**. When inspection is on, normal spaces appear as `·` and half-spaces appear as `⟦ZWNJ⟧`. `⟦ZWJ⟧` is a *different* character and is preserved for joined emoji sequences.

## Reproducibility and research limitations

1. The raw source is preserved; each downstream stage uses the previous output. The full JSON includes the exact configuration, token lists, counts and mappings.
2. Cleaning options are task-dependent. Removing emojis, punctuation, or negation can erase critical signals. This is a teaching and audit tool, not a general-purpose Persian spellchecker.
3. **Conservative** spacing avoids broad edits that would damage valid words; it cannot fix every unspaced Persian word. **Hazm** is recommended for richer normalization.
4. Lemmatization may depend on language resources and on the selected POS tag; stemming can yield strings that are not full dictionary words.
5. The environment needs the packages in `requirements.txt` for the full GUI and model-backed stages. A minimal Python environment can still execute the standalone spacing verification script.

## Verification

```shell
python scripts/verify_spacing.py
python -m unittest tests.test_spacing_studio tests.test_six_stage_pipeline -v
```

Example report files in `outputs/six_stages/` show the exact JSON schema. Only the model-backed Persian morphology requires Hazm; tests that cannot load optional packages are skipped or report that dependency explicitly.

## Curated professor demonstration cases

Use the **Test case** dropdown to load eight Persian academic examples or one English baseline. See [Persian research-case guide](PERSIAN_TEST_CASES_EN.md) for expected checks, caveats and a reproducible five-experiment presentation plan.
