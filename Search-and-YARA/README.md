# Evidence search and YARA

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Search extracted data with explicit encodings and preserve offsets so every hit can be checked in context.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Text, binary, and UTF-16 searches](#text-binary-and-utf-16-searches)
- [Write a focused YARA rule](#write-a-focused-yara-rule)
- [Control false positives](#control-false-positives)
- [Translate offsets correctly](#translate-offsets-correctly)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| file / strings / xxd / rg | Type, bytes, and string triage | `sudo apt install file binutils xxd ripgrep coreutils`. [Source](https://github.com/BurntSushi/ripgrep#installation) | `file --version`; `rg --version` |
| YARA | Byte-pattern rules | `sudo apt install yara`. [Source](https://yara.readthedocs.io/en/stable/gettingstarted.html) | `yara --version` |

## Script and command recipe

Helper: [scan_bytes.py](../scripts/helpers/scan_bytes.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/scan_bytes.py "$CASE/artifact.bin" --text "CTF{" > "$CASE/work/marker-offsets.tsv"
python3 scripts/helpers/scan_bytes.py "$CASE/artifact.bin" --hex 4354467b
```

Prints decimal and hexadecimal file offsets, preserving overlapping and chunk-boundary matches. Uses bounded buffers rather than loading the artifact into RAM. A hit is a marker match, not a validated flag.

## Text, binary, and UTF-16 searches

```bash
rg -n -i --glob '*.log' 'password|token|download' extracts/
rg -a -n -F 'CTF{' artifact.bin
strings -a -t x -n 6 artifact.bin > work/ascii-offsets.txt
strings -a -el -t x artifact.bin > work/utf16le-offsets.txt
```

`rg -n` reports line numbers, not binary offsets. `strings -t x` reports byte offsets for the beginning of each extracted string. Confirm actual bytes at the hit and account for compressed or encoded layers.

For exact marker offsets, including overlaps:

```bash
python3 - <<'PYCODE'
from pathlib import Path
blob = Path('artifact.bin').read_bytes()  # For modest-sized artifacts.
needle = b'CTF{'
position = blob.find(needle)
while position != -1:
    print(hex(position), repr(blob[position:position + 80]))
    position = blob.find(needle, position + 1)
PYCODE
```

For large images, use a streaming/memory-mapped scanner rather than reading the whole image into RAM. Preserve an overlap of at least the longest pattern minus one byte between chunks.

## Write a focused YARA rule

Save as `work/markers.yar`:

```yara
rule ctf_artifact_markers
{
    meta:
        purpose = "Triage markers only; not malware attribution"
    strings:
        $flag = "CTF{" ascii wide
        $config = "device_cfg=" ascii
        $tag = { 4B 45 59 49 54 45 4D 31 }
    condition:
        any of them
}
```

```bash
yara -s work/markers.yar artifact.bin
yara -r -s work/markers.yar extracts/
```

Replace markers with strings justified by your challenge. `ascii wide` covers ordinary bytes and YARA's interleaved-NUL representation; it is not a general Unicode decoder. Hex patterns can constrain binary structure and allow wildcards where fields vary.

## Control false positives

Combine independent markers, size ranges, file headers, and expected offsets when appropriate. A flag-shaped string can be a decoy, source-code constant, or stale memory. A positive rule means its condition matched, not that the file is malicious or the flag is correct.

For family identification, prefer several distinctive features over generic words such as `password`. Avoid huge regular expressions and broad wildcard patterns over full disk images without a reason.

## Translate offsets correctly

A disk-file offset, carved-file offset, process virtual address, and physical-memory offset are different coordinate systems. Add the carve's base offset when returning to the original artifact. For process scans, use the dump's mapping metadata; never add a virtual base to a raw file offset blindly.

See [memory analysis](../Memory-Forensics/README.md) for process-oriented scans and [file triage](../File-Triage/README.md) for carving around validated markers.

## References

- [YARA rule syntax](https://yara.readthedocs.io/en/stable/writingrules.html)
- [YARA command line](https://yara.readthedocs.io/en/stable/commandline.html)
- [ripgrep guide](https://github.com/BurntSushi/ripgrep/blob/master/GUIDE.md)
- [GNU strings](https://sourceware.org/binutils/docs/binutils/strings.html)
