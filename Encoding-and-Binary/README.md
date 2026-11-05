# Encoding and binary transformations

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Recognize representations, decode bytes explicitly, and keep each intermediate result reproducible.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Identify the layer](#identify-the-layer)
- [Strict Base64 and hex decoding](#strict-base64-and-hex-decoding)
- [Compression wrappers](#compression-wrappers)
- [XOR and byte order](#xor-and-byte-order)
- [Transformation notebook](#transformation-notebook)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| file / strings / xxd / rg | Type, bytes, and string triage | `sudo apt install file binutils xxd ripgrep coreutils`. [Source](https://github.com/BurntSushi/ripgrep#installation) | `file --version`; `rg --version` |

## Script and command recipe

Helper: [decode_bytes.py](../scripts/helpers/decode_bytes.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/decode_bytes.py hex "$CASE/hex.txt" "$CASE/carved/hex.bin"
python3 scripts/helpers/decode_bytes.py xor "$CASE/cipher.bin" "$CASE/carved/plain.bin" --key-hex 1337
```

Processes exactly one layer, capped at 64 MiB input. Base64 is strict and does not silently fix padding. The XOR key is illustrative and repeats from byte zero; replace it with evidence-backed bytes.

## Identify the layer

| Observation | Candidate | Confirm with |
| --- | --- | --- |
| Even-length hexadecimal text | Base16 | Valid alphabet and decoded file structure |
| Mostly letters/digits with `+`, `/`, `=` | Base64 | Alphabet, padding, context; plain text can look similar |
| `-` and `_` in an encoded token | URL-safe Base64 | Producer format; do not change arbitrary punctuation |
| Mostly A–Z and 2–7 | Base32 | Alphabet and decoder result |
| `%xx` sequences | URL percent encoding | Decode bytes; `+` means space only in form-style contexts |
| Alternating printable bytes and NUL | UTF-16LE/BE | BOM, alignment, surrounding structure |
| `1f 8b` | gzip | Decompress and validate CRC/length |
| Often `78 01`, `78 9c`, or `78 da` | zlib wrapper | Header checks and successful decompression |
| High byte diversity | Compression, encryption, or media | Structure and producing code; entropy alone cannot distinguish them |

## Strict Base64 and hex decoding

These examples read local files and emit bytes without executing decoded content:

```bash
python3 - <<'PYCODE'
import base64
from pathlib import Path
raw = Path('encoded.txt').read_bytes()
compact = b''.join(raw.split())  # Only when whitespace is formatting, not data.
Path('work/base64.bin').write_bytes(base64.b64decode(compact, validate=True))
PYCODE
xxd -r -p hex.txt > work/hex.bin
file work/base64.bin work/hex.bin
```

`xxd -r -p` is permissive; use `bytes.fromhex()` on a text-only hex field when invalid characters must fail. Never run it on an entire annotated hex dump and assume every decoded byte belongs to the payload.

For URL-safe Base64, use `base64.b64decode(data, altchars=b'-_', validate=True)`. Add missing `=` padding only if the enclosing format permits omission. Keep binary output as bytes rather than forcing it through UTF-8.

## Compression wrappers

Choose the wrapper based on evidence:

```python
import gzip
import zlib

# Alternatives, not sequential operations:
# plain = gzip.decompress(blob)
# plain = zlib.decompress(blob)       # zlib header and checksum
# plain = zlib.decompress(blob, -15)  # raw DEFLATE
```

A decompression error may indicate the wrong offset, truncation, a dictionary requirement, or wrong wrapper. Inspect `decompressobj().unused_data` and `.eof` when parsing a stream embedded in a larger record. Use output-size limits for unknown compressed inputs; a tiny file can expand enormously. See [archives](../Archives-and-Passwords/README.md).

## XOR and byte order

```bash
python3 - <<'PYCODE'
from pathlib import Path
blob = Path('cipher.bin').read_bytes()
key = bytes.fromhex('1337')  # Illustrative repeating key; replace from evidence.
plain = bytes(value ^ key[i % len(key)] for i, value in enumerate(blob))
Path('work/xor.bin').write_bytes(plain)
PYCODE
```

Record whether the key repeats per file, per record, or across a continuous stream. Recover a candidate repeating key from known plaintext only after confirming alignment. Score candidates using valid structure, not printability alone.

For binary integers, specify endianness and width: `int.from_bytes(field, 'little')`, `struct.unpack('<I', field)`, or `struct.unpack('>I', field)`. Native layouts can add padding or use a host-dependent word size.

## Transformation notebook

Record input hash → slice/offset → transform → parameters → output hash. Preserve order: `reverse → Base64 → gzip` differs from `Base64 → reverse → gzip`. Stop when the result becomes a recognizable artifact and switch to its parser.

Do not treat a 32-character hex string as automatically MD5 or a 64-character string as automatically SHA-256; keys, IDs, and random bytes can have identical representations.

## References

- [RFC 4648 — Base16, Base32, Base64](https://www.rfc-editor.org/rfc/rfc4648)
- [Python Base64 interface](https://docs.python.org/3/library/base64.html)
- [Python zlib interface](https://docs.python.org/3/library/zlib.html)
- [Python binary structures](https://docs.python.org/3/library/struct.html)
