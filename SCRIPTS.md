# Runnable helper scripts

[Home](README.md) · [Tool setup](SETUP.md)

Run helpers from the repository root using `python3 scripts/helpers/NAME.py --help`. Python 3.9+ is required. Activate the venv from SETUP.md when using installed Python tools. Keep inputs and generated case reports outside this repository.

Helpers are small, explicit operations rather than automatic challenge solvers. File-producing helpers use exclusive creation and refuse an existing output. Directory-producing helpers require a new directory. Shell redirection (`> report`) follows normal shell overwrite rules; choose a fresh report name. A nonzero exit can leave partial reports or output; inspect stderr and discard/review that output before continuing.

## Scripts and inputs

| Helper | Input → output | Dependencies / limits |
| --- | --- | --- |
| [inventory.py](scripts/helpers/inventory.py) | File/tree → JSONL hashes and metadata | Standard library; skips symlinks/special files; output must be outside scanned tree |
| [carve.py](scripts/helpers/carve.py) | File + byte range → carved file and hash | Standard library; range bounds checked; streams large inputs |
| [scan_bytes.py](scripts/helpers/scan_bytes.py) | File + literal/hex marker → decimal/hex offsets | Standard library; overlapping and chunk-boundary matches |
| [decode_bytes.py](scripts/helpers/decode_bytes.py) | Base64/URL-safe Base64/hex/XOR → bytes | Standard library; one layer, 64 MiB input cap, strict Base64 |
| [timestamps.py](scripts/helpers/timestamps.py) | Known epoch + integer → UTC JSON | Standard library; retains FILETIME residual ticks, no guessing |
| [zip_inventory.py](scripts/helpers/zip_inventory.py) | ZIP/APK/OOXML → member metadata JSONL | Standard library; no extraction, decompression, or password recovery |
| [browser_history.py](scripts/helpers/browser_history.py) | Copied Chromium/Firefox DB → visit JSONL | Standard library SQLite; fixed documented schemas, raw time retained |
| [wal_frames.py](scripts/helpers/wal_frames.py) | SQLite WAL → checksum-validated frame JSONL | Standard library; no snapshot replay or encrypted-WAL support |
| [email_extract.py](scripts/helpers/email_extract.py) | EML → generated attachment files and manifest | Standard library; 64 MiB input cap; nested message attachments unsupported |
| [lsb_extract.py](scripts/helpers/lsb_extract.py) | RGB/RGBA image → packed bitplane bytes | Pillow; explicit channel/bit/order, no automatic cropping or conversion |
| [hid_boot_decode.py](scripts/helpers/hid_boot_decode.py) | Hex boot-keyboard reports → keypress JSONL | Standard library; US layout subset, 8-byte reports, no report IDs/NKRO |
| [cloudtrail_summary.py](scripts/helpers/cloudtrail_summary.py) | CloudTrail Records JSON → summary JSONL | Standard library; 64 MiB input cap; no network or credentials |
| [pcap_summary.py](scripts/helpers/pcap_summary.py) | PCAP → protocol/conversation/DNS reports | TShark on PATH; optional --wireless adds 802.11/EAPOL reports |
| [memory_triage.py](scripts/helpers/memory_triage.py) | Windows memory → five reports and stderr logs | Volatility 3 executable and symbols; partial failures return nonzero |
| [evtx_export.ps1](scripts/helpers/evtx_export.ps1) | EVTX → raw XML and event metadata JSONL | Windows PowerShell/Get-WinEvent; original SystemTime retained |

## Recipes by topic

- [Methodology](Methodology/README.md#script-and-command-recipe)
- [File Triage](File-Triage/README.md#script-and-command-recipe)
- [Disk Forensics](Disk-Forensics/README.md#script-and-command-recipe)
- [Memory Forensics](Memory-Forensics/README.md#script-and-command-recipe)
- [Network Forensics](Network-Forensics/README.md#script-and-command-recipe)
- [Windows Artifacts](Windows-Artifacts/README.md#script-and-command-recipe)
- [Linux forensics](Linux-Forensics/README.md#script-and-command-recipe)
- [macOS forensics](macOS-Forensics/README.md#script-and-command-recipe)
- [Browser and Messaging](Browser-and-Messaging/README.md#script-and-command-recipe)
- [SQLite and WAL](SQLite-and-WAL/README.md#script-and-command-recipe)
- [Documents and Email](Documents-and-Email/README.md#script-and-command-recipe)
- [Steganography](Steganography/README.md#script-and-command-recipe)
- [Malware Recovery](Malware-Recovery/README.md#script-and-command-recipe)
- [Android and Firmware](Android-and-Firmware/README.md#script-and-command-recipe)
- [Logs and Timelines](Logs-and-Timelines/README.md#script-and-command-recipe)
- [USB and Peripherals](USB-and-Peripherals/README.md#script-and-command-recipe)
- [Encoding and Binary](Encoding-and-Binary/README.md#script-and-command-recipe)
- [Archives and Passwords](Archives-and-Passwords/README.md#script-and-command-recipe)
- [Search and YARA](Search-and-YARA/README.md#script-and-command-recipe)
- [Timestamps and Timelines](Timestamps-and-Timelines/README.md#script-and-command-recipe)
- [Wireless Forensics](Wireless-Forensics/README.md#script-and-command-recipe)
- [Cloud and Containers](Cloud-and-Containers/README.md#script-and-command-recipe)

## Validation

Run `python3 -m unittest discover -s tests -v`. Fixtures cover byte ranges, chunk boundaries, invalid encodings, output collisions, epochs, ZIP path metadata, browser schema errors, WAL corruption/truncation, attachment paths, HID state, and cloud optional fields. Packet and memory wrappers are tested for invocation and error propagation; real-memory correctness is owned by Volatility and the acquisition. The EVTX helper needs a separate Windows integration check.
