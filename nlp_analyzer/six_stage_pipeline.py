"""Inspectable six-step pipeline from the course handout (PDF pages 27, 29-49, 50-99).

Stages are *not* aliases: the original, cleaning, normalization, word/sentence
segmentation, optional stopword filtering, and one morphology method each have
an independently exportable snapshot.  Destructive choices are task-dependent.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, replace
import re

from .core import split_sentences, tokenize_words
from .normalization import NormalizationOptions, normalize
from .preprocessing import PreprocessOptions, clean_text, preset, PRESET_NAMES
from .spacing_inspection import spacing_counts


NAMES = (
    ('raw', '1. Raw Text', 'Raw Text'),
    ('cleaning', '2. Cleaning', 'Cleaning'),
    ('normalization', '3. Normalization', 'Normalization'),
    ('tokenization', '4. Tokenization', 'Tokenization'),
    ('stopwords', '5. Stopwords', 'Stopwords'),
    ('morphology', '6. Stemming / Lemmatization', 'Stemming / Lemmatization'),
)
SPECIAL = re.compile(r'(<(?:NUM|URL|EMAIL|USER|PHONE|NATIONAL_ID)>)')


def _options(cls, values, defaults):
    if values is None:
        return defaults
    if not isinstance(values, dict):
        raise ValueError('Stage options must be a JSON object.')
    invalid = set(values) - set(asdict(defaults))
    if invalid:
        raise ValueError('Unknown stage options: ' + ', '.join(sorted(invalid)))
    return cls(**(asdict(defaults) | values))


def _tokens_regex(text):
    # Core tokenizer preserves Persian ZWNJ, marks and contractions. Preserve
    # explicit placeholders as whole units instead of treating <NUM> as NUM.
    chunks = SPECIAL.split(text)
    out = []
    for chunk in chunks:
        if not chunk:
            continue
        if SPECIAL.fullmatch(chunk):
            out.append(chunk)
        else:
            out.extend(tokenize_words(chunk, include_numbers=True))
    return out


def _tokenize(text, sentence_text, language, method):
    if method == 'auto':
        method = 'hazm' if language == 'fa' else 'nltk'
    if method == 'regex':
        return split_sentences(sentence_text), _tokens_regex(text), method
    if method == 'hazm':
        if language != 'fa':
            raise ValueError('Hazm is the Persian tokenizer; choose nltk or regex for English.')
        try:
            from hazm import sent_tokenize, word_tokenize
        except ImportError as exc:
            raise ValueError('Persian Hazm is missing. Install requirements-nlp.txt or choose tokenizer="regex".') from exc
        return sent_tokenize(sentence_text), word_tokenize(text), method
    if method == 'nltk':
        if language != 'en':
            raise ValueError('NLTK tokenizer is recommended for English; choose hazm or regex for Persian.')
        import nltk
        from pathlib import Path
        data_dir = str(Path(__file__).resolve().parents[1] / '.nlp_data')
        if data_dir not in nltk.data.path:
            nltk.data.path.insert(0, data_dir)
        try:
            return nltk.sent_tokenize(sentence_text), nltk.word_tokenize(text), method
        except LookupError as exc:
            raise ValueError('NLTK punkt_tab not installed. Run: python setup_resources.py --resources punkt_tab or select tokenizer="regex".') from exc
    raise ValueError('tokenizer must be auto, regex, hazm or nltk.')


def _statistics(tokens):
    count = Counter(tokens)
    size = len(tokens)
    return {
        'token_count': size,
        'type_count': len(count),
        'type_token_ratio': len(count)/size if size else 0,
        'singleton_count': sum(1 for n in count.values() if n == 1),
        'top_10': [{'word': word, 'count': n} for word, n in count.most_common(10)],
    }


def _morph(tokens, language, method, stemmer, pos, protected):
    if method == 'none':
        return list(tokens), [{'token': token, 'result': token, 'protected': True} for token in tokens], 'disabled'
    if method not in ('stem', 'lemma'):
        raise ValueError('morph_method must be stem, lemma or none. Never apply both in sequence.')
    if language == 'fa':
        try:
            from hazm import Stemmer, Lemmatizer
        except ImportError as exc:
            raise ValueError('Persian stemming/lemmatization needs Hazm. Install requirements-nlp.txt or set morph_method="none".') from exc
        model = Stemmer() if method == 'stem' else Lemmatizer()
        transform = model.stem if method == 'stem' else model.lemmatize
        engine = 'Hazm ' + ('Stemmer' if method == 'stem' else 'Lemmatizer')
    elif language == 'en':
        from nltk.stem import PorterStemmer, SnowballStemmer, LancasterStemmer, WordNetLemmatizer
        if method == 'stem':
            choices = {'porter': PorterStemmer, 'snowball': lambda: SnowballStemmer('english'),
                       'lancaster': LancasterStemmer}
            if stemmer not in choices:
                raise ValueError('Choose porter, snowball or lancaster as stemmer.')
            transform = choices[stemmer]().stem
            engine = 'NLTK ' + stemmer
        else:
            if pos not in ('n', 'v', 'a', 'r', 's'):
                raise ValueError('English WordNet POS must be n, v, a, r or s.')
            from pathlib import Path
            import nltk
            local = str(Path(__file__).resolve().parents[1] / '.nlp_data')
            if local not in nltk.data.path:
                nltk.data.path.insert(0, local)
            model = WordNetLemmatizer()
            transform = lambda token: model.lemmatize(token, pos=pos)
            engine = 'NLTK WordNet (POS=' + pos + ')'
    else:
        raise ValueError('Choose language fa or en.')
    result, mapping = [], []
    for token in tokens:
        # Do not stem numbers, explicit placeholders or named domain terms.
        skip = token.casefold() in protected or (token.startswith('<') and token.endswith('>')) or not any(c.isalpha() for c in token)
        try:
            output = token if skip else transform(token)
        except LookupError as exc:
            raise ValueError('English lemmatization requires WordNet. Run: python setup_resources.py --resources wordnet') from exc
        result.append(output)
        mapping.append({'token': token, 'result': output, 'protected': skip})
    return result, mapping, engine


def run_six_stage_pipeline(text: str, corpus=None, *, language='fa', cleaning_preset='general',
                           cleaning=None, normalization=None, tokenizer='auto',
                           remove_stopwords=True, stopword_mode='dictionary',
                           custom_stopwords=None, protected_words=None, preserve_negation=True,
                           min_document_ratio=.8, max_idf=.3, min_frequency=2,
                           morph_method='stem', stemmer='porter', pos='n',
                           english_stopword_library='nltk'):
    """Run exactly six ordered steps; return untruncated snapshots and audits.

    ``cleaning`` and ``normalization`` are partial objects overriding preset
    defaults.  Sentence boundaries are captured *before* destructive punctuation
    removal, and both are normalized the same way before tokenization.
    """
    if not isinstance(text, str):
        raise TypeError('Input text must be a string.')
    if language not in ('fa', 'en'):
        raise ValueError('Choose language fa or en.')
    if cleaning_preset not in PRESET_NAMES:
        raise ValueError('Choose cleaning_preset from: ' + ', '.join(PRESET_NAMES))
    if not isinstance(remove_stopwords, bool):
        raise ValueError('remove_stopwords must be true or false.')
    if not isinstance(preserve_negation, bool):
        raise ValueError('preserve_negation must be true or false.')
    for values in (custom_stopwords, protected_words):
        if values is not None and (not isinstance(values, list) or
                                   not all(isinstance(v, str) for v in values)):
            raise ValueError('custom_stopwords and protected_words must be lists of strings.')
    if english_stopword_library not in ('nltk', 'sklearn'):
        raise ValueError('english_stopword_library must be nltk or sklearn.')
    if corpus is not None and (not isinstance(corpus, list) or not all(isinstance(t, str) for t in corpus)):
        raise ValueError('corpus must be a list of documents.')

    # Stage 2 is *cleaning* only. Let stage 3 own Persian letters, digits,
    # diacritics, case-folding, optional colloquial mapping, and spacing.
    cp = preset(cleaning_preset)
    cp = replace(cp, unicode_form='NFC', normalize_persian=False,
                 digit_style='keep', remove_diacritics=False, reduce_elongations=False)
    cp = _options(PreprocessOptions, cleaning, cp)
    cleaned = clean_text(text, cp)

    np = NormalizationOptions(persian_letters=(language == 'fa'),
                              digit_style='ascii', remove_marks=True,
                              spacing='hazm' if language == 'fa' else 'none',
                              casefold=language == 'en',
                              elongation='language-aware' if cleaning_preset in ('general', 'topic') else 'keep')
    np = _options(NormalizationOptions, normalization, np)
    normalized = normalize(cleaned.text, np)
    # clean_text stores punctuation-bearing text before optional punctuation removal.
    normalized_sentences = normalize(cleaned.sentence_text, np)['text']
    second_pass = normalize(normalized['text'], np)['text']

    sentences, token_candidates, backend = _tokenize(normalized['text'], normalized_sentences, language, tokenizer)
    # Native Hazm/NLTK output can include punctuation. Keep it in the audit,
    # but feed lexical items into the optional stopword/morphological steps.
    lexical_tokens = [tok if SPECIAL.fullmatch(tok) else tok.casefold() if np.casefold else tok for tok in token_candidates
                      if any(c.isalpha() or c.isdigit() for c in tok)]
    # Form a dictionary from the same *normalized* lexical representation as
    # text tokens (important for Arabic/Persian yeh and kaf normalization).
    from .course_extensions import NEGATIONS, stopword_set, vocabulary_statistics
    stops = set()
    removed = []
    if remove_stopwords:
        if stopword_mode not in ('dictionary', 'custom', 'statistical'):
            raise ValueError('stopword_mode must be dictionary, custom or statistical.')
        if stopword_mode == 'dictionary' and language == 'en' and english_stopword_library == 'nltk':
            # Matches the NLTK example in the PDF's English pipeline (p.99).
            import nltk
            from pathlib import Path
            local = str(Path(__file__).resolve().parents[1] / '.nlp_data')
            if local not in nltk.data.path:
                nltk.data.path.insert(0, local)
            try:
                from nltk.corpus import stopwords as nltk_stops
                dictionary_words = nltk_stops.words('english')
            except LookupError as exc:
                raise ValueError('NLTK stopwords not installed. Run: python setup_resources.py --resources stopwords or set english_stopword_library="sklearn".') from exc
            stops = stopword_set(language, list(dictionary_words) + (custom_stopwords or []),
                                 protected_words, preserve_negation, dictionary=False)
        else:
            stops = stopword_set(language, custom_stopwords, protected_words, preserve_negation,
                                 dictionary=stopword_mode == 'dictionary')
        if language == 'en' and preserve_negation:
            # NLTK word_tokenize separates a contraction into e.g. 'do', "n't".
            stops.discard("n't")
        if stopword_mode == 'statistical':
            if not corpus:
                raise ValueError('Statistical stopwords require multiple corpus documents; supply --training-corpus.')
            if not 0 <= min_document_ratio <= 1 or max_idf < 0 or min_frequency < 1:
                raise ValueError('Invalid statistical stopword thresholds.')
            stats = vocabulary_statistics(corpus, language)
            candidates = [r['word'] for r in stats if r['document_ratio'] >= min_document_ratio
                          and r['idf'] <= max_idf and r['frequency'] >= min_frequency]
            stops.update(stopword_set(language, candidates, protected_words, preserve_negation, False))
        kept = [tok for tok in lexical_tokens if tok.casefold() not in stops]
        removed = [tok for tok in lexical_tokens if tok.casefold() in stops]
    else:
        kept = list(lexical_tokens)
    # Besides the stopword list, protect explicitly named terms from morphology.
    # Normalize the protection list to avoid normal-form mismatches.
    protected = {normalize(w, np)['text'].casefold() for w in (protected_words or [])}
    protected |= {'python', 'nlp', 'bert', 'gpt'}
    result_tokens, morph_map, morph_backend = _morph(kept, language, morph_method, stemmer, pos, protected)

    stages = []
    def add(index, output, *, tokens=None, extras=None):
        key, title, english = NAMES[index]
        row = {'number': index + 1, 'stage': key, 'title': title, 'english': english,
               'output': output}
        if tokens is not None:
            row['tokens'] = list(tokens)
            row.update(_statistics(tokens))
        row.update(extras or {})
        stages.append(row)
    add(0, text, extras={'characters': len(text), 'utf8_bytes': len(text.encode('utf-8')),
                         'original_unchanged': True})
    add(1, cleaned.text, extras={'cleaning_changes': cleaned.statistics['changed_stages'],
                                  'before_characters': len(text), 'after_characters': len(cleaned.text),
                                  'sentence_boundary_snapshot': cleaned.sentence_text})
    add(2, normalized['text'], extras={'normalization_changes': normalized['stages'],
             'spacing_before': spacing_counts(cleaned.text),
             'spacing_after': spacing_counts(normalized['text']),
             'idempotent': normalized['text'] == second_pass, 'second_pass': second_pass})
    add(3, ' | '.join(lexical_tokens), tokens=lexical_tokens,
        extras={'sentences': sentences, 'sentence_count': len(sentences),
                'all_word_tokenizer_units': token_candidates, 'backend': backend})
    add(4, ' | '.join(kept), tokens=kept,
        extras={'enabled': remove_stopwords, 'mode': stopword_mode if remove_stopwords else 'off',
                'removed_tokens': removed, 'removed_count': len(removed),
                'stopwords_used': sorted(stops), 'preserve_negation': preserve_negation,
                'dictionary_backend': ('NLTK' if english_stopword_library == 'nltk' else 'scikit-learn')
                                      if language == 'en' and stopword_mode == 'dictionary' and remove_stopwords else
                                      ('Hazm' if language == 'fa' and stopword_mode == 'dictionary' and remove_stopwords else None)})
    add(5, ' | '.join(result_tokens), tokens=result_tokens,
        extras={'method': morph_method, 'backend': morph_backend,
                'mappings': morph_map, 'english_pos': pos if language == 'en' else None})
    return {'pipeline_version': 'handout-six-stages', 'language': language, 'source': text,
            'cleaning_preset': cleaning_preset, 'cleaning_options': asdict(cp),
            'normalization_options': asdict(np), 'tokenizer': backend,
            'stages': stages, 'sentences': sentences, 'tokens': result_tokens,
            'final_text': ' '.join(result_tokens), 'statistics': {
                'original_characters': len(text), 'clean_characters': len(cleaned.text),
                'normalized_characters': len(normalized['text']),
                'sentences': len(sentences),
                'words_before_stopwords': len(lexical_tokens),
                'words_after_stopwords': len(kept),
                'removed_stopwords': len(removed),
                'final_tokens': len(result_tokens),
                'final_unique_words': len(set(result_tokens)),
                'normalization_idempotent': normalized['text'] == second_pass},
            'notes': [
                'Cleaning is task-dependent: emoji/punctuation/numbers may be useful for sentiment, NER or transformers.',
                'Sentence segmentation uses a pre-punctuation-removal snapshot.',
                'Stopword removal is optional and negations are protected by a finite list.',
                'Stemming and lemmatization are alternatives, not sequential steps.',
                'English WordNet lemmatization uses the selected POS (not automatic grammatical tagging).',
                'Raw text is immutable; inspect changes before using the result to train a model.',
            ]}
