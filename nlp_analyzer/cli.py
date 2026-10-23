"""Command-line interface for reproducible homework analysis."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
from .core import AnalysisOptions, analyze
from .dataset import clean_dataset
from .preprocessing import PRESET_NAMES, preset
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
    cleaning = parser.add_argument_group('session 2 preprocessing (opt-in)')
    cleaning.add_argument('--clean-preset', choices=PRESET_NAMES,
                          help='Task-dependent cleaning preset; defaults to no cleaning')
    cleaning.add_argument('--emoji', choices=['keep', 'remove', 'label'])
    cleaning.add_argument('--punctuation', choices=['keep', 'normalize', 'remove'])
    cleaning.add_argument('--number-mode', choices=['keep', 'remove', 'placeholder'])
    cleaning.add_argument('--digit-style', choices=['keep', 'ascii', 'persian'])
    cleaning.add_argument('--invisible', choices=['none', 'safe', 'controls'])
    cleaning.add_argument('--mask-pii', action='store_true', help='Mask emails, Iranian mobiles and 10-digit IDs')
    cleaning.add_argument('--keep-urls', action='store_true')
    cleaning.add_argument('--keep-mentions', action='store_true')
    cleaning.add_argument('--keep-hashtag-marker', action='store_true')
    cleaning.add_argument('--remove-diacritics', action='store_true')
    cleaning.add_argument('--join-broken-lines', action='store_true')
    cleaning.add_argument('--reduce-elongations', action='store_true')
    cleaning.add_argument('--keep-elongations', action='store_true')
    cleaning.add_argument('--remove-retweets', action='store_true')
    cleaning.add_argument('--keep-retweets', action='store_true')
    cleaning.add_argument('--keep-html', action='store_true')
    dataset_group = parser.add_argument_group('dataset cleaning (.csv, .tsv, .jsonl)')
    dataset_group.add_argument('--dataset', action='store_true', help='Clean rows; requires file and --output')
    dataset_group.add_argument('--text-column', default='text')
    dataset_group.add_argument('--min-length', type=int, default=3)
    dataset_group.add_argument('--max-length', type=int, default=5000)
    dataset_group.add_argument('--min-persian-script-ratio', type=float, default=0.0)
    dataset_group.add_argument('--keep-duplicates', action='store_true')
    dataset_group.add_argument('--near-duplicate', type=float, metavar='THRESHOLD')
    parser.add_argument('--format', choices=['text', 'json', 'csv', 'html'], default='text')
    parser.add_argument('--output', type=Path, help='Write UTF-8 output to this file')
    args = parser.parse_args(argv)
    if args.gui:
        try:
            from .gui import launch
            launch()
        except (ImportError, RuntimeError) as exc:
            parser.exit(2, f'Desktop interface unavailable: {exc}\nUse the CLI or install the desktop dependency: python -m pip install -r requirements-gui.txt\n')
        return 0
    try:
        modifications = {'emoji_mode': args.emoji, 'punctuation_mode': args.punctuation,
                         'number_mode': args.number_mode, 'digit_style': args.digit_style,
                         'invisible_mode': args.invisible}
        modifications = {key: value for key, value in modifications.items() if value is not None}
        if args.mask_pii: modifications['mask_pii'] = True
        if args.keep_urls: modifications['remove_urls'] = False
        if args.keep_mentions: modifications['remove_mentions'] = False
        if args.keep_hashtag_marker: modifications['strip_hashtags'] = False
        if args.remove_diacritics: modifications['remove_diacritics'] = True
        if args.join_broken_lines: modifications['join_broken_lines'] = True
        if args.reduce_elongations and args.keep_elongations:
            raise ValueError('Choose only one of --reduce-elongations / --keep-elongations.')
        if args.remove_retweets and args.keep_retweets:
            raise ValueError('Choose only one of --remove-retweets / --keep-retweets.')
        if args.reduce_elongations: modifications['reduce_elongations'] = True
        if args.keep_elongations: modifications['reduce_elongations'] = False
        if args.remove_retweets: modifications['remove_retweet_marker'] = True
        if args.keep_retweets: modifications['remove_retweet_marker'] = False
        if args.keep_html: modifications['remove_html'] = False
        preprocessor = (replace(preset(args.clean_preset or 'general'), **modifications)
                        if args.clean_preset or modifications or args.dataset else None)
        if args.dataset:
            if not args.file or not args.output:
                raise ValueError('--dataset requires an input file and --output.')
            summary = clean_dataset(args.file, args.output, preprocessor,
                                    text_column=args.text_column, min_length=args.min_length,
                                    max_length=args.max_length,
                                    min_persian_ratio=args.min_persian_script_ratio,
                                    deduplicate=not args.keep_duplicates,
                                    near_duplicate_threshold=args.near_duplicate)
            sys.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
            return 0
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
                                              persian_normalization=args.persian, include_numbers=args.include_numbers,
                                              preprocessing=preprocessor))
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
