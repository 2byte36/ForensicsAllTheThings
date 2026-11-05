#!/usr/bin/env python3
"""List SQLite WAL frames only after validating salts and rolling checksums.

No replay/decryption. A valid frame chain does not establish historical consistency
with a particular main database. Nonzero exit means the output is only a prefix.
"""
import argparse
import json
import struct
from pathlib import Path
from _common import cli


def checksum(data, state, order):
    a, b = state
    for x, y in struct.iter_unpack(order + 'II', data):
        a = (a + x + b) & 0xffffffff
        b = (b + y + a) & 0xffffffff
    return a, b


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('wal', type=Path)
    args = parser.parse_args()
    with args.wal.open('rb') as src:
        header = src.read(32)
        if len(header) != 32:
            raise ValueError('truncated WAL header')
        magic, version, size, sequence, salt1, salt2, check1, check2 = struct.unpack('>8I', header)
        if magic not in (0x377f0682, 0x377f0683) or version != 3007000:
            raise ValueError('unsupported WAL magic/version')
        if size < 512 or size > 65536 or size & (size - 1):
            raise ValueError('invalid WAL page size')
        order = '<' if magic == 0x377f0682 else '>'
        state = checksum(header[:24], (0, 0), order)
        if state != (check1, check2):
            raise ValueError('WAL header checksum mismatch')
        print(json.dumps({'kind': 'header', 'page_size': size, 'checkpoint_sequence': sequence}))
        index = 0
        while True:
            offset = src.tell()
            frame = src.read(24)
            if not frame:
                break
            index += 1
            if len(frame) != 24:
                raise ValueError(f'truncated frame header at {offset}')
            page, db_size, s1, s2, c1, c2 = struct.unpack('>6I', frame)
            data = src.read(size)
            if len(data) != size:
                raise ValueError(f'truncated page at frame {index}')
            if not page or (s1, s2) != (salt1, salt2):
                raise ValueError(f'invalid page number or stale salts at frame {index}')
            state = checksum(frame[:8] + data, state, order)
            if state != (c1, c2):
                raise ValueError(f'checksum mismatch at frame {index}')
            print(json.dumps({'kind': 'frame', 'frame': index, 'offset': offset,
                              'page_number': page, 'commit_db_pages': db_size,
                              'checksum_valid': True}))


if __name__ == '__main__':
    cli(main)
