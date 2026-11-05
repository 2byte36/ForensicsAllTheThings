#!/usr/bin/env python3
"""Run basic Volatility 3 Windows reports into a NEW directory; no dumping/execution."""
import argparse
import subprocess
from pathlib import Path
from _common import cli


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('memory', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--vol', default='vol', help='Volatility 3 executable path')
    args = parser.parse_args()
    if not args.memory.is_file():
        raise ValueError('memory input must exist')
    args.output.mkdir()
    failed = []
    for plugin in ('windows.info', 'windows.pslist', 'windows.pstree', 'windows.cmdline', 'windows.netscan'):
        with (args.output / f'{plugin}.txt').open('x') as out, (args.output / f'{plugin}.stderr.txt').open('x') as err:
            result = subprocess.run([args.vol, '-f', str(args.memory), plugin], stdout=out, stderr=err)
        if result.returncode:
            failed.append(plugin)
    if failed:
        raise ValueError('plugins failed; inspect stderr reports: ' + ', '.join(failed))


if __name__ == '__main__':
    cli(main)
