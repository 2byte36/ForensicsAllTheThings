#!/usr/bin/env python3
"""Extract MIME attachments into a NEW directory using generated filenames."""
import argparse
import json
from email import policy
from email.parser import BytesParser
from pathlib import Path
from _common import cli, digest, read_small, save


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('output', type=Path, help='new directory; parent must exist')
    args = parser.parse_args()
    message = BytesParser(policy=policy.default).parsebytes(read_small(args.input))
    args.output.mkdir()
    for index, part in enumerate(message.walk()):
        if not (part.get_filename() or part.get_content_disposition() == 'attachment'):
            continue
        data = part.get_payload(decode=True)
        if data is None:
            print(json.dumps({'part': index, 'status': 'not extracted: multipart or encapsulated message'}))
            continue
        dest = args.output / f'attachment-{index}.bin'
        save(dest, data)
        print(json.dumps({'part': index, 'output': str(dest), 'original_name': part.get_filename(),
                          'content_type': part.get_content_type(), 'size': len(data), 'sha256': digest(dest)}))


if __name__ == '__main__':
    cli(main)
