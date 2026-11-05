#!/usr/bin/env python3
"""Export visits from a copied Chromium History or Firefox places.sqlite database."""
import argparse
import json
import sqlite3
from pathlib import Path
from _common import cli


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('browser', choices=['chromium', 'firefox'])
    parser.add_argument('database', type=Path, help='working copy, with matching sidecars if applicable')
    parser.add_argument('--limit', type=int, default=100)
    args = parser.parse_args()
    if args.limit < 1:
        raise ValueError('limit must be positive')
    query = {
        'chromium': """SELECT v.visit_time AS raw_time,
          datetime(v.visit_time/1000000.0-11644473600,'unixepoch') AS utc,
          u.url,u.title FROM visits v JOIN urls u ON u.id=v.url ORDER BY v.visit_time DESC LIMIT ?""",
        'firefox': """SELECT v.visit_date AS raw_time,
          datetime(v.visit_date/1000000.0,'unixepoch') AS utc,
          p.url,p.title FROM moz_historyvisits v JOIN moz_places p ON p.id=v.place_id
          ORDER BY v.visit_date DESC LIMIT ?"""
    }[args.browser]
    try:
        db = sqlite3.connect(args.database.resolve().as_uri() + '?mode=ro', uri=True)
        try:
            db.row_factory = sqlite3.Row
            for row in db.execute(query, (args.limit,)):
                print(json.dumps(dict(row)))
        finally:
            db.close()
    except sqlite3.Error as exc:
        raise ValueError(f'database/schema error: {exc}') from exc


if __name__ == '__main__':
    cli(main)
