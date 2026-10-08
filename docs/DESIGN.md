# Design and homework walkthrough

Version 1.1 accepts text of any length. The original 300-word assignment remains documented below only as background and a regression example.

## Requirements mapping

| Homework requirement | Implementation | Evidence |
| --- | --- | --- |
| Choose a 300-word text | `examples/english_300.txt` | 300 tokens under default rules; also 300 whitespace-separated items |
| Count sentences | `split_sentences` | 26 sample sentences, visible in HTML/JSON |
| Count words | `tokenize_words` | 300 sample tokens, preserved in JSON |
| Count unique words | Counter vocabulary size | 207 sample vocabulary items |
| Extract ten frequent words | Counter ranking, first-appearance ties | Ten rows in all main reports |
| Use Python | Standard library implementation | Python 3.10+ |

## Processing sequence

1. Read a UTF-8 text file, literal string, standard input, or desktop text field.
2. Normalize canonical Unicode representation and optional Persian letter variants.
3. Split sentences using documented punctuation heuristics.
4. Identify word tokens from Unicode character categories.
5. Case-fold tokens unless case-sensitive analysis is selected.
6. Build a frequency table using `collections.Counter`.
7. Count total tokens, vocabulary items, and singleton items.
8. Rank vocabulary by descending frequency and first occurrence for ties.
9. Render results for any input length; no target or pass/fail status is applied.

Sentence analysis and word analysis consume the same normalized source. Sentence boundaries do not change token counts. All interfaces call the same core function, avoiding inconsistent counting rules between outputs.

## Explaining the result in class

The sample contains 300 word tokens but only 207 distinct vocabulary items. Repeated words account for the difference. For example, `the` occurs 19 times. The 166 singleton items occur exactly once; this is a different concept from the 207 unique vocabulary items. Common grammatical words remain because the assignment requests raw frequency analysis.

This is an introductory rule-based NLP pipeline. It counts observable textual patterns; it does not infer intent, understand meaning, translate language, or train a model. It demonstrates the preprocessing issues discussed in the lecture, including normalization, ambiguity, and language-dependent word boundaries.

## Engineering choices

- Core logic is independent of input/output and GUI code.
- No network calls, telemetry, credentials, or external dependencies are used.
- Reports expose options and tokens for reproducibility.
- Input files cannot be overwritten through the same-path export commands.
- HTML escapes user text before inserting it into markup.
- Ranking uses Python's stable Counter ordering for deterministic ties.
- Full token and sentence lists are retained for auditability. Memory use grows with input size; this is a homework tool rather than a streaming large-corpus processor.

## Course source

User-provided `NLP_Session1_White.pdf`, Session 1, “First NLP Pipeline / Course Roadmap” slide (printed number 17), and the matching uploaded homework screenshot. The task asks for a 300-word text and sentence, word, unique-word, and top-ten frequency analysis in Python. The sample prose is original. The supplied lecture file is not redistributed in this repository.
