#!/usr/bin/env python3
"""Copy one validated byte range without loading the source into RAM."""
import argparse
import json
from pathlib import Path
from _common import cli, digest, number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--offset', type=number, required=True)
    parser.add_argument('--length', type=number, required=True)
    args = parser.parse_args()
    if not args.length or args.offset + args.length > args.input.stat().st_size:
        raise ValueError('range must be nonempty and entirely inside the input')
    with args.input.open('rb') as src, args.output.open('xb') as dst:
        src.seek(args.offset)
        remaining = args.length
        while remaining:
            data = src.read(min(remaining, 1024 * 1024))
            if not data:
                raise ValueError('input changed or ended during carving; output is partial')
            dst.write(data)
            remaining -= len(data)
    print(json.dumps({'output': str(args.output), 'source_offset': args.offset,
                      'length': args.length, 'sha256': digest(args.output)}))


if __name__ == '__main__':
    cli(main)
