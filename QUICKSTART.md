# CTF quick reference

[Home](README.md) · [Toolbox](TOOLS.md) · [Case notes](templates/case-notes.md)

Missing a command? Follow [tool setup](SETUP.md). For ready-to-run operations, use [the helper catalog](SCRIPTS.md) or the Script and command recipe section in each topic.

## First five minutes

```bash
mkdir -p work extracts carved
sha256sum evidence.bin | tee work/evidence.sha256
file -k evidence.bin
xxd -l 128 evidence.bin
strings -a -n 6 evidence.bin > work/strings.txt
strings -a -el evidence.bin > work/strings-utf16le.txt
rg -n -i 'flag|ctf|password|secret|https?://' work/strings*.txt
7z l evidence.bin
```

An archive-listing error may simply mean this is not an archive. File extensions and visible strings are clues; confirm the underlying structure. Record offsets and surrounding context for any candidate flag.

## Route by artifact

| Artifact or clue | First useful action | Next guide |
| --- | --- | --- |
| Unknown blob | `file`, `xxd`, `7z l`, `binwalk` | [File triage](File-Triage/README.md) |
| Disk image | `mmls image.dd`; inspect partitions | [Disk](Disk-Forensics/README.md) |
| AD1 / E01 / virtual disk | Open with a supporting image parser | [Disk](Disk-Forensics/README.md) |
| Windows RAM | `vol -f memory.raw windows.info` | [Memory](Memory-Forensics/README.md) |
| ELF / process core | `readelf -h -l core.dump` | [Memory](Memory-Forensics/README.md#process-core-dumps) |
| PCAP / PCAPNG | `tshark -r capture.pcapng -q -z io,phs` | [Network](Network-Forensics/README.md) |
| EVTX / registry / Prefetch | Parse the relevant artifact and correlate time | [Windows](Windows-Artifacts/README.md) |
| Database + WAL | Preserve the database and sidecars before opening | [SQLite](SQLite-and-WAL/README.md) |
| Browser / chat profile | Identify the user and actual profile directory | [Browser](Browser-and-Messaging/README.md) |
| PDF / Office / email | `exiftool`, `pdftotext`, `7z l`, `olevba` | [Documents](Documents-and-Email/README.md) |
| Image / audio / video | Metadata, structure, channels, spectrogram | [Steganography](Steganography/README.md) |
| Encrypted file + suspicious code | Recover exact format, key derivation, mode | [Recovery](Malware-Recovery/README.md) |
| APK / phone / flash | Package data, configuration, static code | [Android](Android-and-Firmware/README.md) |
| USB / custom traffic | Identify descriptors, report layout, framing | [Peripherals](USB-and-Peripherals/README.md) |

## General technique shortcuts

| Need | Guide |
| --- | --- |
| Decode Base64, hex, XOR, compressed streams | [Encoding and binary](Encoding-and-Binary/README.md) |
| Inspect or repair an archive; recover its password | [Archives and passwords](Archives-and-Passwords/README.md) |
| Search exact bytes, UTF-16, or structured patterns | [Search and YARA](Search-and-YARA/README.md) |
| Convert FILETIME/browser epochs or build a timeline | [Timestamps](Timestamps-and-Timelines/README.md) |
| Interpret raw wireless frames or handshake material | [Wireless](Wireless-Forensics/README.md) |
| Trace cloud actions, old container layers, or commits | [Cloud and containers](Cloud-and-Containers/README.md) |

## High-value pivots

- **File absent from disk?** Try deleted entries, memory file objects, process mappings, old WAL frames, or older container layers.
- **Key absent from code?** Look for environment values, registry data, xattrs, timestamps, runtime buffers, or module-relative bytes.
- **Looks like noise?** Verify framing, compression, encoding order, channel selection, and fragment order before brute force.
- **Parser says corrupt?** Verify format and acquisition type, then inspect structure. A minidump is not a full physical-memory image.
- **Decryption looks plausible?** Check the format parser, expected length, padding, checksum, or authentication tag.
- **Question asks for exact time?** Preserve source time, timezone, precision, and normalized UTC separately.

## Before submitting

Record the exact question, artifact path, command, decisive output, and exact answer string. Check case, separators, timezone, and whether the expected path is on the host or inside a container. See [methodology](Methodology/README.md).
