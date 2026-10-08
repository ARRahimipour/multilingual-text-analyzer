"""Create the project virtual environment and install its desktop dependencies."""
import argparse
from pathlib import Path
import subprocess
import sys
import venv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli-only', action='store_true', help='Create .venv without downloading Qt')
    args = parser.parse_args()
    if sys.version_info < (3, 10):
        parser.exit(2, 'Python 3.10 or newer is required; Python 3.12 is the tested version.\n')
    root = Path(__file__).resolve().parent
    environment = root / '.venv'
    try:
        if environment.exists() and not (environment / 'pyvenv.cfg').is_file():
            parser.exit(2, '.venv already exists but is not a virtual environment. Rename it first.\n')
        if not environment.exists():
            print('Creating .venv...', flush=True)
            venv.EnvBuilder(with_pip=True).create(environment)
        interpreter = environment / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
        if not interpreter.is_file():
            parser.exit(2, 'The existing .venv belongs to a different platform or is incomplete. Recreate it.\n')
        if not args.cli_only:
            subprocess.run([str(interpreter), '-m', 'pip', 'install', '-r', str(root / 'requirements.txt')],
                           cwd=root, check=True)
        print('Environment ready.' if args.cli_only else
              'Environment ready. Launch the desktop with: python run_gui.py')
        print('For CLI-only use, run main.py with the Python executable inside .venv.')
        return 0
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f'Setup failed: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
