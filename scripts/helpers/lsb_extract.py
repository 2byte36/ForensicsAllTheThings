#!/usr/bin/env python3
"""Extract one image channel's bitplane in row-major order; requires Pillow."""
import argparse
from pathlib import Path
from _common import cli, save


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('output', type=Path)
    parser.add_argument('--channel', choices=['R', 'G', 'B', 'A'], default='B')
    parser.add_argument('--bit', type=int, choices=range(8), default=0)
    parser.add_argument('--order', choices=['msb', 'lsb'], default='msb', help='bit packing within each output byte')
    args = parser.parse_args()
    from PIL import Image
    with Image.open(args.input) as image:
        if image.mode not in ('RGB', 'RGBA'):
            raise ValueError('requires native RGB/RGBA; palette and grayscale modes need explicit interpretation')
        if args.channel not in image.getbands():
            raise ValueError('requested channel is absent')
        samples = image.getchannel(args.channel).tobytes()
    if len(samples) % 8:
        raise ValueError('pixel count is not divisible by eight; choose an explicit crop before extraction')
    out = bytearray()
    for start in range(0, len(samples), 8):
        byte = 0
        for i, value in enumerate(samples[start:start+8]):
            shift = 7-i if args.order == 'msb' else i
            byte |= ((value >> args.bit) & 1) << shift
        out.append(byte)
    save(args.output, out)


if __name__ == '__main__':
    cli(main)
