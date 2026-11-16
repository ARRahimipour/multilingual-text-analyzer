# Expanded course lab — rebuilt v3.1.1

This rebuild restores the expanded 118-page handout activities after the earlier temporary release files expired. It descends from GitHub commit `f48d6a2`; it does not pretend to reproduce the lost commit hashes byte-for-byte.

## Desktop workflow

Use Python 3.12. Run `python setup_env.py`, then `python run_gui.py`. Open **Course Lab**, select an activity, enter your text/query and put corpus documents in the lower-left editor, one per line. Classification input is JSONL with string `text` and `label` fields.

**Advanced options → Open JSON options** loads an included example configuration. JSON overrides the controls above. Clear the JSON to `{}` when switching to an unrelated activity. Representation/search/classifier settings belong inside `vectorizer`; language and maximum n-gram length otherwise inherit the visible controls. Results appear in Details, Matrices and Full JSON and can be exported without modifying source text.

## Activities

| Activity | What it does | Example configuration |
| --- | --- | --- |
| `pipeline` | Top-ten words, token/type counts and a measured explanation across raw, normalized, filtered and stemmed/lemmatized stages | `pipeline_config.json` |
| `stopwords` | Dictionary, custom or statistical stopwords, removal audit and protected words | `stopwords_config.json` |
| `learn_stopwords` | Random Forest word-label experiment with held-out labels and feature importances | `learned_stopwords_config.json` |
| `library_pipeline` | Actual Hazm/NLTK sentence, word, stopword and morphology stages | `english_pipeline_config.json` for English |
| `representation` | Sparse BoW/TF-IDF, explicit IDF convention and memory statistics | `textbook_config.json` |
| `search` | Fit on corpus, transform queries, rank by cosine similarity | `retrieval_config.json` |
| `classify_compare` | BoW vs TF-IDF, same split, Logistic Regression or Naive Bayes, full metrics | `classification_compare_config.json` |

### Stopwords and morphology

`stopword_mode` accepts `dictionary`, `custom`, or `statistical`. English dictionary mode uses scikit-learn's bundled list; Persian uses Hazm. `custom_stopwords` adds strings; `protected_words` overrides removal. `preserve_negation` defaults to true but its finite list is not a grammatical negation detector. Protect task-specific negated verbs and aspect terms explicitly.

Statistical selection requires all thresholds: `min_document_ratio` (default .8), `max_idf` (.3), `min_frequency` (2). Its IDF is `ln(N/df)`. Frequent domain terms are not necessarily irrelevant: inspect suggestions before removal.

`pipeline` uses case-folded Unicode word counts before Persian normalization as the raw baseline. It does not silently perform destructive HTML cleaning. Morphology follows normalization and stopword filtering. Choose `morph_method="stem"` or `"lemma"`, never both sequentially. English stemming accepts `stemmer="porter"`, `"snowball"`, or `"lancaster"`; WordNet uses explicit `pos` (`n`, `v`, `a`, `r`, `s`).

`learn_stopwords` needs `word_labels` such as `{"word":"the","label":1}`. One means stopword, zero means content word. Supply at least eight distinct corpus words with at least two examples per class. Feature statistics use the unlabeled corpus; labels are split with a seed. This is a transductive demonstration, not a language-wide classifier. POS is omitted without a tagged model. Probabilities are suggestions, not automatic deletions.

### Optional NLTK data

`library_pipeline` runs actual Hazm operations for Persian. For English it uses NLTK sentence/word tokenization and the NLTK stopword corpus, followed by Porter or WordNet. Download resources once using the environment's Python:

```bash
python setup_resources.py --resources punkt_tab stopwords wordnet
```

If network policy blocks downloads, install approved local NLTK data under `.nlp_data` or use the resource-free tokenizer/stemmer activities. The app does not bypass network policy or download data during analysis.

### Representation controls

| `vectorizer` option | Default / purpose |
| --- | --- |
| `language` | `fa` or `en`; consistent normalization for corpus/query/test |
| `ngram_min`, `ngram_max` | Inclusive range, 1 through 5 |
| `min_df`, `max_df` | Integer document counts or floating proportions; 1 and 1.0 |
| `max_features` | Vocabulary cap, null by default |
| `binary` | Presence/absence counts, false by default |
| `idf_mode` | `smooth` or `textbook` |
| `norm` | `l2` or `none` |
| `sublinear_tf` | Positive TF becomes `1 + ln(TF)`, false by default |
| `remove_stopwords` | Dictionary filtering, false by default |
| `custom_stopwords`, `protected_words` | Explicit normalized word lists |
| `preserve_negation` | True by default |

The page 110 fixture uses raw counts, `idf_mode="textbook"` and `norm="none"`. Here IDF is `ln(N/df)`, so `بود` has zero weight. Default smoothed IDF is `ln((1+N)/(1+df))+1` followed by L2 normalization; a ubiquitous word then has IDF one. These numerical conventions must not be confused.

Complete CSR arrays are always exported. Dense previews are limited to 10,000 cells, and all-pairs cosine to 100 documents. Large corpora still cost memory and time. Single-character Persian words and ZWNJ are retained by the tokenizer. Empty/fully filtered vocabularies raise an error.

### Retrieval and classification

For search, load `search_fa.txt` and `retrieval_config.json`: three queries against six documents, returning five results each. Without a `queries` override, the input editor is the query. Vocabulary/IDF are fitted only on corpus documents. Ties follow document order; all-zero queries yield zero scores, not semantic matches.

For classifier comparison, open `classification_fa_train.jsonl` as corpus and `classification_fa_holdout.jsonl` through **Load holdout**. Load the classifier configuration. If no holdout is supplied, a seeded stratified split is used (`test_size=.25`, `random_state=42`). Both representations use the same split and training vocabulary. Duplicate normalized training documents, train/holdout overlap and unseen holdout labels are rejected. Near duplicates and source leakage still need human review.

Results include accuracy, macro precision/recall/F1, class reports and confusion matrices (rows actual, columns predicted in `class_order`). The small original example is classroom data, not a benchmark. Scores are not production claims.

## Commands

With `.venv` activated:

```bash
python main.py --lab pipeline --text "كتاب کتاب و کتاب‌ها خوب نیست" --lab-config examples/pipeline_config.json
python main.py --lab representation --text "" --training-corpus examples/representation_fa.txt --lab-config examples/textbook_config.json
python main.py --lab search --text "" --training-corpus examples/search_fa.txt --lab-config examples/retrieval_config.json
python main.py --lab classify_compare --text "فیلم خوب" --training-corpus examples/classification_fa_train.jsonl --evaluation examples/classification_fa_holdout.jsonl --lab-config examples/classification_compare_config.json
python main.py --lab learn_stopwords --text "" --training-corpus examples/word_label_corpus.txt --lab-config examples/learned_stopwords_config.json
python scripts/run_expanded_demo.py
```

Use `--output outputs/report.json` to save full JSON. The demo writes results under `outputs/expanded-demo`. No cloud inference is involved.
