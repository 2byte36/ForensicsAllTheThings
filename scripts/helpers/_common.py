"""Shared CLI utilities; Python 3.9+, standard library only."""
import argparse
import hashlib
import sys
from pathlib import Path


def number(text):
    try:
        value = int(text, 16 if text.lower().startswith('0x') else 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('expected decimal or 0x-prefixed integer') from exc
    if value < 0:
        raise argparse.ArgumentTypeError('expected a nonnegative integer')
    return value


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def read_small(path, limit=64 * 1024 * 1024):
    with Path(path).open('rb') as src:
        data = src.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f'input exceeds {limit} bytes; use a smaller extracted region')
    return data


def save(path, data):
    # No implicit directory creation or replacement of existing output.
    with Path(path).open('xb') as out:
        out.write(data)


def cli(main):
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        sys.exit(1)
