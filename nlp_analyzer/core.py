"""Deterministic Unicode text analysis using only the Python standard library."""
from collections import Counter
from dataclasses import asdict, dataclass
import re
import unicodedata

JOINERS = {"'", "\u200c", "\u200d"}
ENDINGS = set('.!?؟。！？।॥…։።')
CLOSERS = set('\"\'”’»)]}」』')
ABBREVIATIONS = {'mr', 'mrs', 'ms', 'dr', 'prof', 'sr', 'jr', 'st', 'vs', 'etc', 'e.g', 'i.e'}


@dataclass(frozen=True)
class AnalysisOptions:
    """Explicit counting rules; defaults preserve stopwords for homework."""
    top_n: int = 10
    case_sensitive: bool = False
    persian_normalization: bool = False
    include_numbers: bool = False

    def __post_init__(self):
        for name in ('top_n',):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f'{name} must be a positive integer.')


@dataclass(frozen=True)
class AnalysisResult:
    sentence_count: int
    word_count: int
    unique_word_count: int
    singleton_word_count: int
    top_words: list[dict]
    frequencies: dict[str, int]
    sentences: list[str]
    tokens: list[str]
    warnings: list[str]
    options: dict

    def to_dict(self):
        return asdict(self)


def normalize_text(text: str, persian: bool = False) -> str:
    """Normalize canonical forms without silently changing other scripts."""
    text = unicodedata.normalize('NFC', text).lstrip('\ufeff')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('\u2019', "'").replace('\u2018', "'")
    if persian:
        text = text.translate(str.maketrans({'ي': 'ی', 'ى': 'ی', 'ك': 'ک', 'ـ': ''}))
    return text


def tokenize_words(text: str, include_numbers: bool = False) -> list[str]:
    """Keep letters, attached marks, and internal apostrophes/ZWNJ/ZWJ.

    Hyphens separate words. Pure numbers are excluded unless requested.
    Unspaced scripts remain runs, not dictionary-segmented lexical words.
    """
    words, current = [], []

    def flush():
        if current:
            token = ''.join(current)
            if include_numbers or any(unicodedata.category(c).startswith('L') for c in token):
                words.append(token)
            current.clear()

    for index, char in enumerate(text):
        category = unicodedata.category(char)[0]
        if category in {'L', 'N'} or (category == 'M' and current):
            current.append(char)
        elif (char in JOINERS and current and index + 1 < len(text)
              and unicodedata.category(text[index + 1])[0] in {'L', 'N'}):
            current.append(char)
        else:
            flush()
    flush()
    return words


def _quoted_symbol_positions(text: str) -> set[int]:
    """Protect quoted punctuation examples, but not actual quoted sentences.

    A balanced quotation containing no letters or numbers denotes symbols,
    such as «؟» or "!". Its internal punctuation is not a sentence boundary.
    """
    protected = set()
    for opening, closing in [('«', '»'), ('“', '”'), ('‘', '’'),
                             ('"', '"'), ("'", "'"), ('「', '」'), ('『', '』')]:
        pattern = re.escape(opening) + '([^' + re.escape(opening + closing) + ']*)' + re.escape(closing)
        for match in re.finditer(pattern, text):
            content = match.group(1)
            if content and not any(unicodedata.category(c)[0] in {'L', 'N'} for c in content):
                protected.update(range(match.start(1), match.end(1)))
    return protected


def split_sentences(text: str) -> list[str]:
    """Split common multilingual endings; protect decimals and common titles.

    Blank lines separate paragraphs. Single line wraps do not end sentences.
    This is a documented heuristic, not a universal linguistic segmenter.
    """
    sentences = []
    for paragraph in re.split(r'\n\s*\n', text):
        start, index = 0, 0
        protected = _quoted_symbol_positions(paragraph)
        while index < len(paragraph):
            char = paragraph[index]
            if char not in ENDINGS or index in protected:
                index += 1
                continue
            if char == '.':
                before = paragraph[index - 1] if index else ''
                after = paragraph[index + 1] if index + 1 < len(paragraph) else ''
                if before.isdigit() and after.isdigit():
                    index += 1
                    continue
                # Preserve internal dots in URLs, abbreviations, and domains.
                if before.isalpha() and after.isalpha():
                    index += 1
                    continue
                match = re.search(r'([\w.]+)$', paragraph[:index])
                label = match.group(1).casefold() if match else ''
                remainder = paragraph[index + 1:].lstrip()
                if remainder and (label in ABBREVIATIONS or (len(label) == 1 and label.isalpha())):
                    index += 1
                    continue
            end = index + 1
            while end < len(paragraph) and paragraph[end] in ENDINGS | CLOSERS:
                end += 1
            candidate = paragraph[start:end].strip()
            if tokenize_words(candidate, include_numbers=True):
                sentences.append(candidate)
            start = end
            index = end
        candidate = paragraph[start:].strip()
        if tokenize_words(candidate, include_numbers=True):
            sentences.append(candidate)
    return sentences


def analyze(text: str, options: AnalysisOptions | None = None) -> AnalysisResult:
    """Compute all homework metrics with reproducible tie ordering."""
    if not isinstance(text, str):
        raise TypeError('text must be a string.')
    options = options or AnalysisOptions()
    normalized = normalize_text(text, options.persian_normalization)
    sentences = split_sentences(normalized)
    raw_tokens = tokenize_words(normalized, options.include_numbers)
    tokens = raw_tokens if options.case_sensitive else [word.casefold() for word in raw_tokens]
    counts = Counter(tokens)
    # Stable insertion order resolves ties by first appearance in the source.
    ranking = counts.most_common()
    warnings = []
    if any(('\u3400' <= c <= '\u9fff') or ('\u3040' <= c <= '\u30ff')
           or ('\u0e00' <= c <= '\u0eff') or ('\u1780' <= c <= '\u17ff')
           or ('\u1000' <= c <= '\u109f') or ('\U00020000' <= c <= '\U0003134f') for c in normalized):
        warnings.append('Unspaced-script text detected: token counts describe character runs; '
                        'accurate lexical word counts require a language-specific segmenter.')
    return AnalysisResult(
        sentence_count=len(sentences), word_count=len(tokens), unique_word_count=len(counts),
        singleton_word_count=sum(count == 1 for count in counts.values()),
        top_words=[{'word': word, 'count': count} for word, count in ranking[:options.top_n]],
        frequencies=dict(ranking), sentences=sentences, tokens=tokens,
        warnings=warnings, options=asdict(options),
    )
