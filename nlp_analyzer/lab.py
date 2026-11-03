"""One reproducible interface to the four-handout learning activities."""
from dataclasses import asdict
import json
from pathlib import Path
from .normalization import NormalizationOptions, normalization_audit, unicode_inspect
from .tokenization import (compare_tokenizers, tokenize, SubwordModel, vocabulary_encode, prepare_batch, chunk_text)
from .analytics import morphology, corpus_features, classify

OPERATIONS = ('normalize', 'unicode', 'compare', 'subword', 'oov', 'batch', 'chunk', 'morphology', 'features', 'classify')


def run_lab(operation, text, corpus=None, **settings):
    corpus = corpus if corpus is not None else [text]
    if operation == 'normalize':
        config = settings.get('normalization', {})
        return normalization_audit(text, NormalizationOptions(**config), settings.get('lexical_map'))
    if operation == 'unicode': return unicode_inspect(text)
    if operation == 'compare': return compare_tokenizers(text, settings.get('methods', ('whitespace', 'regex', 'word', 'character', 'grapheme', 'nltk', 'treebank', 'hazm')))
    if operation in ('subword', 'batch', 'chunk'):
        model = None
        model_file = settings.get('model_file')
        method = settings.get('method', 'bpe')
        if model_file: model = SubwordModel.load(model_file)
        elif operation == 'subword' or settings.get('use_subword', False):
            model = SubwordModel.train(corpus, method, int(settings.get('vocab_size', 300)))
        if operation == 'subword':
            result = model.encode(text)
            result.update({'algorithm': model.engine, 'actual_vocabulary_size': model.vocabulary_size,
                           'training_documents': len(corpus), 'training_source': 'saved model' if model_file else 'supplied corpus',
                           'note': 'Local educational tokenizer, not a pretrained BERT/GPT tokenizer. Byte-level BPE reserves all 256 bytes. Requested vocabulary is a target, not a guarantee.'})
            if settings.get('save_model'): model.save(settings['save_model'])
            return result
        if operation == 'chunk':
            return chunk_text(text, int(settings.get('max_length', 128)), int(settings.get('overlap', 16)), model)
        if model:
            sequences = [model.encode(doc)['ids'] for doc in corpus]; pad_id = model.pad_id
            vocabulary = None
        else:
            encoded = vocabulary_encode(corpus, text)
            vocabulary = encoded['vocabulary']; pad_id = 0
            sequences = [[vocabulary.get(word, 1) for word in tokenize(doc)] for doc in corpus]
        result = prepare_batch(sequences, int(settings.get('max_length', 32)), pad_id,
                               settings.get('truncation', True), settings.get('side', 'right'))
        result.update({'documents': corpus, 'vocabulary': vocabulary, 'tokenizer': model.engine if model else 'word vocabulary',
                       'special_tokens_note': 'No model-specific BOS/EOS/CLS/SEP are inserted. The budget covers encoded content only.'})
        return result
    if operation == 'oov': return vocabulary_encode(corpus, text, int(settings.get('vocab_size', 1000)))
    if operation == 'morphology':
        return morphology(text, settings.get('language', 'fa'), settings.get('morph_method', 'stem'),
                          settings.get('stopwords', False), settings.get('pos', 'n'))
    if operation == 'features': return corpus_features(corpus, int(settings.get('ngram', 1)))
    if operation == 'classify': return classify(settings.get('training_records', []), text, settings.get('evaluation_records'))
    raise ValueError('Unknown lab operation: ' + operation)


def save_lab_report(result, path):
    """UTF-8 JSON makes every token, option and measurement inspectable."""
    destination = Path(path); destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
