# ForensicsAllTheThings

**Find the artifact. Recover the evidence. Understand the technique.**

A general digital forensics cheatsheet for CTFs and artifact investigation, maintained by [2byte](https://2byte36.github.io/blog/). Organized by artifact and technique, with copyable commands, recovery workflows, format notes, and common pitfalls.

Inspired by the topic-per-directory structure of [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings). This independent project combines primary tool documentation, file-format specifications, general forensic practice, and worked CTF examples. Recipes are designed to stand on their own; personal writeups provide additional case studies.

## Start here

- [Tool setup](SETUP.md) — install commands, platform notes, and upstream installation sources.
- [Runnable scripts](SCRIPTS.md) — reusable helpers with explicit inputs and limitations.
- [Quick reference](QUICKSTART.md) — choose a starting point from the file in front of you.
- [Investigation methodology](Methodology/README.md) — triage, timelines, and sequential Q&A.
- [Reference library](REFERENCES.md) — primary documentation and specifications by subject.
- [Worked examples](WRITEUPS.md) — challenge writeups illustrating the techniques.
- [Toolbox](TOOLS.md) — tools, purposes, and upstream documentation.

## Topics

| Topic | Reach for it when you have… |
| --- | --- |
| [File triage and carving](File-Triage/README.md) | Unknown files, archives, broken signatures, fragmented files |
| [Disk and filesystem](Disk-Forensics/README.md) | DD/IMG, AD1, E01, VMDK, deleted files, LUKS, extended attributes |
| [Memory forensics](Memory-Forensics/README.md) | Windows/Linux RAM, process dumps, injected code, runtime keys |
| [Network forensics](Network-Forensics/README.md) | PCAP/PCAPNG, HTTP, DNS, ICMP, TLS, MQTT, exfiltration |
| [Windows artifacts](Windows-Artifacts/README.md) | EVTX, registry, Prefetch, MFT/USN, DPAPI, RDP caches |
| [Linux forensics](Linux-Forensics/README.md) | Auth logs, systemd/cron persistence, shell history, container layers |
| [macOS forensics](macOS-Forensics/README.md) | Property lists, launch agents/daemons, keychains, unified logs |
| [Browser and messaging](Browser-and-Messaging/README.md) | Chromium profiles, downloads, Signal, Outlook, encrypted stores |
| [SQLite and WAL](SQLite-and-WAL/README.md) | Deleted rows, old database states, uncommitted transactions |
| [Documents and email](Documents-and-Email/README.md) | PDF, DOCX/DOCM, EML, macros, misleading redaction |
| [Steganography and media](Steganography/README.md) | Images, bitplanes, video frames, audio, SSTV, hidden streams |
| [Malware and ransomware recovery](Malware-Recovery/README.md) | Obfuscated scripts, .NET/Go/Python binaries, encrypted files |
| [Android and firmware](Android-and-Firmware/README.md) | Android dumps/APKs, Unity IL2CPP, ESP32 flash |
| [Logs and timelines](Logs-and-Timelines/README.md) | Web logs, blind SQLi traces, fragmented requests, incident sequencing |
| [USB and peripheral captures](USB-and-Peripherals/README.md) | HID keyboard reports, Linux input events, raw display data |
| [Encoding and binary transformations](Encoding-and-Binary/README.md) | Base64, hex, compression, XOR, endianness, layered data |
| [Archives and passwords](Archives-and-Passwords/README.md) | ZIP/7z/RAR, split archives, damage, password verifiers, known plaintext |
| [Search and YARA](Search-and-YARA/README.md) | Exact markers, UTF-16 strings, binary patterns, offset-aware searches |
| [Timestamps and timelines](Timestamps-and-Timelines/README.md) | FILETIME, Unix/browser epochs, timezones, clock skew, Plaso |
| [Wireless captures](Wireless-Forensics/README.md) | Raw 802.11, SSIDs/BSSIDs, handshakes, decryption prerequisites |
| [Cloud and containers](Cloud-and-Containers/README.md) | Audit exports, OCI/Docker layers, Git history, CI logs |

## Use it during a CTF

Open the topic matching your artifact, run its first-pass commands, then follow the evidence to the next topic. Code examples assume a Linux analysis environment unless marked PowerShell or debugger. Replace example paths, PIDs, offsets, and field names with values from your case. Create output folders before exporting.

Search the checkout with ripgrep:

```bash
rg -n -i 'wal|dpapi|luks|icmp|pclntab' --glob '*.md'
```

Copy [the case notes template](templates/case-notes.md) into your own case directory. Keep challenge evidence and generated output outside this reference repository.

## Sources and scope

Coverage follows common forensic artifacts and questions, not a single event or author's solve history. The [reference library](REFERENCES.md) points to upstream manuals and format specifications. Topic pages cite those sources and link relevant case studies.

The [writeup index](WRITEUPS.md) currently catalogs 25 posts from 2byte's blog as an initial example collection; it is not the boundary of the cheatsheet. Challenge outcomes remain source-reported, and original challenge artifacts were not rerun. Commands are starting points with stated prerequisites and version limitations.

Use extracted scripts and binaries as evidence: inspect and decode them statically. Do not execute a recovered loader to see what it does. Old challenge addresses and malware URLs are not required to use this cheatsheet.

## Maintain the cheatsheet

See [CONTRIBUTING.md](CONTRIBUTING.md) and the [topic template](templates/topic.md). Validate local links and structure with:

```bash
python3 scripts/check_docs.py
python3 -m unittest discover -s tests -v
```

The repository is Markdown-first: no build, hosting account, or deployment is needed to read it.
