#!/usr/bin/env python3
"""Stream SHA-256 and size inventory as JSONL; skip symlinks and special files."""
import argparse
import json
from pathlib import Path
from _common import cli, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    args = parser.parse_args()
    if not args.path.exists() or args.path.is_symlink():
        raise ValueError('input must be an existing regular file or directory, not a symlink')
    paths = [args.path] if args.path.is_file() else sorted(args.path.rglob('*'))
    for path in paths:
        if path.is_symlink() or not path.is_file():
            continue
        stat = path.stat()
        print(json.dumps({'path': str(path), 'size': stat.st_size,
                          'sha256': digest(path), 'mtime_ns': stat.st_mtime_ns}))


if __name__ == '__main__':
    cli(main)
