"""Direction detection and non-destructive alignment regression checks."""
import unittest
from unittest.mock import Mock
from nlp_analyzer.direction import align_editor, text_direction
from nlp_analyzer import analyze
from nlp_analyzer.reports import render_report


class DirectionTests(unittest.TestCase):
    def test_persian_arabic_and_english(self):
        for text in ['سلام دنیا', 'مرحبا بالعالم', '۱۴۰۵: این متن فارسی است!']:
            self.assertEqual(text_direction(text), 'rtl')
        for text in ['', '123!?', 'Hello world']:
            self.assertEqual(text_direction(text), 'ltr')

    def test_mixed_text_uses_dominant_direction(self):
        self.assertEqual(text_direction('NLP این متن فارسی درباره زبان است'), 'rtl')
        self.assertEqual(text_direction('An English paragraph mentions سلام.'), 'ltr')
        self.assertEqual(text_direction('بa'), 'rtl')
        self.assertEqual(text_direction('aب'), 'ltr')

    def test_editor_switches_alignment_without_editing_content(self):
        editor = Mock()
        self.assertEqual(align_editor(editor, 'سلام دنیا\nHello world'), 'ltr')
        editor.tag_add.assert_any_call('rtl', '1.0', '1.end+1c')
        editor.tag_add.assert_any_call('ltr', '2.0', '2.end+1c')
        editor.insert.assert_not_called()
        editor.delete.assert_not_called()
        editor.mark_set.assert_not_called()
        editor.reset_mock()
        align_editor(editor, '')
        editor.tag_remove.assert_any_call('rtl', '1.0', 'end')
        editor.tag_add.assert_called_once_with('ltr', '1.0', '1.end+1c')

    def test_html_direction(self):
        report = render_report(analyze('سلام دنیا. Hello world.'), 'html')
        self.assertIn('<li dir="rtl">سلام دنیا.</li>', report)
        self.assertIn('<li dir="ltr">Hello world.</li>', report)
        self.assertIn('<td dir="rtl">سلام</td>', report)
        self.assertIn('text-align:start', report)

    def test_alignment_does_not_change_counts(self):
        text = 'سلام دنیا! Hello world.'
        before = analyze(text).to_dict()
        align_editor(Mock(), text)
        self.assertEqual(analyze(text).to_dict(), before)
