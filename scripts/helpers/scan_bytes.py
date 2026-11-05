#!/usr/bin/env python3
"""Stream exact byte-marker offsets, including overlapping and chunk-boundary hits."""
import argparse
from pathlib import Path
from _common import cli


def offsets(src, needle, chunk_size=1024 * 1024):
    tail = b''
    consumed = 0
    while True:
        chunk = src.read(chunk_size)
        if not chunk:
            break
        data = tail + chunk
        base = consumed - len(tail)
        start = 0
        while True:
            hit = data.find(needle, start)
            if hit < 0:
                break
            yield base + hit
            start = hit + 1
        consumed += len(chunk)
        tail = data[-(len(needle) - 1):] if len(needle) > 1 else b''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--text', help='UTF-8 literal marker')
    group.add_argument('--hex', help='hexadecimal byte marker')
    args = parser.parse_args()
    needle = args.text.encode('utf-8') if args.text is not None else bytes.fromhex(args.hex)
    if not needle or len(needle) > 1024 * 1024:
        raise ValueError('marker length must be between 1 byte and 1 MiB')
    with args.input.open('rb') as src:
        for offset in offsets(src, needle):
            print(f'{offset}\t0x{offset:x}')


if __name__ == '__main__':
    cli(main)
