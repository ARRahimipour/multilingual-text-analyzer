"""Auditable, task-dependent text cleaning for the session-two material.

This module is deliberately standard-library-only.  Cleaning is opt-in so
the original assignment's counts remain reproducible.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from html.parser import HTMLParser
import html
import re
import unicodedata


INVISIBLE = re.compile(r'[\u200b\u200e\u200f\u202a-\u202e\u2060\u00ad\ufeff]')
CONTROL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
URL = re.compile(r'(?i)\b(?:https?://|www\.)[^\s<>"\']+')
EMAIL = re.compile(r'(?i)(?<![\w.+-])[\w.+-]+@[\w.-]+\.[a-z]{2,}(?!\w)')
MENTION = re.compile(r'(?<!\w)@[\w\u200c]+')
HASHTAG = re.compile(r'(?<!\w)#(?=[\w\u200c])')
PHONE = re.compile(r'(?<!\w)(?:(?:\+|00)98|0)?9\d{9}(?!\w)')
NATIONAL_ID = re.compile(r'(?<!\w)\d{10}(?!\w)')
NUMBER = re.compile(r'\d+(?:[.,٫٬]\d+)*')
REPEATED_PUNCT = re.compile(r'([!?؟,،؛;])\1{1,}')
ELONGATION = re.compile(r'([^\W\d_])\1{2,}', flags=re.UNICODE)
RETWEET = re.compile(r'(?i)(?<!\w)RT\s+(?=@\w+)')
ARABIC_MARKS = re.compile(r'[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]')
EMOJI_BASE = r'[\U0001f000-\U0001faff\u2600-\u27bf\u00a9\u00ae\u203c\u2049\u2122\u2139]'
EMOJI_UNIT = EMOJI_BASE + r'[\ufe0e\ufe0f\U0001f3fb-\U0001f3ff]*'
EMOJI = re.compile(r'(?:[\U0001f1e6-\U0001f1ff]{2}|[0-9#*]\ufe0f?\u20e3|'
                   + EMOJI_UNIT + r'(?:\u200d' + EMOJI_UNIT + r')*)')
PERSIAN_LETTERS = str.maketrans({'ي': 'ی', 'ى': 'ی', 'ك': 'ک', 'ـ': ''})
ASCII_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹', '01234567890123456789')
PERSIAN_DIGITS = str.maketrans('0123456789٠١٢٣٤٥٦٧٨٩', '۰۱۲۳۴۵۶۷۸۹۰۱۲۳۴۵۶۷۸۹')
QUOTES = str.maketrans({'«': '"', '»': '"', '“': '"', '”': '"', '„': '"', '‘': "'", '’': "'"})
PRESET_NAMES = ('general', 'sentiment', 'topic', 'ner', 'transformer', 'spam')


@dataclass(frozen=True)
class PreprocessOptions:
    unicode_form: str = 'NFKC'
    normalize_persian: bool = True
    digit_style: str = 'keep'  # keep | ascii | persian
    remove_diacritics: bool = False
    invisible_mode: str = 'safe'  # none | safe | controls
    remove_html: bool = True
    remove_urls: bool = True
    url_replacement: str = ''  # '' or '<URL>'
    remove_emails: bool = True
    remove_mentions: bool = True
    remove_retweet_marker: bool = False
    strip_hashtags: bool = True
    emoji_mode: str = 'keep'  # keep | remove | label
    punctuation_mode: str = 'normalize'  # keep | normalize | remove
    collapse_repeated_punctuation: bool = False
    reduce_elongations: bool = False
    number_mode: str = 'keep'  # keep | remove | placeholder
    mask_pii: bool = False
    join_broken_lines: bool = False
    collapse_whitespace: bool = True

    def __post_init__(self):
        choices = {'unicode_form': {'NFC', 'NFKC'}, 'digit_style': {'keep', 'ascii', 'persian'},
                   'invisible_mode': {'none', 'safe', 'controls'},
                   'emoji_mode': {'keep', 'remove', 'label'},
                   'punctuation_mode': {'keep', 'normalize', 'remove'},
                   'number_mode': {'keep', 'remove', 'placeholder'},
                   'url_replacement': {'', '<URL>'}}
        for name, allowed in choices.items():
            if getattr(self, name) not in allowed:
                raise ValueError(f'{name} must be one of {sorted(allowed)}')


def preset(name: str) -> PreprocessOptions:
    """Suggested defaults, not universal rules; callers may use replace(...)."""
    if name not in PRESET_NAMES:
        raise ValueError(f'Unknown cleaning preset: {name}')
    base = PreprocessOptions()
    if name == 'sentiment':
        return replace(base, emoji_mode='keep', punctuation_mode='keep',
                       number_mode='placeholder', collapse_repeated_punctuation=False)
    if name == 'topic':
        return replace(base, emoji_mode='remove', punctuation_mode='remove', number_mode='remove',
                       reduce_elongations=True, remove_retweet_marker=True)
    if name == 'ner':
        return replace(base, remove_urls=False, remove_emails=False, remove_mentions=False,
                       emoji_mode='remove', punctuation_mode='keep', number_mode='keep')
    if name == 'transformer':
        return replace(base, remove_urls=False, remove_emails=False, remove_mentions=False,
                       strip_hashtags=False, emoji_mode='keep', punctuation_mode='keep')
    if name == 'spam':
        return replace(base, remove_urls=True, url_replacement='<URL>',
                       remove_emails=False, remove_mentions=False, strip_hashtags=False,
                       emoji_mode='keep', punctuation_mode='keep', number_mode='keep')
    return replace(base, emoji_mode='remove', reduce_elongations=True, remove_retweet_marker=True)


class _TextFromHTML(HTMLParser):
    """Ignore scripts/styles; replace tags with boundaries, decode entities."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript'):
            self.hidden += 1
        self.chunks.append(' ')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript') and self.hidden:
            self.hidden -= 1
        self.chunks.append(' ')

    def handle_data(self, data):
        if not self.hidden:
            self.chunks.append(data)


def _strip_html(text):
    parser = _TextFromHTML()
    parser.feed(text)
    parser.close()
    return html.unescape(''.join(parser.chunks))


def _emoji_label(match):
    names = [unicodedata.name(char, '') for char in match.group()
             if char not in ('\u200d', '\ufe0f', '\ufe0e') and not unicodedata.category(char).startswith('M')]
    return ':' + '_'.join('_'.join(name.lower().split()) for name in names if name) + ':' if names else ''


def _strip_punctuation(text):
    return ''.join(' ' if unicodedata.category(char).startswith('P') else char for char in text)


@dataclass(frozen=True)
class CleaningResult:
    text: str
    sentence_text: str  # Snapshot before potentially destructive punctuation removal
    statistics: dict


def clean_text(source: str, options: PreprocessOptions | None = None) -> CleaningResult:
    """Return cleaned copy and per-stage measurements; never mutate source."""
    if not isinstance(source, str):
        raise TypeError('text must be a string.')
    options = options or PreprocessOptions()
    text = source
    stages = {}

    def step(name, operation):
        nonlocal text
        before = text
        text = operation(text)
        stages[name] = {'changed': text != before, 'characters_before': len(before),
                        'characters_after': len(text)}

    step('unicode', lambda t: unicodedata.normalize(options.unicode_form, t)
         .replace('\r\n', '\n').replace('\r', '\n'))
    if options.remove_html:
        step('html', _strip_html)
    if options.invisible_mode != 'none':
        step('invisible', lambda t: INVISIBLE.sub('', t) if options.invisible_mode == 'safe'
             else CONTROL.sub('', INVISIBLE.sub('', t)))
    if options.normalize_persian:
        step('persian_letters', lambda t: t.translate(PERSIAN_LETTERS))
    if options.remove_diacritics:
        step('arabic_diacritics', lambda t: ARABIC_MARKS.sub('', t))
    if options.digit_style != 'keep':
        translation = ASCII_DIGITS if options.digit_style == 'ascii' else PERSIAN_DIGITS
        step('digits', lambda t: t.translate(translation))
    if options.join_broken_lines:
        step('broken_lines', lambda t: re.sub(r'(?<=\w)-\s*\n\s*(?=\w)', '', t))
    if options.mask_pii:
        def hide_pii(t):
            t = EMAIL.sub('<EMAIL>', t)
            # Match on an equal-length ASCII-digit shadow, while leaving all
            # non-sensitive original script and spelling untouched.
            numeric_shadow = t.translate(ASCII_DIGITS)
            spans = [(m.start(), m.end(), '<PHONE>') for m in PHONE.finditer(numeric_shadow)]
            spans += [(m.start(), m.end(), '<NATIONAL_ID>') for m in NATIONAL_ID.finditer(numeric_shadow)
                      if not any(m.start() < right and m.end() > left for left, right, _ in spans)]
            for left, right, label in sorted(spans, reverse=True):
                t = t[:left] + label + t[right:]
            return t
        step('pii', hide_pii)
    if options.remove_urls:
        def drop_url(match):
            # The trailing full stop belongs to the sentence, not the URL.
            value = match.group()
            trailing = value[len(value.rstrip('.,!?؟…')):]
            return (options.url_replacement or ' ') + trailing
        step('urls', lambda t: URL.sub(drop_url, t))
    if options.remove_emails and not options.mask_pii:
        step('emails', lambda t: EMAIL.sub(' ', t))
    if options.remove_retweet_marker:
        step('retweets', lambda t: RETWEET.sub('', t))
    if options.remove_mentions:
        step('mentions', lambda t: MENTION.sub(' ', t))
    if options.strip_hashtags:
        step('hashtags', lambda t: HASHTAG.sub('', t))
    if options.emoji_mode != 'keep':
        step('emoji', lambda t: EMOJI.sub(' ' if options.emoji_mode == 'remove' else _emoji_label, t))
    if options.reduce_elongations:
        step('elongations', lambda t: ELONGATION.sub(r'\1', t))
    # Remove/replace numbers only after PII, URLs and sentence punctuation were inspected.
    if options.number_mode != 'keep':
        step('numbers', lambda t: NUMBER.sub(' ' if options.number_mode == 'remove' else '<NUM>', t))
    # Sentence segmentation must happen before deleting '.', '!', '?' or '؟'.
    sentence_text = re.sub(r'\s+', ' ', text).strip() if options.collapse_whitespace else text.strip()
    if options.punctuation_mode == 'normalize':
        step('punctuation', lambda t: t.translate(QUOTES).replace('…', '...'))
    elif options.punctuation_mode == 'remove':
        step('punctuation', _strip_punctuation)
    if options.collapse_repeated_punctuation and options.punctuation_mode != 'remove':
        step('repeated_punctuation', lambda t: re.sub(r'\.{4,}', '...', REPEATED_PUNCT.sub(r'\1', t)))
    if options.collapse_whitespace:
        step('whitespace', lambda t: re.sub(r'\s+', ' ', t).strip())
    else:
        step('whitespace', lambda t: t.strip())
    stats = {'characters_before': len(source), 'characters_after': len(text),
             'utf8_bytes_before': len(source.encode('utf-8')),
             'utf8_bytes_after': len(text.encode('utf-8')),
             'changed_stages': stages, 'options': asdict(options)}
    return CleaningResult(text=text, sentence_text=sentence_text, statistics=stats)


def persian_script_ratio(text: str) -> float:
    """Lightweight script ratio; it is NOT a Persian language classifier."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum('\u0600' <= c <= '\u06ff' or '\u0750' <= c <= '\u077f'
               or '\u08a0' <= c <= '\u08ff' for c in letters) / len(letters)
