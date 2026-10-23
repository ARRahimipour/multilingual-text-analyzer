# Session 2 implementation map — slides 1–17

This release implements the **topics actually covered through slide 17** of the
supplied `NLP_Session2.pdf`. Slide 17 is the section divider introducing
normalization; stemming, stopwords, NLTK/Hazm, Zipf and Bag-of-Words appear
later and have **not** been added or represented as studied topics.

| Slides | Topic | Implemented in this project |
| --- | --- | --- |
| 1–3 | Session overview, NLP pipeline, Persian Unicode pitfalls | Existing token/frequency analyzer retained; optional cleaning pipeline with explicit task preset |
| 4–5 | Raw/noisy text and order of cleaning → normalization → tokenization | `clean_text` returns cleaned copy and an intermediate sentence snapshot; `analyze` tokenizes final cleaned text |
| 6–7 | HTML, URLs, email, emoji, punctuation, numbers, whitespace | HTML parser discards script/style, decodes entities; configurable URL/email, emoji, punctuation, number and whitespace behavior |
| 8 | Source-specific web/PDF/social noise | Hashtags without `#`, retweet marker, mentions, repeated `!`, optional joining of PDF-like hyphenated line wraps; preserving PDF/document source fidelity still requires review |
| 9 | Emoji retain/remove/label; normalize quotes/ellipsis/repeats; preserve ZWJ | Three emoji modes, quote canonicalization, ellipsis normalization, optional punctuation compression; ZWJ preserved |
| 10–11 | Unicode letters, half-space, encoding and byte lengths | NFC/NFKC, Arabic kaf/yeh → Persian, optional digit styles, ZWNJ preservation, UTF-8 read/write, code-point and UTF-8 byte before/after statistics |
| 12 | Remove ZWSP/BOM/LRM/RLM and optional ASCII controls | Safe/controls/none modes; ZWNJ and ZWJ intentionally excluded |
| 13 | Code points versus visual grapheme units | Byte and code-point measurements clearly labelled; no false claim that Python `len()` counts grapheme clusters |
| 14 | Dataset deduplication, language/script screening, length, privacy | CSV/TSV/JSONL cleaning, post-normalization exact and optional heuristic near-dedup, length thresholds, Arabic-script ratio, opt-in email/mobile/ID masking |
| 15 | Record stats, preserve raw data, preview changes | Raw GUI editor/source file unchanged; preview, stage change/length log, token and vocabulary before/after counts, dataset keep/drop reasons |
| 16 | Task-dependent cleaning | General, sentiment, topic, NER, transformer, spam presets and overridable controls |
| 17 | Normalization section header | Unicode/letter/digit normalization support is provided; later teaching content deliberately not assumed |

## Interface and reproducibility

- **Desktop:** choose a cleaning preset and tune settings; inspect the cleaned
  preview without changing the input. The original Session 1 counting mode is
  the default. Use **Clean dataset** for a separate cleaned data file.
- **CLI:** pass `--clean-preset NAME` for one text, or `--dataset` with a
  `.csv`, `.tsv` or `.jsonl` input and a distinct `--output` path. Dataset
  summaries are emitted as JSON. JSON analysis reports include the cleaned
  text and per-stage audit statistics.
- **API:** `preprocessing.preset(name)`, `preprocessing.clean_text(source,
  options)`, `core.analyze(source, AnalysisOptions(preprocessing=options))`, and
  `dataset.clean_dataset(...)` can all be used without a GUI or third-party NLP
  models.

Example:

```bash
python main.py --text '<p>سلام&nbsp;دنیا 😍!</p>' --clean-preset sentiment --format json
python main.py input.csv --dataset --text-column text --clean-preset topic \
  --near-duplicate 0.9 --output cleaned.csv
python -m unittest discover -s tests -v
```

## Deliberate boundaries

1. **Cleaning loses information.** Choose the preset according to the task.
   For sentiment, emoji and `!!!` may matter; for NER, amounts and dates matter.
2. **Sentence splitting precedes destructive punctuation handling.** It is a
   multilingual heuristic, not a statistical sentence model.
3. **Unicode `len()` is code points, not grapheme clusters.** The project never
   equates these; visual grapheme segmentation would require another library.
4. **Script ratio is not Persian language identification.** Arabic uses many of
   the same letters. The ratio is a simple filter, not `langdetect`/fastText.
5. **PII masking is not guaranteed anonymization.** It recognizes email,
   Iranian mobile formats and 10-digit numeric identifiers, with possible
   false positives or misses. Names, addresses and other columns need human
   review before publication. Never export untreated source text publicly.
6. **Near-duplicate detection is heuristic.** It uses shared shingles plus
   sequence similarity and checks at most 250 candidates per text. For a
   train/test split, deduplicate globally and separately audit leakage.
7. **Morphological analysis is not covered here.** Stopword removal, stemming,
   lemmatization and word segmentation models are outside the first 17 slides.
8. **No external PDF/Word ingestion dependency.** Copy or extract text from
   those sources; use the optional broken-line cleanup and visually audit the
   result (especially Persian presentation forms and page headers).
