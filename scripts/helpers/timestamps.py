#!/usr/bin/env python3
"""Convert decimal timestamps or little-endian FILETIME bytes to UTC."""
import argparse
import json
from datetime import datetime, timedelta, timezone
from _common import cli


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('format', choices=['unix', 'unix-ms', 'unix-us', 'filetime', 'chromium', 'apple'])
    parser.add_argument('value', help='signed decimal integer, or quoted hex bytes with --hex-le')
    parser.add_argument('--hex-le', action='store_true',
                        help='FILETIME only: exactly 8 little-endian hex bytes, spaced or compact')
    args = parser.parse_args()
    if args.hex_le:
        if args.format != 'filetime':
            parser.error('--hex-le is only supported for filetime')
        try:
            raw_bytes = bytes.fromhex(args.value)
        except ValueError:
            parser.error('--hex-le expects hex bytes, e.g. "0C 66 1E 5A D1 4D DD 01"')
        if len(raw_bytes) != 8:
            parser.error('FILETIME requires exactly 8 bytes')
        value = int.from_bytes(raw_bytes, byteorder='little', signed=False)
    else:
        try:
            value = int(args.value)
        except ValueError:
            parser.error('expected a decimal integer; use --hex-le for FILETIME hex bytes')
    epoch_year, divisor = {
        'unix': (1970, 1), 'unix-ms': (1970, 1000), 'unix-us': (1970, 1000000),
        'filetime': (1601, 10000000), 'chromium': (1601, 1000000), 'apple': (2001, 1)
    }[args.format]
    seconds, fractional = divmod(value, divisor)
    micros, remainder = divmod(fractional * 1000000, divisor)
    try:
        utc = datetime(epoch_year, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds, microseconds=micros)
    except OverflowError as exc:
        raise ValueError('timestamp outside supported datetime range') from exc
    result = {'format': args.format, 'raw': value, 'utc': utc.isoformat(),
              'remaining_100ns_ticks': remainder // 1000000 if args.format == 'filetime' else 0}
    if args.hex_le:
        result['raw_hex_le'] = raw_bytes.hex(' ')
    if args.format == 'filetime':
        # datetime stops at microseconds; retain all seven FILETIME fractional digits.
        result['utc_100ns'] = utc.isoformat(timespec='seconds')[:-6] + f'.{fractional:07d}Z'
    print(json.dumps(result))


if __name__ == '__main__':
    cli(main)
