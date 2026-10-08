"""Command-line interface for reproducible homework analysis."""
import argparse
from pathlib import Path
import sys
from .core import AnalysisOptions, analyze
from .reports import render_report


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError('must be a positive integer')
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description='Count sentences, words, unique words, and frequent words.')
    source = parser.add_mutually_exclusive_group()
    source.add_argument('file', nargs='?', type=Path, help='UTF-8 input file; omit to read stdin')
    source.add_argument('--text', help='Analyze a literal string')
    source.add_argument('--gui', action='store_true', help='Launch the desktop interface')
    parser.add_argument('--top', type=positive_int, default=10, help='Number of frequent words (default: 10)')
    parser.add_argument('--case-sensitive', action='store_true')
    parser.add_argument('--persian', action='store_true', help='Normalize Arabic yeh/kaf to Persian forms')
    parser.add_argument('--include-numbers', action='store_true')
    parser.add_argument('--format', choices=['text', 'json', 'csv', 'html'], default='text')
    parser.add_argument('--output', type=Path, help='Write UTF-8 output to this file')
    args = parser.parse_args(argv)
    if args.gui:
        try:
            from .gui import launch
            launch()
        except (ImportError, RuntimeError) as exc:
            parser.exit(2, f'Desktop interface unavailable: {exc}\nUse the CLI or install Python with Tk support.\n')
        return 0
    try:
        if args.file and args.output and args.file.resolve() == args.output.resolve():
            raise ValueError('Output must not overwrite the input file.')
        if args.file:
            text = args.file.read_text(encoding='utf-8-sig')
        elif args.text is not None:
            text = args.text
        else:
            if sys.stdin.isatty():
                parser.error('provide a file, --text, piped input, or --gui')
            text = sys.stdin.read()
        result = analyze(text, AnalysisOptions(top_n=args.top, case_sensitive=args.case_sensitive,
                                              persian_normalization=args.persian, include_numbers=args.include_numbers))
        report = render_report(result, args.format)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(report, encoding='utf-8')
        else:
            sys.stdout.write(report)
        for warning in result.warnings:
            print('Warning: ' + warning, file=sys.stderr)
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
