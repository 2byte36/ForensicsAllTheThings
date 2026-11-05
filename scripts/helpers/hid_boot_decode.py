#!/usr/bin/env python3
"""Decode NEW presses in one 8-byte USB boot-keyboard report per hex-text line.

US layout subset only; no report IDs, NKRO, or host auto-repeat. Emits events,
not an assumed final edited document. Unknown usages remain explicit.
"""
import argparse
import json
from _common import cli


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='text file with exactly one 8-byte report per nonempty line')
    args = parser.parse_args()
    previous = set()
    caps = False
    pairs = dict(zip(range(30, 40), zip('1234567890', '!@#$%^&*()')))
    pairs.update({45: ('-', '_'), 46: ('=', '+'), 47: ('[', '{'), 48: (']', '}'),
                  49: ('\\', '|'), 51: (';', ':'), 52: ("'", '"'), 53: ('`', '~'),
                  54: (',', '<'), 55: ('.', '>'), 56: ('/', '?')})
    controls = {40: '<ENTER>', 41: '<ESC>', 42: '<BACKSPACE>', 43: '<TAB>', 44: ' '}
    with open(args.input, encoding='ascii') as src:
        for line_number, line in enumerate(src, 1):
            if not line.strip():
                continue
            report = bytes.fromhex(line.replace(':', ''))
            if len(report) != 8 or report[1] != 0:
                raise ValueError(f'line {line_number}: not an 8-byte boot keyboard report')
            keys = set(report[2:]) - {0}
            if keys & {1, 2, 3}:
                raise ValueError(f'line {line_number}: HID error/rollover report')
            shift = bool(report[0] & 0x22)
            for code in dict.fromkeys(report[2:]):
                if not code or code in previous:
                    continue
                if code == 57:
                    caps = not caps
                    text = '<CAPSLOCK>'
                elif 4 <= code <= 29:
                    text = chr(ord('a') + code - 4)
                    if caps ^ shift:
                        text = text.upper()
                elif code in pairs:
                    text = pairs[code][int(shift)]
                else:
                    text = controls.get(code, f'<USAGE_{code}>')
                print(json.dumps({'line': line_number, 'usage': code, 'modifiers': report[0], 'text': text}))
            previous = keys


if __name__ == '__main__':
    cli(main)
