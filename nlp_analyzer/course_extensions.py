"""Executable exercises from the expanded 118-page handout."""
from collections import Counter
import math
from .analytics import words, morphology
from .normalization import normalize, NormalizationOptions

NEGATIONS = {'fa': {'نه', 'نیست', 'نیستم', 'نیستند', 'هرگز', 'نبود', 'نشد'},
             'en': {'no', 'not', 'nor', 'never', 'cannot', "don't", "isn't", "won't"}}


def text_tokens(text, language='fa'):
    if language not in ('fa', 'en'):
        raise ValueError('Choose language fa or en.')
    config = NormalizationOptions(persian_letters=language == 'fa',
        spacing='conservative' if language == 'fa' else 'none', casefold=True)
    return words(normalize(text, config)['text'])


def stopword_set(language='fa', custom=None, protected=None, preserve_negation=True, dictionary=True):
    if language not in NEGATIONS: raise ValueError('Choose language fa or en.')
    for values in (custom, protected):
        if values is not None and (not isinstance(values, list) or not all(isinstance(v, str) for v in values)):
            raise ValueError('Custom and protected words must be lists of strings.')
    stops = set()
    if dictionary:
        if language == 'fa':
            from hazm import stopwords_list
            stops = set(stopwords_list())
        else:
            from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
            stops = set(ENGLISH_STOP_WORDS)
    canonical = lambda values: {' '.join(text_tokens(v, language)) for v in values}
    keep = canonical(protected or [])
    if preserve_negation: keep |= canonical(NEGATIONS[language])
    return canonical(stops | set(custom or [])) - keep


def vocabulary_statistics(corpus, language='fa'):
    if not corpus or not all(isinstance(d, str) for d in corpus):
        raise ValueError('Supply a nonempty list of text documents.')
    docs = [text_tokens(d, language) for d in corpus]
    counts = Counter(t for doc in docs for t in doc)
    df = Counter(t for doc in docs for t in set(doc)); total = sum(counts.values())
    return [{'word': w, 'frequency': counts[w], 'document_frequency': df[w],
        'document_ratio': df[w]/len(docs), 'idf': math.log(len(docs)/df[w]),
        'relative_frequency': counts[w]/total, 'length': len(w)} for w in sorted(counts)]


def stopword_activity(text, corpus, language='fa', stopword_mode='dictionary', custom_stopwords=None,
                      protected_words=None, preserve_negation=True, min_document_ratio=.8,
                      max_idf=.3, min_frequency=2):
    if stopword_mode not in ('dictionary', 'custom', 'statistical'):
        raise ValueError('Choose dictionary, custom or statistical stopwords.')
    if not 0 <= min_document_ratio <= 1 or not math.isfinite(max_idf) or max_idf < 0 or min_frequency < 1:
        raise ValueError('Invalid statistical thresholds.')
    stops = stopword_set(language, custom_stopwords, protected_words, preserve_negation,
                         dictionary=stopword_mode == 'dictionary')
    stats = vocabulary_statistics(corpus, language)
    if stopword_mode == 'statistical':
        candidates = [r['word'] for r in stats if r['document_ratio'] >= min_document_ratio
                      and r['idf'] <= max_idf and r['frequency'] >= min_frequency]
        stops |= stopword_set(language, candidates, protected_words, preserve_negation, False)
    tokens = text_tokens(text, language); removed = [t for t in tokens if t in stops]
    kept = [t for t in tokens if t not in stops]
    return {'source': text, 'mode': stopword_mode, 'tokens': kept, 'removed_tokens': removed,
        'before_count': len(tokens), 'after_count': len(kept),
        'removed_fraction': len(removed)/len(tokens) if tokens else 0,
        'stopwords': sorted(stops), 'rows': [dict(r, selected=r['word'] in stops) for r in stats],
        'formula': 'idf = ln(N/df)', 'preserve_negation': preserve_negation,
        'note': 'Candidates depend on this corpus. Explicit protection overrides removal; the finite negation list is not a grammatical detector.'}


def pipeline_comparison(text, language='fa', morph_method='stem', stemmer='porter', pos='n',
                        custom_stopwords=None, protected_words=None, preserve_negation=True):
    raw = words(text); normalized = text_tokens(text, language)
    stops = stopword_set(language, custom_stopwords, protected_words, preserve_negation)
    filtered = [t for t in normalized if t not in stops]
    transformed = morphology(' '.join(filtered), language, morph_method, False, pos, stemmer)['tokens']
    stages = []
    for name, tokens in [('raw', raw), ('normalized', normalized), ('without_stopwords', filtered),
                        ('stemmed' if morph_method == 'stem' else 'lemmatized', transformed)]:
        counts = Counter(tokens)
        stages.append({'stage': name, 'token_count': len(tokens), 'type_count': len(counts),
            'top_10': [{'word': w, 'count': n} for w, n in counts.most_common(10)], 'tokens': tokens})
    return {'source': text, 'stages': stages, 'analysis':
        f'Normalization changes token count from {len(raw)} to {len(normalized)}. '
        f'Stopword filtering removes {len(normalized)-len(filtered)} occurrences. '
        f'Morphology changes vocabulary size from {len(set(filtered))} to {len(set(transformed))}. '
        'These changes do not demonstrate better task accuracy.',
        'note': 'Raw means case-folded Unicode words before Persian normalization. Stemming and lemmatization are alternatives, never sequential.'}


def vectorize(corpus, language='fa', ngram_min=1, ngram_max=1, min_df=1, max_df=1.0,
              max_features=None, binary=False, idf_mode='smooth', norm='l2', sublinear_tf=False,
              remove_stopwords=False, custom_stopwords=None, protected_words=None, preserve_negation=True):
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.preprocessing import normalize as matrix_normalize
    import numpy as np
    if not corpus or not all(isinstance(d, str) for d in corpus):
        raise ValueError('Supply a nonempty list of documents.')
    if idf_mode not in ('smooth', 'textbook') or norm not in ('l2', 'none'):
        raise ValueError('Choose smooth/textbook IDF and l2/none normalization.')
    if not 1 <= ngram_min <= ngram_max <= 5: raise ValueError('Require 1 <= ngram_min <= ngram_max <= 5.')
    stops = stopword_set(language, custom_stopwords, protected_words, preserve_negation, remove_stopwords)
    def analyzer(text):
        tokens = [t for t in text_tokens(text, language) if t not in stops]
        return [' '.join(tokens[i:i+n]) for n in range(ngram_min, ngram_max+1)
                for i in range(len(tokens)-n+1)]
    cv = CountVectorizer(analyzer=analyzer, min_df=min_df, max_df=max_df,
                         max_features=max_features, binary=binary)
    counts = cv.fit_transform(corpus).astype(float).tocsr()
    df = np.asarray((counts > 0).sum(axis=0)).ravel()
    idf = np.log((1+len(corpus))/(1+df))+1 if idf_mode == 'smooth' else np.log(len(corpus)/df)
    def weight(matrix):
        matrix = matrix.astype(float).tocsr(copy=True)
        if sublinear_tf: matrix.data = 1 + np.log(matrix.data)
        matrix = matrix.multiply(idf).tocsr(); matrix.eliminate_zeros()
        return matrix_normalize(matrix, norm='l2') if norm == 'l2' else matrix
    return cv, counts, weight(counts), df, idf, weight


def csr_report(matrix):
    matrix = matrix.tocsr(); cells = matrix.shape[0]*matrix.shape[1]
    return {'format': 'csr', 'shape': list(matrix.shape), 'data': matrix.data.tolist(),
        'indices': matrix.indices.tolist(), 'indptr': matrix.indptr.tolist(), 'nnz': matrix.nnz,
        'density': matrix.nnz/cells if cells else 0,
        'storage_bytes': matrix.data.nbytes+matrix.indices.nbytes+matrix.indptr.nbytes,
        'dense_float64_bytes': cells*8}


def representation(corpus, **settings):
    from sklearn.metrics.pairwise import cosine_similarity
    cv, counts, weighted, df, idf, _ = vectorize(corpus, **settings)
    result = {'vocabulary': cv.get_feature_names_out().tolist(), 'document_frequency': df.tolist(),
        'idf': idf.tolist(), 'bow_csr': csr_report(counts), 'tfidf_csr': csr_report(weighted),
        'settings': settings, 'formula': 'ln(N/df)' if settings.get('idf_mode') == 'textbook' else 'ln((1+N)/(1+df))+1'}
    if counts.shape[0]*counts.shape[1] <= 10000:
        result.update(bow=counts.toarray().tolist(), tfidf=weighted.toarray().tolist())
    if len(corpus) <= 100: result['cosine_similarity'] = cosine_similarity(weighted).tolist()
    result['note'] = 'CSR exports are complete. Dense previews: at most 10,000 cells; all-pairs cosine: at most 100 documents.'
    return result


def search_documents(corpus, queries, top_k=5, **settings):
    from sklearn.metrics.pairwise import cosine_similarity
    if not isinstance(top_k, int) or top_k < 1: raise ValueError('top_k must be positive.')
    if not queries or not all(isinstance(q, str) for q in queries): raise ValueError('Supply text queries.')
    cv, _, matrix, _, _, weight = vectorize(corpus, **settings)
    results = []
    for query in queries:
        q = weight(cv.transform([query]))  # Never fit vocabulary or IDF on queries.
        scores = cosine_similarity(q, matrix).ravel()
        order = sorted(range(len(corpus)), key=lambda i: (-scores[i], i))[:top_k]
        results.append({'query': query, 'zero_vector': q.nnz == 0,
            'matches': [{'rank': j+1, 'document_index': i, 'text': corpus[i], 'score': float(scores[i])}
                        for j, i in enumerate(order)]})
    return {'queries': results, 'vocabulary': cv.get_feature_names_out().tolist(),
        'note': 'Vocabulary and IDF are fitted on documents only. Ties follow input order; zero query vectors yield zero scores.'}


def classification_comparison(training_records, evaluation_records=None, query='', test_size=.25,
                              random_state=42, classifier='logistic', **settings):
    from sklearn.model_selection import train_test_split
    from sklearn.linear_model import LogisticRegression
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
    def validate(records):
        if not records or any(not isinstance(r, dict) or not isinstance(r.get('text'), str)
            or not isinstance(r.get('label'), str) or not r['label'] for r in records):
            raise ValueError('Each record needs string text and a nonempty string label.')
    validate(training_records)
    key = lambda r: ' '.join(text_tokens(r['text'], settings.get('language', 'fa')))
    if len({key(r) for r in training_records}) != len(training_records):
        raise ValueError('Remove normalized duplicate training documents before splitting.')
    if len({r['label'] for r in training_records}) < 2: raise ValueError('At least two classes are required.')
    if evaluation_records is None:
        train, test = train_test_split(training_records, test_size=test_size, random_state=random_state,
                                      stratify=[r['label'] for r in training_records])
        strategy = 'seeded stratified split'
    else:
        validate(evaluation_records); train, test = training_records, evaluation_records; strategy = 'explicit holdout'
    if {key(r) for r in train} & {key(r) for r in test}: raise ValueError('Normalized train/holdout duplicate detected; remove leakage.')
    if not {r['label'] for r in test} <= {r['label'] for r in train}: raise ValueError('Holdout-only label detected.')
    if classifier not in ('logistic', 'naive_bayes'): raise ValueError('Choose logistic or naive_bayes.')
    cv, counts, weighted, _, _, weight = vectorize([r['text'] for r in train], **settings)
    test_counts = cv.transform([r['text'] for r in test]); query_counts = cv.transform([query])
    labels = sorted({r['label'] for r in train}); rows = []
    for name, x, xt, xq in [('bow', counts, test_counts, query_counts),
                           ('tfidf', weighted, weight(test_counts), weight(query_counts))]:
        model = LogisticRegression(max_iter=1000, random_state=random_state) if classifier == 'logistic' else MultinomialNB()
        model.fit(x, [r['label'] for r in train]); predicted = model.predict(xt); actual = [r['label'] for r in test]
        report = classification_report(actual, predicted, labels=labels, output_dict=True, zero_division=0)
        rows.append({'representation': name, 'accuracy': float(accuracy_score(actual, predicted)),
            'precision_macro': report['macro avg']['precision'], 'recall_macro': report['macro avg']['recall'],
            'f1_macro': report['macro avg']['f1-score'], 'report': report,
            'confusion_matrix': confusion_matrix(actual, predicted, labels=labels).tolist(),
            'prediction': str(model.predict(xq)[0]), 'holdout_predictions': predicted.tolist()})
    return {'rows': rows, 'class_order': labels, 'classifier': classifier, 'split': strategy,
        'training_rows': len(train), 'evaluation_rows': len(test), 'random_state': random_state,
        'vocabulary': cv.get_feature_names_out().tolist(),
        'note': 'Both representations share the split and training vocabulary. Vocabulary and IDF never fit holdout/query data. Scores describe this sample only.'}


def learned_stopwords(corpus, records, language='fa', random_state=42):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report
    stats = vocabulary_statistics(corpus, language); indexed = {r['word']: r for r in stats}
    features = ['relative_frequency', 'idf', 'tfidf', 'length']
    feature = lambda r: [r['relative_frequency'], r['idf'], r['relative_frequency']*r['idf'], r['length']]
    x, y, seen = [], [], set()
    for record in records:
        if not isinstance(record, dict) or record.get('label') not in (0, 1) or not isinstance(record.get('word'), str):
            raise ValueError('Word labels require word and label (0 or 1).')
        token = ' '.join(text_tokens(record['word'], language))
        if token not in indexed or token in seen: raise ValueError('Labeled words must be distinct and present in the corpus.')
        seen.add(token); x.append(feature(indexed[token])); y.append(record['label'])
    if len(x) < 8 or set(y) != {0, 1} or min(Counter(y).values()) < 2:
        raise ValueError('Provide eight labeled words with at least two per class.')
    train, test = train_test_split(list(range(len(x))), test_size=.25, random_state=random_state, stratify=y)
    model = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=random_state)
    model.fit([x[i] for i in train], [y[i] for i in train])
    prediction = model.predict([x[i] for i in test])
    probabilities = model.predict_proba([feature(r) for r in stats])[:, list(model.classes_).index(1)]
    return {'rows': [dict(r, stopword_probability=float(p)) for r, p in zip(stats, probabilities)],
        'features': features, 'feature_importance': dict(zip(features, map(float, model.feature_importances_))),
        'evaluation': classification_report([y[i] for i in test], prediction, output_dict=True, zero_division=0),
        'training_words': len(train), 'holdout_words': len(test),
        'note': 'Transductive word-label experiment: corpus statistics are shared, labels held out. POS is omitted without a model. Suggestions are not automatic deletions.'}


def library_pipeline(text, language='fa', morph_method='stem', pos='n', preserve_negation=True):
    if morph_method not in ('stem', 'lemma'): raise ValueError('Choose stem or lemma.')
    if language == 'fa':
        from hazm import Normalizer, sent_tokenize, word_tokenize, stopwords_list, Stemmer, Lemmatizer
        normalized = Normalizer().normalize(text); sentences = sent_tokenize(normalized); tokens = word_tokenize(normalized)
        stops = set(stopwords_list()); transform = Stemmer().stem if morph_method == 'stem' else Lemmatizer().lemmatize
    elif language == 'en':
        import nltk
        import unicodedata
        from pathlib import Path
        path = str(Path(__file__).resolve().parents[1]/'.nlp_data')
        if path not in nltk.data.path: nltk.data.path.insert(0, path)
        try:
            from nltk.corpus import stopwords
            from nltk.stem import PorterStemmer, WordNetLemmatizer
            normalized = unicodedata.normalize('NFKC', text).lower()
            sentences = nltk.sent_tokenize(normalized); tokens = nltk.word_tokenize(normalized)
            stops = set(stopwords.words('english'))
            if pos not in ('n', 'v', 'a', 'r', 's'): raise ValueError('Invalid WordNet POS.')
            transform = PorterStemmer().stem if morph_method == 'stem' else lambda t: WordNetLemmatizer().lemmatize(t, pos)
        except LookupError as exc:
            raise ValueError('Install local resources: python setup_resources.py --resources punkt_tab stopwords wordnet') from exc
    else: raise ValueError('Choose language fa or en.')
    if preserve_negation: stops -= NEGATIONS[language]
    filtered = [t for t in tokens if any(c.isalpha() for c in t) and t not in stops]
    try: transformed = [transform(t) for t in filtered]
    except LookupError as exc: raise ValueError('Install WordNet: python setup_resources.py --resources wordnet') from exc
    return {'source': text, 'normalized': normalized, 'sentences': sentences, 'word_tokens': tokens,
        'filtered_tokens': filtered, 'tokens': transformed, 'backend': 'Hazm' if language == 'fa' else 'NLTK',
        'morph_method': morph_method, 'note': 'Punctuation-only tokens are filtered. Negation protection uses a finite list.'}
