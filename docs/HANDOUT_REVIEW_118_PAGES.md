# Expanded handout review — rebuilt v3.1.1

Reference: the attached 118-page `Binder1.pdf`, physical PDF page numbering. Baseline: repository `ARRahimipour/multilingual-text-analyzer`, commit `f48d6a2`. This reconstruction replaces expired local v3.1 release files; new commit hashes and timestamps are expected.

| Pages | Subject | Implementation |
| --- | --- | --- |
| 1-22 | NLP foundations and counting | Existing counters and conceptual guide retained |
| 23-38 | Cleaning, noise, Unicode and datasets | Existing preprocessing/dataset modules retained |
| 39-49 | Normalization | Existing Unicode forms, letter/digit/spacing policies and audit retained |
| 50-65 | Tokenization, subwords and model inputs | Existing actual local tokenizer training, OOV, padding and chunks retained |
| 66-76, 81-84 | Dictionary, domain and statistical stopwords | New stopwords activity with explicit custom/protected words, negation protection and removal audit |
| 77-80 | Supervised word-label example | New Random Forest, explicit labels, held-out word-label evaluation and feature importance |
| 85-96 | Morphology | Existing Hazm/Porter/WordNet plus Snowball and Lancaster choices |
| 97 | Four-stage top-ten comparison | New pipeline activity with raw/normalized/filtered/morphological counts and generated measured explanation |
| 98-99 | Hazm/NLTK full pipelines | New actual library sentence/word/stopword/morphology activity; optional NLTK resource installer |
| 100-107 | BoW, n-grams and sparse representation | New CSR output, memory statistics and vectorizer controls |
| 108-111 | Textbook and smoothed TF-IDF | Separate formulas, optional normalization and verified page 110 example |
| 112-113 | Cosine retrieval | Fit corpus once, transform queries without fitting, deterministic ranking |
| 114-116 | Classifiers and evaluation | BoW/TF-IDF comparison with same split, train-only fitting, class/macro metrics and confusion matrices |
| 118 | Persian classification and three-query retrieval | Original example train/holdout data, six search documents, three queries and five results each |

## Scope

The handout names alternative libraries and research directions. This release does not claim spaCy/Parsivar adapters, automatic POS tagging, LASSO/chi-square/mutual-information selection, clustering, attention-based word importance or trained embeddings/LLMs. The Random Forest example omits POS without a tagged model. Unlabeled corpus statistics are shared in this transductive word-label experiment; held-out labels remain separate.

Stopword importance is task-dependent, and attention alone does not establish irrelevance. Protection lists are finite, not semantic reasoning. The pipeline's raw stage uses case-folded Unicode word tokens before Persian normalization; destructive cleaning remains separately inspectable. Legacy features/classify activities remain for compatibility. Choose representation/search/classify_compare for the expanded exercises.

Textbook IDF is ln(N/df); smooth IDF is ln((1+N)/(1+df))+1. The common word بود has textbook IDF zero. Default library output adds smoothing and L2 normalization. Zero vectors produce zero cosine, and unknown queries never expand the corpus vocabulary.

See EXPANDED_LAB_GUIDE.md for setup, all settings and runnable commands.
