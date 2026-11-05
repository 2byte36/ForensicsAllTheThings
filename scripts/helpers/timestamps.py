#!/usr/bin/env python3
"""Convert integer timestamps to UTC without floating-point epoch arithmetic."""
import argparse
import json
from datetime import datetime, timedelta, timezone
from _common import cli


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('format', choices=['unix', 'unix-ms', 'unix-us', 'filetime', 'chromium', 'apple'])
    parser.add_argument('value', type=int, help='signed decimal integer; sentinel interpretation is caller-owned')
    args = parser.parse_args()
    epoch_year, divisor = {
        'unix': (1970, 1), 'unix-ms': (1970, 1000), 'unix-us': (1970, 1000000),
        'filetime': (1601, 10000000), 'chromium': (1601, 1000000), 'apple': (2001, 1)
    }[args.format]
    seconds, fractional = divmod(args.value, divisor)
    micros, remainder = divmod(fractional * 1000000, divisor)
    try:
        utc = datetime(epoch_year, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds, microseconds=micros)
    except OverflowError as exc:
        raise ValueError('timestamp outside supported datetime range') from exc
    print(json.dumps({'format': args.format, 'raw': args.value, 'utc': utc.isoformat(),
                      'remaining_100ns_ticks': remainder // 1000000 if args.format == 'filetime' else 0}))


if __name__ == '__main__':
    cli(main)
