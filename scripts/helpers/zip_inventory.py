#!/usr/bin/env python3
"""List ZIP/APK/OOXML members as JSONL without extracting or decrypting them."""
import argparse
import json
import zipfile
from pathlib import PurePosixPath
from _common import cli


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    args = parser.parse_args()
    try:
        with zipfile.ZipFile(args.input) as archive:
            for index, entry in enumerate(archive.infolist()):
                name = entry.filename.replace('\\', '/')
                parts = PurePosixPath(name).parts
                suspicious = name.startswith('/') or '..' in parts or (len(name) > 1 and name[1] == ':')
                print(json.dumps({'index': index, 'name': entry.filename, 'size': entry.file_size,
                                  'compressed_size': entry.compress_size, 'method': entry.compress_type,
                                  'encrypted_flag': bool(entry.flag_bits & 1), 'crc32': f'{entry.CRC:08x}',
                                  'header_offset': entry.header_offset, 'suspicious_path': suspicious}))
    except zipfile.BadZipFile as exc:
        raise ValueError(f'not a readable ZIP container: {exc}') from exc


if __name__ == '__main__':
    cli(main)
