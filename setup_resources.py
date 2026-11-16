"""Download selected optional NLTK data for subsequent offline use."""
import argparse
from pathlib import Path
import nltk


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resources', nargs='+', choices=['wordnet', 'punkt_tab', 'stopwords'], default=['wordnet'])
    args = parser.parse_args()
    destination = Path(__file__).resolve().parent / '.nlp_data'
    destination.mkdir(exist_ok=True)
    for resource in args.resources:
        if not nltk.download(resource, download_dir=str(destination), quiet=False):
            parser.exit(1, f'{resource} download failed. Use approved local NLTK data or retry on an allowed network.\n')
    print('Selected resources are ready for offline use.')


if __name__ == '__main__':
    main()
