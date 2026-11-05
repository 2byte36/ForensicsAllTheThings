#!/usr/bin/env python3
"""Decode exactly one Base64, hex, or repeating-XOR layer (64 MiB input limit)."""
import argparse
import base64
from _common import cli, read_small, save


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['base64', 'base64url', 'hex', 'xor'])
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('--key-hex', help='required for xor; key repeats from input byte zero')
    parser.add_argument('--ignore-whitespace', action='store_true', help='Base64 formatting only')
    args = parser.parse_args()
    data = read_small(args.input)
    if args.mode in ('base64', 'base64url'):
        if args.key_hex:
            raise ValueError('--key-hex applies only to xor')
        if args.ignore_whitespace:
            data = b''.join(data.split())
        data = base64.b64decode(data, altchars=b'-_' if args.mode == 'base64url' else None,
                                validate=True)
    elif args.mode == 'hex':
        if args.key_hex or args.ignore_whitespace:
            raise ValueError('hex mode accepts no additional flags; ASCII whitespace is allowed')
        data = bytes.fromhex(data.decode('ascii'))
    else:
        if not args.key_hex or args.ignore_whitespace:
            raise ValueError('xor requires --key-hex and disallows --ignore-whitespace')
        key = bytes.fromhex(args.key_hex)
        if not key:
            raise ValueError('empty XOR key')
        data = bytes(value ^ key[i % len(key)] for i, value in enumerate(data))
    save(args.output, data)


if __name__ == '__main__':
    cli(main)
