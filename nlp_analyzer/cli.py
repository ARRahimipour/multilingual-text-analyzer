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
    lab_group = parser.add_argument_group('four-handout learning lab')
    lab_group.add_argument('--lab', choices=['normalize', 'unicode', 'compare', 'subword', 'oov', 'batch', 'chunk', 'morphology', 'features', 'classify'])
    lab_group.add_argument('--lab-config', type=Path, help='JSON object of lab options; see examples/lab_config.json')
    lab_group.add_argument('--training-corpus', type=Path, help='UTF-8 text, one training document per line; labeled JSONL for classify')
    lab_group.add_argument('--evaluation', type=Path, help='Separate labeled JSONL holdout for classify')
    lab_group.add_argument('--tokenizer', choices=['bpe', 'wordpiece', 'unigram', 'sentencepiece'], default='bpe')
    lab_group.add_argument('--vocab-size', type=positive_int, default=300)
    lab_group.add_argument('--max-tokens', type=positive_int, default=128)
    lab_group.add_argument('--overlap', type=int, default=16)
    lab_group.add_argument('--model', type=Path, help='Local tokenizer JSON or SentencePiece .model')
    lab_group.add_argument('--save-model', type=Path)
    args = parser.parse_args(argv)
    if args.gui and args.lab:
        parser.error('Use --lab separately from --gui.')
    if args.gui:
        try:
            from .gui import launch
            launch()
        except (ImportError, RuntimeError) as exc:
            parser.exit(2, f'Desktop interface unavailable: {exc}\nUse the CLI or install the desktop dependency: python -m pip install -r requirements-gui.txt\n')
        return 0
    try:
        if args.lab:
            from .lab import run_lab, save_lab_report
            if args.dataset or args.gui:
                raise ValueError('Use --lab separately from --dataset or --gui.')
            sources = [p.resolve() for p in (args.file, args.training_corpus, args.evaluation, args.model, args.lab_config) if p]
            for output in (args.output, args.save_model):
                if output and output.resolve() in sources:
                    raise ValueError('Lab output must not overwrite an input or loaded model.')
            if args.output and args.save_model and args.output.resolve() == args.save_model.resolve():
                raise ValueError('Report and model destinations must be different.')
            text = args.file.read_text(encoding='utf-8-sig') if args.file else args.text
            if text is None:
                if sys.stdin.isatty(): raise ValueError('Provide a file, --text or piped input for the lab.')
                text = sys.stdin.read()
            corpus = args.training_corpus.read_text(encoding='utf-8-sig').splitlines() if args.training_corpus else [text]
            corpus = [line for line in corpus if line.strip()]
            settings = dict(method=args.tokenizer, vocab_size=args.vocab_size,
                            max_length=args.max_tokens, overlap=args.overlap)
            if args.lab_config:
                config = json.loads(args.lab_config.read_text(encoding='utf-8'))
                if not isinstance(config, dict): raise ValueError('Lab config must be a JSON object.')
                if any(key in config for key in ('model_file', 'save_model')):
                    raise ValueError('Use --model and --save-model for file paths, not lab config.')
                settings.update(config)
            if args.model: settings['model_file'] = str(args.model)
            if args.save_model: settings['save_model'] = str(args.save_model)
            if args.lab == 'classify':
                if not args.training_corpus: raise ValueError('Classification requires --training-corpus with labeled JSONL records.')
                settings['training_records'] = [json.loads(row) for row in corpus]
                if args.evaluation:
                    settings['evaluation_records'] = [json.loads(row) for row in args.evaluation.read_text(encoding='utf-8').splitlines() if row.strip()]
            result = run_lab(args.lab, text, corpus, **settings)
            if args.output: save_lab_report(result, args.output)
            else: print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        modifications = {'emoji_mode' : args.emoji, 'punctuation_mode': args.punctuation,
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
    except (OSError, UnicodeError, ValueError, ImportError, LookupError, TypeError) as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
