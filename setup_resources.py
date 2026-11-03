"""Download optional English WordNet once, then use it fully offline."""
from pathlib import Path
import nltk

if __name__ == '__main__':
    destination = Path(__file__).resolve().parent / '.nlp_data'
    destination.mkdir(exist_ok=True)
    if not nltk.download('wordnet', download_dir=str(destination), quiet=False):
        raise SystemExit('WordNet download failed. Other lab features do not need it.')
    print('WordNet ready for offline English lemmatization.')
