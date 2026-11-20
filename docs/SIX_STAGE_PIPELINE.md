# Six-Stage NLP Preprocessing Pipeline — Session 2

This guide explains the reproducible, ordered pipeline in the course handout. The core flowchart appears on **PDF page 27**; subsequent sections address cleaning, Unicode normalization, sentence and word segmentation, optional stopword filtering, and stemming or lemmatization.

## Run the desktop experiment

```bash
python setup_env.py
python run_gui.py
```

1. Open **06 / Six-stage pipeline** from the main window.
2. Pick a named **Test case** and click **Load case**, or paste your own UTF-8 text. Loading a case selects its intended language and a suggested cleaning profile.
3. Review **Language**, **Cleaning profile**, **Tokenizer**, **Persian spacing**, **Stage 6 / morphology**, and **Digit format**. The stopword and negation controls are optional.
4. Click **Run all 6 stages**. The six-stage navigator is a responsive, multirow grid, so all stages remain reachable without a horizontal navigation scrollbar.
5. Select any stage, then compare **Stage output**, **Audit & evidence**, and **Reproducible JSON**. Use **Show spaces & ZWNJ** to inspect Unicode spaces without changing the data.
6. Click **Export JSON** to preserve source text, configuration, all stage outputs, token statistics, and morphological mappings.

The application uses the primary monitor's **available screen geometry** instead of assuming a fixed desktop resolution. The main window and pipeline have a vertically scrollable content area. Resize the window freely, including on a laptop or with OS display scaling.

The original text remains editable and is never overwritten by running the pipeline.

## All six stages

| Stage | Operation | Observable evidence |
|---|---|---|
| 01 Raw input | Preserve the unmodified UTF-8 source | Character and byte lengths |
| 02 Cleaning | Remove or transform task-specific noise | Per-operation changed/unchanged flags; boundary-preserving sentence snapshot |
| 03 Normalization | Normalize Unicode, Persian letters, digits, diacritics and spacing | Before/after counters, ZWNJ inspector, second-pass idempotence |
| 04 Tokenization | Split sentences and lexical word units | Sentence list, token count, unique types, top-ten counts |
| 05 Stopwords | Optionally remove frequent functional terms | Exact removed tokens, protected negation, before/after token counts |
| 06 Stemming / Lemmatization | Choose one morphological reduction method | Backend, method and token-to-result mappings |

Stage 5 can be disabled; Stage 6 supports **Stem**, **Lemma** or **None**. Neither is an unconditional improvement to all tasks. Do not apply stemming and lemmatization sequentially.

### Important configuration details

- `cleaning_preset`: `general`, `sentiment`, `topic`, `ner`, `transformer`, or `spam`. Emojis, punctuation and numbers can encode sentiment, named entities or task context, so removal is selective.
- `cleaning`: additional `PreprocessOptions` overrides, such as `emoji_mode`, `punctuation_mode`, `number_mode`, `mask_pii`, `remove_urls` or `join_broken_lines`.
- `normalization`: `NormalizationOptions` overrides such as `unicode_form`, `digit_style`, `spacing`, `remove_marks`, `casefold`, `elongation`, `lexical_map` and `placeholders`.
- `tokenizer`: `auto`, `hazm`, `nltk`, or `regex`. Automatic mode selects Hazm for Persian and NLTK for English. The simpler regex alternative can be inspected without trained tokenizer resources.
- `stopword_mode`: `dictionary`, `custom`, or `statistical` (the last mode requires multiple corpus documents). Use `protected_words` for named technical terms and `preserve_negation` when polarity matters.
- `morph_method`: `stem`, `lemma`, `none`. English stemming supports Porter, Snowball and Lancaster; English WordNet lemmatization additionally requires a POS selection. Persian morphology uses Hazm.
- `english_stopword_library`: `nltk` or `sklearn`. Model-backed functionality needs its local language resources to be installed once.

### Persian typography rules

A **regular space U+0020** separates words, whereas **ZERO WIDTH NON-JOINER U+200C** (a half-space) separates components inside a Persian token. The display-only inspector shows `·` for spaces, `⟦ZWNJ⟧` for half-spaces, `⟦NBSP⟧` for nonbreaking spaces and `⟦ZWJ⟧` for the different joiner used by some emoji sequences.

Conservative spacing intentionally repairs a limited number of high-confidence patterns. It avoids changing unrelated words that merely *resemble* plurals. Hazm can handle broader Persian morphology, but no automatic normalizer can always infer the writer's intention from ambiguous or informal text. Check the actual output and normalization idempotence before relying on results.

### Sentence-boundary preservation

Sentence segmentation is computed from the **pre-punctuation-removal snapshot**. This preserves potential sentence boundaries when a topic-cleaning profile removes punctuation from the main cleaned text, as emphasized in the handout around PDF page 31.

## Command-line reproduction

```bash
python main.py examples/six_stages_sample_fa.txt --lab six_stages --lab-config examples/six_stages_persian_config.json --output outputs/analysis_fa.json
python main.py --lab six_stages --text "the children were running and the cats are sleeping" --lab-config examples/six_stages_english_config.json --output outputs/analysis_en.json
python scripts/run_six_stage_demo.py
```

The JSON report uses UTF-8 and includes the exact six stages even when an optional operation is disabled.

## Research limitations

- Stems can be truncated strings that are not dictionary words. Lemmas depend on linguistic resources and, sometimes, part-of-speech information.
- Colloquial Persian, joined compounds, poorly extracted PDF text, hidden layout fragments and informal hashtags are difficult cases; use the supplied benchmarks to identify incorrect edits rather than assuming every transformation is valid.
- Stopword filtering is not always appropriate for named-entity recognition, question answering, sentiment classification or Transformer-based models.
- The built-in examples use synthetic entities rather than real contact details. The cleaning pipeline is not a complete personally identifiable information redaction product.

## Test cases and expected checks

See [English test-case guide](PERSIAN_TEST_CASES_EN.md). Every fixture lives under `examples/academic_cases/` and is selectable from the desktop. No online service is required for processing.

## Verification

```bash
python scripts/verify_spacing.py
python -m unittest discover -s tests -v
```

GUI-dependent tests need PySide6; Persian Hazm tests need Hazm and its local resources. A skipped dependency-specific test is not evidence that the corresponding feature was verified.
