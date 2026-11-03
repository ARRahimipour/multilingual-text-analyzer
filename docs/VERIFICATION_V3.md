# Verification record — v3.0

Date: 2026-11-03. Environment: Linux, Python 3.12, PySide6 Essentials 6.8.3. Exact direct NLP dependencies are pinned in `requirements-nlp.txt`.

## Executed checks

- `python -m unittest discover -s tests -v`: **108 tests passed**, no skipped tests. Full output: `test-results-v3.txt`.
- The numeric TF-IDF oracle checks manually derived counts, IDF, L2 normalization and cosine. A separate test compares the output with scikit-learn.
- BPE, WordPiece, Unigram and SentencePiece each trained on a small local corpus, encoded a separate query, saved a model and reproduced token IDs after loading it.
- The byte-level BPE example round-tripped multilingual text without unknown IDs.
- The demo script successfully produced reports for all ten lab activities, all four subword algorithms and saved-model batch/chunk experiments.
- CLI normalization with a JSON config and classification with a separate holdout both executed successfully and wrote JSON reports.
- Qt tests executed offscreen, including the real Course Lab worker, Persian/English paragraph direction and matrix display. The actual lab window was rendered and inspected (`course-lab-preview.png`).
- Python compilation, `pip check` and `git diff --check` passed.

## Limits of this verification

English WordNet lemmatization is implemented through NLTK but was not executed against an installed WordNet corpus: the network policy blocked its optional download. The resource helper reports failure; no proxy/security override was used. Persian Hazm morphology and English Porter stemming were executed. WordNet is not bundled in the archive.

Qt verification used Linux offscreen rendering. Windows/macOS installation and physical display behavior were not tested here. Installation needs compatible wheels and internet access or a prepared local wheel cache. The environment itself is not portable and is intentionally excluded from the release.

The tiny classification examples demonstrate the workflow, not general predictive quality. No claim is made about accuracy across arbitrary languages, universal sentence segmentation, large-corpus performance, contextual Finglish conversion or pretrained LLM behavior.

Historical verification files retain their original version labels. This file is the current release record.
