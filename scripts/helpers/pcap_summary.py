#!/usr/bin/env python3
"""Run read-only TShark reports into a NEW output directory."""
import argparse
import subprocess
from pathlib import Path
from _common import cli


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--wireless', action='store_true')
    args = parser.parse_args()
    if not args.capture.is_file():
        raise ValueError('capture must exist')
    args.output.mkdir()
    reports = {'protocols.txt': ['-q', '-z', 'io,phs'],
               'conversations.txt': ['-q', '-z', 'conv,tcp', '-z', 'conv,udp'],
               'dns.tsv': ['-Y', 'dns.flags.response == 0', '-T', 'fields',
                           '-e', 'frame.number', '-e', 'frame.time_epoch', '-e', 'dns.qry.name']}
    if args.wireless:
        reports['wireless.tsv'] = ['-Y', 'wlan.fc.type == 0', '-T', 'fields', '-e', 'frame.number',
                                  '-e', 'wlan.bssid', '-e', 'wlan.ssid']
        reports['eapol.txt'] = ['-Y', 'eapol', '-V']
    for name, options in reports.items():
        with (args.output / name).open('x') as out:
            result = subprocess.run(['tshark', '-r', str(args.capture), *options], stdout=out)
        if result.returncode:
            raise ValueError(f'tshark failed for {name}; directory contains partial reports')


if __name__ == '__main__':
    cli(main)
