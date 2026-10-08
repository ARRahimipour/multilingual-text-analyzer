"""Launch the desktop with this project's .venv, without shell activation."""
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent
    interpreter = root / '.venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    if not interpreter.is_file():
        print('Project environment not found. Run: python setup_env.py', file=sys.stderr)
        return 2
    try:
        return subprocess.call([str(interpreter), str(root / 'main.py'), '--gui'], cwd=root)
    except OSError as exc:
        print(f'Cannot launch the project environment: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
