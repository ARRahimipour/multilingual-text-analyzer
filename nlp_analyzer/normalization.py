"""Configurable normalization and Unicode inspection for handout three."""
from dataclasses import asdict, dataclass
from functools import lru_cache
import re
import unicodedata
from .preprocessing import ASCII_DIGITS, PERSIAN_DIGITS, PERSIAN_LETTERS, ARABIC_MARKS, INVISIBLE, URL, EMAIL, MENTION, NUMBER


@dataclass(frozen=True)
class NormalizationOptions:
    unicode_form: str = 'NFKC'
    persian_letters: bool = True
    digit_style: str = 'keep'
    remove_marks: bool = False
    arabic_variants: bool = False
    casefold: bool = False
    spacing: str = 'conservative'  # none, conservative, hazm
    elongation: str = 'keep'  # keep, language-aware
    expand_contractions: bool = False
    lexical_map: bool = False
    placeholders: bool = False

    def __post_init__(self):
        for field, choices in {'unicode_form': ('NFC', 'NFD', 'NFKC', 'NFKD'),
                               'digit_style': ('keep', 'ascii', 'persian'),
                               'spacing': ('none', 'conservative', 'hazm'),
                               'elongation': ('keep', 'language-aware')}.items():
            if getattr(self, field) not in choices:
                raise ValueError(f'Invalid {field}: {getattr(self, field)}')


@lru_cache(maxsize=1)
def hazm_normalizer():
    from hazm import Normalizer
    return Normalizer()


def normalize(source, options=None, custom_map=None):
    options = options or NormalizationOptions()
    stages = []
    text = source
    def step(name, transform):
        nonlocal text
        before = text; text = transform(text)
        stages.append({'stage': name, 'before': before, 'after': text, 'changed': before != text})
    step('Unicode ' + options.unicode_form, lambda t: unicodedata.normalize(options.unicode_form, t))
    step('Invisible controls', lambda t: INVISIBLE.sub('', t).replace('\r\n', '\n').replace('\r', '\n'))
    if options.persian_letters: step('Persian letters', lambda t: t.translate(PERSIAN_LETTERS))
    if options.arabic_variants: step('Optional Arabic variants', lambda t: t.translate(str.maketrans('ةأإٱ', 'هااا')))
    if options.remove_marks: step('Arabic diacritics', lambda t: ARABIC_MARKS.sub('', t))
    if options.digit_style != 'keep':
        step('Digits', lambda t: t.translate(ASCII_DIGITS if options.digit_style == 'ascii' else PERSIAN_DIGITS))
    if options.expand_contractions:
        def expand(t):
            t = t.replace('’', "'")
            substitutions = {"can't": 'cannot', "won't": 'will not', "shan't": 'shall not',
                             "i'm": 'I am', "let's": 'let us'}
            for old, new in substitutions.items(): t = re.sub(r'\b' + re.escape(old) + r'\b', new, t, flags=re.I)
            for old, new in [("n't", ' not'), ("'re", ' are'), ("'ve", ' have'), ("'ll", ' will')]:
                t = re.sub(re.escape(old) + r'\b', new, t, flags=re.I)
            return t  # Ambiguous 's and 'd intentionally stay unchanged.
        step('English contractions', expand)
    if options.elongation != 'keep':
        def reduce(t):
            return re.sub(r'([^\W\d_])\1{2,}', lambda m: m[1] * (2 if 'LATIN' in unicodedata.name(m[1], '') else 1), t)
        step('Repeated letters', reduce)
    if options.lexical_map or custom_map:
        lexicon = {'نمیدونم': 'نمی‌دانم', 'نمی‌دونم': 'نمی‌دانم', 'میخوام': 'می‌خواهم',
                   'مساله': 'مسئله', 'مسأله': 'مسئله', 'salam': 'سلام'} if options.lexical_map else {}
        lexicon.update(custom_map or {})
        # Simultaneous replacement makes dictionary behavior inspectable.
        if lexicon:
            pattern = r'(?<![\w\u200c])(?:' + '|'.join(re.escape(k) for k in sorted(lexicon, key=len, reverse=True)) + r')(?![\w\u200c])'
            step('Explicit lexical dictionary', lambda t: re.sub(pattern, lambda m: lexicon[m[0]], t))
    if options.spacing == 'hazm': step('Hazm normalization', lambda t: hazm_normalizer().normalize(t))
    elif options.spacing == 'conservative':
        def spacing(t):
            t = re.sub('\u200c{2,}', '\u200c', t)
            t = re.sub(r'[ \t]*\u200c[ \t]*', '\u200c', t)
            # Only separated prefixes/suffixes are repaired; never split a word like میز.
            t = re.sub(r'(?<!\w)(ن?می)[ \t]+(?=[\u0621-\u06ff])', r'\1\u200c'.replace('\\u200c', '\u200c'), t)
            t = re.sub(r'(?<=[\u0621-\u06ff])[ \t]+(ها|های|تر|ترین|ام)(?![\w\u200c])', '\u200c' + r'\1', t)
            t = re.sub(r'[ \t]+([،؛؟!?.,])', r'\1', t)
            t = re.sub(r'([،؛؟!?])(?=[^\s»”\"\'])', r'\1 ', t)
            return t
        step('Conservative spacing', spacing)
    if options.placeholders:
        def replace_entities(t):
            t = URL.sub(lambda m: '<URL>' + m[0][len(m[0].rstrip('.,!?؟')):], t)
            t = EMAIL.sub('<EMAIL>', t)
            t = MENTION.sub('<USER>', t)
            return NUMBER.sub('<NUM>', t)
        step('Entity placeholders', replace_entities)
    if options.casefold:
        step('Case folding', lambda t: re.sub(r'<[A-Z_]+>|[^<]+|<', lambda m: m[0] if re.fullmatch(r'<[A-Z_]+>', m[0]) else m[0].casefold(), t))
    step('Whitespace', lambda t: re.sub(r'[^\S\n]+', ' ', t).strip())
    return {'source': source, 'text': text, 'options': asdict(options), 'stages': stages,
            'warnings': ['Lexical conversion is an explicit small dictionary, not a general informal-language or Finglish model.'] if options.lexical_map else []}


def normalization_audit(source, options=None, custom_map=None):
    first = normalize(source, options, custom_map)
    second = normalize(first['text'], options, custom_map)
    first['idempotent'] = first['text'] == second['text']
    first['second_pass'] = second['text']
    return first


def unicode_inspect(text):
    import regex
    return {'text': text, 'code_points': len(text), 'utf8_bytes': len(text.encode('utf-8')),
            'grapheme_count': len(regex.findall(r'\X', text)), 'graphemes': regex.findall(r'\X', text),
            'characters': [{'character': c, 'code': f'U+{ord(c):04X}', 'name': unicodedata.name(c, 'UNNAMED'),
                            'category': unicodedata.category(c), 'utf8_bytes': len(c.encode('utf-8'))} for c in text],
            'forms': {f: unicodedata.normalize(f, text) for f in ('NFC', 'NFD', 'NFKC', 'NFKD')}}
