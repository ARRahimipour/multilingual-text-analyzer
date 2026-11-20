"""Explain Unicode spaces without changing the bytes of the NLP source."""


def visible_spaces(text: str) -> str:
    """Human-readable *display* only; do not send this text to tokenizers."""
    return (text.replace('\u00a0', '⟦NBSP⟧').replace('\u200c', '⟦ZWNJ⟧')
            .replace('\u200d', '⟦ZWJ⟧').replace('\t', '⇥')
            .replace(' ', '·').replace('\n', '↵\n'))


def spacing_counts(text: str) -> dict:
    return {
        'ordinary_spaces_U+0020': text.count(' '),
        'half_spaces_ZWNJ_U+200C': text.count('\u200c'),
        'joiners_ZWJ_U+200D': text.count('\u200d'),
        'non_breaking_spaces_U+00A0': text.count('\u00a0'),
        'tabs': text.count('\t'),
        'line_breaks': text.count('\n'),
    }
