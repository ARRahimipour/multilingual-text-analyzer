"""Real tokenizer comparisons, locally trained subword models and model inputs."""
from collections import Counter
from functools import lru_cache
import io
import re
from pathlib import Path
import time
import tracemalloc
from .core import tokenize_words, split_sentences

BASIC_METHODS = ('whitespace', 'regex', 'word', 'character', 'grapheme', 'nltk', 'treebank', 'hazm')
SUBWORD_METHODS = ('bpe', 'wordpiece', 'unigram', 'sentencepiece')
SPECIAL = ['[UNK]', '[PAD]', '[CLS]', '[SEP]']


@lru_cache(maxsize=1)
def hazm_tokenizer():
    from hazm import WordTokenizer
    return WordTokenizer()


def tokenize(text, method='word'):
    if method == 'whitespace': return text.split()
    if method == 'regex': return re.findall(r'\w+|[^\w\s]', text)
    if method == 'word': return tokenize_words(text, include_numbers=True)
    if method == 'character': return list(text)
    if method == 'grapheme':
        import regex
        return regex.findall(r'\X', text)
    if method == 'nltk':
        from nltk.tokenize import wordpunct_tokenize
        return wordpunct_tokenize(text)
    if method == 'treebank':
        from nltk.tokenize import TreebankWordTokenizer
        return TreebankWordTokenizer().tokenize(text)
    if method == 'hazm': return hazm_tokenizer().tokenize(text)
    raise ValueError('Unknown basic tokenizer: ' + method)


def compare_tokenizers(text, methods=BASIC_METHODS):
    results = []
    for method in methods:
        try:
            tokens = tokenize(text, method)  # Warm import/setup before timing.
            tracemalloc.start()
            start = time.perf_counter()
            tokens = tokenize(text, method)
            elapsed = time.perf_counter() - start
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            results.append({'method': method, 'tokens': tokens, 'count': len(tokens),
                            'elapsed_ms': elapsed * 1000, 'python_peak_bytes': peak})
        except (ImportError, LookupError) as exc:
            if tracemalloc.is_tracing(): tracemalloc.stop()
            results.append({'method': method, 'error': str(exc), 'available': False})
    return {'comparisons': results,
            'measurement_note': 'One warm in-process run; timings vary. tracemalloc measures Python allocations, not native library memory or total process RAM.'}


class SubwordModel:
    def __init__(self, engine, model):
        self.engine, self.model = engine, model

    @classmethod
    def train(cls, corpus, method='bpe', vocab_size=300):
        if method not in SUBWORD_METHODS: raise ValueError('Unknown subword algorithm.')
        if isinstance(vocab_size, bool) or not isinstance(vocab_size, int) or vocab_size < 8:
            raise ValueError('Vocabulary size must be an integer >= 8.')
        texts = [s for s in corpus if isinstance(s, str) and s.strip()]
        if not texts: raise ValueError('Training corpus is empty.')
        if method == 'sentencepiece':
            import sentencepiece as spm
            stream = io.BytesIO()
            alphabet_size = len(set(''.join(texts)))
            spm.SentencePieceTrainer.train(sentence_iterator=iter(texts), model_writer=stream,
                model_type='unigram', vocab_size=max(vocab_size, alphabet_size + 8),
                hard_vocab_limit=False, character_coverage=1.0, shuffle_input_sentence=False,
                num_threads=1, minloglevel=2, unk_id=0, pad_id=1, bos_id=2, eos_id=3)
            return cls(method, spm.SentencePieceProcessor(model_proto=stream.getvalue()))
        from tokenizers import Tokenizer, models, trainers, pre_tokenizers, normalizers, decoders
        if method == 'bpe':
            model = Tokenizer(models.BPE(unk_token='[UNK]'))
            model.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
            model.decoder = decoders.ByteLevel()
            trainer = trainers.BpeTrainer(vocab_size=max(vocab_size, 260), special_tokens=SPECIAL,
                initial_alphabet=pre_tokenizers.ByteLevel.alphabet(), show_progress=False)
        elif method == 'wordpiece':
            model = Tokenizer(models.WordPiece(unk_token='[UNK]'))
            model.pre_tokenizer = pre_tokenizers.BertPreTokenizer()
            model.decoder = decoders.WordPiece(prefix='##')
            trainer = trainers.WordPieceTrainer(vocab_size=max(vocab_size, len(set(''.join(texts))) * 2 + 8),
                                               special_tokens=SPECIAL, show_progress=False)
        else:
            model = Tokenizer(models.Unigram())
            model.pre_tokenizer = pre_tokenizers.Metaspace(replacement='▁', prepend_scheme='always')
            model.decoder = decoders.Metaspace(replacement='▁', prepend_scheme='always')
            trainer = trainers.UnigramTrainer(vocab_size=max(vocab_size, len(set(''.join(texts))) + 8),
                                              special_tokens=SPECIAL, unk_token='[UNK]', show_progress=False)
        model.normalizer = normalizers.NFKC()
        model.train_from_iterator(texts, trainer=trainer)
        return cls(method, model)

    def encode(self, text):
        if self.engine == 'sentencepiece':
            ids = self.model.encode(text, out_type=int)
            pieces = self.model.encode(text, out_type=str)
            return {'tokens': pieces, 'ids': ids, 'count': len(ids),
                    'unknown_count': ids.count(self.model.unk_id()), 'decoded': self.model.decode(ids)}
        encoding = self.model.encode(text)
        unknown = self.model.token_to_id('[UNK]')
        return {'tokens': encoding.tokens, 'ids': encoding.ids, 'offsets': encoding.offsets,
                'count': len(encoding.ids), 'unknown_count': encoding.ids.count(unknown),
                'decoded': self.model.decode(encoding.ids, skip_special_tokens=False)}

    @property
    def vocabulary_size(self):
        return self.model.get_piece_size() if self.engine == 'sentencepiece' else self.model.get_vocab_size()

    @property
    def pad_id(self):
        return self.model.pad_id() if self.engine == 'sentencepiece' else self.model.token_to_id('[PAD]')

    def save(self, path):
        path = Path(path)
        expected = '.model' if self.engine == 'sentencepiece' else '.json'
        if path.suffix != expected: raise ValueError('Save this tokenizer with the ' + expected + ' extension.')
        path.parent.mkdir(parents=True, exist_ok=True)
        if self.engine == 'sentencepiece': path.write_bytes(self.model.serialized_model_proto())
        else: self.model.save(str(path))

    @classmethod
    def load(cls, path):
        path = Path(path)
        if path.suffix == '.model':
            import sentencepiece as spm
            return cls('sentencepiece', spm.SentencePieceProcessor(model_proto=path.read_bytes()))
        from tokenizers import Tokenizer
        import json
        info = json.loads(path.read_text(encoding='utf-8'))
        kind = info.get('model', {}).get('type', '').lower()
        if kind not in SUBWORD_METHODS: raise ValueError('Unsupported tokenizer model type.')
        return cls(kind, Tokenizer.from_file(str(path)))


def vocabulary_encode(training_texts, text, max_size=1000):
    if max_size < 1: raise ValueError('max_size must be positive.')
    counts = Counter(t for s in training_texts for t in tokenize(s))
    vocabulary = {word: i + 2 for i, (word, _) in enumerate(counts.most_common(max_size))}
    vocabulary.update({'[PAD]': 0, '[UNK]': 1})
    tokens = tokenize(text); ids = [vocabulary.get(t, 1) for t in tokens]
    return {'vocabulary': vocabulary, 'tokens': tokens, 'ids': ids,
            'unknown_tokens': [t for t, i in zip(tokens, ids) if i == 1],
            'unknown_rate': sum(i == 1 for i in ids) / len(ids) if ids else 0.0}


def prepare_batch(sequences, max_length=32, pad_id=0, truncation=True, side='right'):
    if max_length < 1 or side not in ('left', 'right'): raise ValueError('Invalid batch settings.')
    result = {'input_ids': [], 'attention_mask': [], 'original_lengths': [], 'truncated_counts': []}
    for sequence in sequences:
        seq = list(sequence)
        if len(seq) > max_length and not truncation:
            raise ValueError('Sequence exceeds max_length and truncation is disabled.')
        values = seq[:max_length] if side == 'right' else seq[-max_length:]
        padding = [pad_id] * (max_length - len(values))
        mask = [1] * len(values)
        result['input_ids'].append(values + padding if side == 'right' else padding + values)
        result['attention_mask'].append(mask + [0] * len(padding) if side == 'right' else [0] * len(padding) + mask)
        result['original_lengths'].append(len(seq)); result['truncated_counts'].append(max(0, len(seq) - max_length))
    return result


def chunk_text(text, max_tokens=128, overlap=16, encoder=None):
    """Pack complete sentences; split overlong sentences only at word boundaries.

    Overlap uses complete trailing units and is at most the requested budget.
    An indivisible word over budget raises a clear error instead of silent loss.
    Counts come from the supplied model encoder when available.
    """
    if max_tokens < 1 or not 0 <= overlap < max_tokens:
        raise ValueError('Require max_tokens > 0 and 0 <= overlap < max_tokens.')
    count = (lambda s: encoder.encode(s)['count']) if encoder else (lambda s: len(tokenize(s)))
    units, warnings = [], []
    for sentence in split_sentences(text):
        if count(sentence) <= max_tokens:
            units.append(sentence); continue
        warnings.append('An overlong sentence was split at whitespace word boundaries.')
        fragment = ''
        for word in sentence.split():
            if count(word) > max_tokens:
                raise ValueError('One indivisible word exceeds the token budget; increase max_tokens.')
            candidate = (fragment + ' ' + word).strip()
            if count(candidate) > max_tokens:
                if fragment: units.append(fragment)
                fragment = word
            else: fragment = candidate
        if fragment: units.append(fragment)
    chunks, start = [], 0
    while start < len(units):
        end = start
        while end < len(units) and count(' '.join(units[start:end + 1])) <= max_tokens: end += 1
        if end == start: raise ValueError('Cannot pack a unit within the requested token budget.')
        value = ' '.join(units[start:end])
        chunks.append({'text': value, 'token_count': count(value), 'unit_start': start, 'unit_end': end})
        if end == len(units): break
        new_start = end
        while new_start > start + 1 and count(' '.join(units[new_start - 1:end])) <= overlap:
            new_start -= 1
        # Drop overlap if it leaves no room for the next new unit.
        while new_start < end and count(' '.join(units[new_start:end + 1])) > max_tokens: new_start += 1
        start = new_start
    return {'chunks': chunks, 'units': units, 'warnings': list(dict.fromkeys(warnings)),
            'max_tokens': max_tokens, 'requested_overlap': overlap,
            'counting': encoder.engine if encoder else 'Unicode word tokens'}
