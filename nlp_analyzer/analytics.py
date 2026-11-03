"""Morphology, lexical statistics and small corpus experiments."""
from collections import Counter
from functools import lru_cache
import math
from pathlib import Path
from .core import tokenize_words


def words(text):
    return [word.casefold() for word in tokenize_words(text, include_numbers=True)]


@lru_cache(maxsize=1)
def hazm_morphology():
    from hazm import Stemmer, Lemmatizer
    return Stemmer(), Lemmatizer()


def morphology(text, language='fa', method='stem', remove_stopwords=False, pos='n'):
    tokens = words(text)
    if language == 'fa':
        from hazm import stopwords_list
        stops = set(stopwords_list())
        stemmer, lemmatizer = hazm_morphology()
        transform = stemmer.stem if method == 'stem' else lemmatizer.lemmatize
    elif language == 'en':
        import nltk
        data_dir = Path(__file__).resolve().parents[1] / '.nlp_data'
        if str(data_dir) not in nltk.data.path: nltk.data.path.insert(0, str(data_dir))
        # A standard library-provided list; no stopword corpus download is needed.
        from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
        from nltk.stem import PorterStemmer, WordNetLemmatizer
        stops = set(ENGLISH_STOP_WORDS)
        if method == 'stem': transform = PorterStemmer().stem
        else:
            if pos not in ('n', 'v', 'a', 'r', 's'): raise ValueError('Invalid WordNet POS.')
            transform = lambda token: WordNetLemmatizer().lemmatize(token, pos=pos)
    else: raise ValueError('Morphology supports fa or en.')
    if method not in ('stem', 'lemma'): raise ValueError('Choose stem or lemma.')
    rows = []
    try:
        for token in tokens:
            removed = remove_stopwords and token in stops
            rows.append({'token': token, 'removed_stopword': removed,
                         'result': None if removed else transform(token)})
    except LookupError as exc:
        raise ValueError('English lemmatization needs local WordNet data. Run: python setup_resources.py') from exc
    return {'language': language, 'method': method, 'rows': rows,
            'tokens': [row['result'] for row in rows if row['result'] is not None],
            'note': 'Stems may not be valid words. Lemmatization is not contextual disambiguation. English POS is explicit.'}


def corpus_features(documents, ngram=1):
    if not documents or not all(isinstance(x, str) for x in documents): raise ValueError('Supply a nonempty text corpus.')
    if not 1 <= ngram <= 5: raise ValueError('ngram must be between 1 and 5.')
    docs = [words(text) for text in documents]
    terms = [[tuple(tokens[i:i + ngram]) for i in range(len(tokens) - ngram + 1)] for tokens in docs]
    vocabulary = sorted(set(term for row in terms for term in row))
    counts = [Counter(row) for row in terms]
    bow = [[row[term] for term in vocabulary] for row in counts]
    dfs = [sum(row[term] > 0 for row in counts) for term in vocabulary]
    idf = [math.log((1 + len(documents)) / (1 + df)) + 1 for df in dfs]
    tfidf = []
    for row in bow:
        weighted = [freq * weight for freq, weight in zip(row, idf)]
        norm = math.sqrt(sum(v * v for v in weighted))
        tfidf.append([v / norm if norm else 0.0 for v in weighted])
    similarities = [[sum(a * b for a, b in zip(left, right)) for right in tfidf] for left in tfidf]
    combined = Counter(t for row in docs for t in row)
    total = sum(combined.values())
    zipf = [{'rank': i, 'word': word, 'frequency': frequency, 'relative_frequency': frequency / total,
             'rank_times_frequency': i * frequency} for i, (word, frequency) in enumerate(combined.most_common(), 1)]
    return {'documents': documents, 'ngram': ngram, 'vocabulary': [' '.join(term) for term in vocabulary],
            'bow': bow, 'document_frequency': dfs, 'idf': idf, 'tfidf': tfidf, 'cosine_similarity': similarities,
            'token_count': total, 'type_count': len(combined), 'type_token_ratio': len(combined) / total if total else 0.0,
            'zipf': zipf, 'formula': 'idf = ln((1 + N)/(1 + df)) + 1; raw count TF; row-wise L2 normalization',
            'note': 'Zipf rows are measured counts, not proof of a power law. Vocabulary and IDF are fit on this supplied corpus.'}


def classify(training_records, query, evaluation_records=None):
    """Train TF-IDF + Multinomial NB on explicit labels; evaluate only held-out data."""
    from sklearn.pipeline import make_pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
    if len(training_records) < 2 or len({r['label'] for r in training_records}) < 2:
        raise ValueError('Training needs at least two labels and two records.')
    texts = [str(r['text']) for r in training_records]
    labels = [str(r['label']) for r in training_records]
    pipeline = make_pipeline(TfidfVectorizer(tokenizer=words, token_pattern=None, lowercase=False), MultinomialNB())
    pipeline.fit(texts, labels)
    prediction = str(pipeline.predict([query])[0])
    result = {'prediction': prediction, 'training_rows': len(texts), 'classes': list(pipeline.classes_),
              'probabilities': dict(zip(map(str, pipeline.classes_), map(float, pipeline.predict_proba([query])[0]))),
              'model': 'TF-IDF + Multinomial Naive Bayes', 'evaluation': None}
    if evaluation_records:
        train_keys = {' '.join(words(t)) for t in texts}
        test_texts = [str(r['text']) for r in evaluation_records]
        if any(' '.join(words(t)) in train_keys for t in test_texts):
            raise ValueError('Evaluation contains a normalized exact duplicate of training text. Remove leakage.')
        actual = [str(r['label']) for r in evaluation_records]
        predicted = pipeline.predict(test_texts)
        classes = sorted(set(labels + actual + list(predicted)))
        result['evaluation'] = {'rows': len(actual), 'accuracy': float(accuracy_score(actual, predicted)),
            'class_order': classes, 'confusion_matrix': confusion_matrix(actual, predicted, labels=classes).tolist(),
            'report': classification_report(actual, predicted, labels=classes, output_dict=True, zero_division=0),
            'note': 'These scores apply only to the supplied holdout. No dataset-wide performance claim.'}
    return result
