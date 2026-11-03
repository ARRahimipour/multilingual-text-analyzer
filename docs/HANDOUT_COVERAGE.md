# Coverage of the four supplied handouts

Reference: the supplied `Binder1.pdf`, 65 PDF pages. Page numbers below are PDF page positions, not slide numbers. The PDF is not redistributed in this source release.

The imported v2.0 archive implemented the counting assignment and cleaning through the earlier Session 2 scope. It did **not** implement the complete normalization and tokenization activities. Version 3.0 adds an executable Course Lab, CLI commands, examples and tests.

| Handout / PDF pages | Topics | Executable location / interface | Scope |
| --- | --- | --- | --- |
| Cleaning, 1–16 | HTML/entities, scripts/styles, links, email, social noise, emoji, punctuation, numbers, whitespace, controls, task presets | `preprocessing.py`; main window cleaning controls; `--clean-preset` | Implemented; task policies are explicit, source text is preserved |
| Cleaning, 1–16 | Dataset filtering, exact/near duplicates, script ratio, PII | `dataset.py`; dataset dialog; `--dataset` | Implemented; PII masking is pattern-based, not guaranteed anonymization |
| Cleaning, 1–16 | Bytes, Unicode characters and visible graphemes | Course Lab `unicode`, `normalization.py` | Real UTF-8/code-point/grapheme measurements; emoji ZWJ sequences are inspectable |
| Foundations, 17–38 | Sentence, word, unique-word and top-frequency assignment | `core.py`; main window; standard CLI | Implemented with regression fixtures; no 300-word input restriction |
| Foundations, 17–38 | NLP, NLU, NLG, ambiguity, context and evolution | `COURSE_GUIDE.md`, accessible through Lab → Guide | Conceptual explanations; contextual understanding is not claimed |
| Foundations, 17–38 | ML workflow and text classification | Lab `features` / `classify`, `analytics.py` | Genuine local TF-IDF + Multinomial Naive Bayes baseline with separate holdout |
| Normalization, 39–49 | NFC, NFD, NFKC, NFKD; Persian letter variants; digits; marks; tatweel | Lab `normalize` / `unicode` | Implemented as inspectable stages; Arabic letter collapsing is opt-in |
| Normalization, 39–49 | ZWNJ, affix spacing, punctuation, repeated characters | Lab `normalize`, conservative or Hazm mode | Conservative rules do not guess unseparated words; Hazm is a broader alternative |
| Normalization, 39–49 | Contractions, spelling variants, colloquial forms and Finglish | Explicit lexical dictionary plus configurable CLI `lexical_map` | Demonstration mappings and user-supplied dictionary; no universal transliteration/context model |
| Normalization, 39–49 | URL/EMAIL/USER/NUM placeholders and idempotence | Lab `normalize` | Ordered replacement and measured second-pass equality; arbitrary custom maps may not be idempotent |
| Tokenization, 50–65 | Whitespace, regex, word, character, grapheme, NLTK and Hazm | Lab `compare`, `tokenization.py` | Actual library execution; warm-run time and Python allocation measurements |
| Tokenization, 50–65 | BPE, WordPiece, Unigram, SentencePiece | Lab `subword`, local training/load/save | Real locally trained models, token IDs, unknown counts and decoded output |
| Tokenization, 50–65 | Vocabulary and OOV | Lab `oov` | Training vocabulary and query are separate; explicit UNK rate |
| Tokenization, 50–65 | Sentences, abbreviations, decimals, quotes | Existing `split_sentences`; Lab `chunk` | Documented heuristic, not a universal sentence detector |
| Tokenization, 50–65 | Length budgets, overlap, padding, truncation, masks | Lab `chunk` / `batch` | Uses selected saved tokenizer or word counts; reports actual budgets and truncation |
| Later-stage overview | Stopwords, stemming, lemmatization | Lab `morphology` | Persian Hazm; English Porter/WordNet, with explicit POS for English lemmas |
| Later-stage overview | N-grams, BoW, TF-IDF, cosine and Zipf | Lab `features`, Matrices tab | Inspectable numeric results, independently checked against scikit-learn |
| Roadmap | Embeddings, RNN/LSTM, Transformers, BERT/GPT, LLM/RAG | Course Guide | Explained, not presented as trained/deployed models |

## Boundaries that matter

- These are the practical preprocessing activities and an educational classifier, not an implementation of every NLP model name mentioned in the slides.
- spaCy and NLTK Punkt are alternative libraries discussed in the handout; this implementation uses NLTK's resource-free WordPunct/Treebank, Hazm and the project's documented sentence splitter. It does not silently impersonate spaCy or a pretrained model tokenizer.
- Dictionary examples cannot infer every informal form, ambiguous spelling or Finglish word. The CLI accepts an explicit custom mapping; results retain each transformation stage.
- A locally trained WordPiece model is not BERT. Its vocabulary and IDs are not interchangeable with a pretrained model. The same distinction applies to GPT and BPE.
- Language-independent Unicode handling does not guarantee linguistically correct segmentation of every language. Persian and English have specific optional morphology support. Arabic text can be displayed and normalized without claiming a trained Arabic morphological analyzer.
- No maximum word count is enforced by the app. Memory and processing time still matter: dense feature matrices and all-pairs cosine comparisons are intended for classroom corpora.
- GUI tables preview at most 1,000 rows; complete JSON export includes all rows. Batch truncation is an explicit experiment and reports removed-token counts.

## Verification map

`tests/test_core.py`, `test_cli.py`, `test_preprocessing.py`, `test_direction.py` and `test_gui.py` retain the original regression checks. `test_lab.py` adds Unicode, idempotence, numerical oracles, OOV, masks, chunk coverage, model round-trips, morphology and holdout leakage checks. `test_lab_gui.py` checks a real Qt worker and per-paragraph text direction. `scripts/run_course_demo.py` exercises all ten activities and four trained subword methods.
