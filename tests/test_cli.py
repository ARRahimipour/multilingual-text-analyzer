"""End-to-end CLI and report contracts."""
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from nlp_analyzer import analyze
from nlp_analyzer.reports import render_report

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args, input=None):
    return subprocess.run([sys.executable, '-m', 'nlp_analyzer', *args], cwd=ROOT,
                          input=input, capture_output=True, text=True, encoding='utf-8')


class CLITests(unittest.TestCase):
    def test_sample_strict_pass(self):
        process = run_cli('examples/english_300.txt', '--strict', '--format', 'json')
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)['word_count'], 300)

    def test_target_failure(self):
        process = run_cli('--text', 'Hello world.', '--strict')
        self.assertEqual(process.returncode, 1)
        self.assertIn('[CHECK]', process.stdout)

    def test_pipe(self):
        process = run_cli('--format', 'json', input='سلام دنیا!')
        self.assertEqual(process.returncode, 0)
        self.assertEqual(json.loads(process.stdout)['word_count'], 2)

    def test_missing_file(self):
        self.assertEqual(run_cli('does-not-exist.txt').returncode, 2)

    def test_invalid_top(self):
        self.assertEqual(run_cli('--text', 'a', '--top', '0').returncode, 2)

    def test_empty_literal(self):
        result = run_cli('--text', '', '--format', 'json')
        self.assertEqual(json.loads(result.stdout)['word_count'], 0)

    def test_export_and_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / 'sub' / 'analysis.json'
            process = run_cli('--text', 'Hello hello!', '--output', str(destination), '--format', 'json')
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(json.loads(destination.read_text())['unique_word_count'], 1)
            invalid = Path(folder) / 'invalid.txt'
            invalid.write_bytes(b'\xff\xfe\xff')
            self.assertEqual(run_cli(str(invalid)).returncode, 2)

    def test_prevent_input_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'input.txt'
            path.write_text('Keep this text.')
            self.assertEqual(run_cli(str(path), '--output', str(path)).returncode, 2)
            self.assertEqual(path.read_text(), 'Keep this text.')

    def test_warning_keeps_json_valid(self):
        process = run_cli('--text', '你好世界。', '--format', 'json')
        self.assertEqual(process.returncode, 0)
        self.assertTrue(json.loads(process.stdout)['warnings'])
        self.assertIn('Warning:', process.stderr)

    def test_all_formats(self):
        result = analyze('One two two.')
        self.assertIn('Words: 3', render_report(result))
        self.assertEqual(json.loads(render_report(result, 'json'))['word_count'], 3)
        rows = list(csv.reader(io.StringIO(render_report(result, 'csv'))))
        self.assertEqual(rows, [['word', 'count'], ['two', '2'], ['one', '1']])
        self.assertIn('<!doctype html>', render_report(result, 'html'))

    def test_html_escapes_input(self):
        report = render_report(analyze('<script>alert("x")</script>'), 'html')
        self.assertNotIn('<script>', report)
        self.assertIn('&lt;script&gt;', report)

    def test_empty_reports(self):
        for format in ['text', 'json', 'csv', 'html']:
            self.assertTrue(render_report(analyze(''), format))

    def test_bad_report_format(self):
        with self.assertRaises(ValueError):
            render_report(analyze('a'), 'invalid')


if __name__ == '__main__':
    unittest.main()
