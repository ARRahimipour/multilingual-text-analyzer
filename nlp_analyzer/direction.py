"""Unicode-aware display alignment without changing source text."""
import unicodedata


def text_direction(text: str) -> str:
    """Choose the dominant strong direction; ties follow the first letter.

    Digits, punctuation, marks, and explicit formatting controls do not vote.
    This detects writing direction, not a specific language.
    """
    rtl = ltr = 0
    first = None
    for char in text:
        bidi = unicodedata.bidirectional(char)
        if bidi in {'R', 'AL'}:
            rtl += 1
            first = first or 'rtl'
        elif bidi == 'L':
            ltr += 1
            first = first or 'ltr'
    if rtl == ltr:
        return first or 'ltr'
    return 'rtl' if rtl > ltr else 'ltr'


def align_editor(editor, text: str) -> str:
    """Apply paragraph justification tags while preserving text and cursor."""
    dominant = text_direction(text)
    editor.tag_remove('rtl', '1.0', 'end')
    editor.tag_remove('ltr', '1.0', 'end')
    for line, content in enumerate(text.split('\n'), 1):
        direction = text_direction(content) if any(c.isalpha() for c in content) else dominant
        editor.tag_add(direction, f'{line}.0', f'{line}.end+1c')
    return dominant
