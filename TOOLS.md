# Toolbox

[Home](README.md) · [Quick reference](QUICKSTART.md)

For install commands and platform-specific sources, see [SETUP.md](SETUP.md). Each topic includes its own Tools and setup table, verification commands, and a runnable recipe linked to [the helper catalog](SCRIPTS.md).

Install only the tools needed for the artifact. Follow upstream instructions and record your version in case notes; plugins, CLI flags, and format support change. The cheatsheet assumes output directories already exist.

## Everyday command line

| Tool | Purpose | Reference |
| --- | --- | --- |
| file, xxd, strings, sha256sum, rg | Types, bytes, strings, hashing, searching | Local `man` pages / `--help` |
| 7-Zip | List and extract supported archives | [7-Zip](https://www.7-zip.org/) |
| ExifTool | Metadata and embedded information | [ExifTool](https://exiftool.org/) |
| Binwalk | Embedded-format signatures; version-dependent extraction | [Binwalk](https://github.com/ReFirmLabs/binwalk) |
| SQLite CLI | Schema inspection and working-copy queries | [SQLite CLI](https://www.sqlite.org/cli.html) |
| CyberChef | Explicit encoding/compression transformations | [CyberChef](https://github.com/gchq/CyberChef) |

## Artifact-specific tools

| Area | Tools and upstream references |
| --- | --- |
| Disk | [Sleuth Kit](https://www.sleuthkit.org/sleuthkit/), [Autopsy](https://www.autopsy.com/), [libewf](https://github.com/libyal/libewf), [cryptsetup](https://gitlab.com/cryptsetup/cryptsetup) |
| Memory | [Volatility 3](https://github.com/volatilityfoundation/volatility3), [MemProcFS](https://github.com/ufrisk/MemProcFS), [bulk_extractor](https://github.com/simsong/bulk_extractor) |
| Windows artifacts | [Eric Zimmerman tools](https://ericzimmerman.github.io/), [pypykatz](https://github.com/skelsec/pypykatz), [bmc-tools](https://github.com/ANSSI-FR/bmc-tools) |
| macOS Unified Logs | [Mandiant macos-UnifiedLogs](https://github.com/mandiant/macos-UnifiedLogs) — `unifiedlog_iterator`; [build and usage recipe](macOS-Forensics/README.md#unified-logs-with-mandiant) |
| Network | [Wireshark/TShark](https://www.wireshark.org/docs/), [Zeek](https://docs.zeek.org/) |
| Browser stores | [dfindexeddb](https://github.com/google/dfindexeddb), SQLite, a version-compatible DPAPI/application parser |
| Documents | [qpdf](https://qpdf.readthedocs.io/), [Poppler](https://poppler.freedesktop.org/), [oletools](https://github.com/decalage2/oletools) |
| Images and media | [zsteg](https://github.com/zed-0xff/zsteg), [pngcheck](https://github.com/pnggroup/pngcheck), [FFmpeg](https://ffmpeg.org/documentation.html), [SoX](https://sox.sourceforge.net/), [Pillow](https://pillow.readthedocs.io/) |
| Static code | [Ghidra](https://github.com/NationalSecurityAgency/ghidra), [ILSpy](https://github.com/icsharpcode/ILSpy), [pyinstxtractor](https://github.com/extremecoders-re/pyinstxtractor), [GDB](https://sourceware.org/gdb/documentation/) |
| Android | [JADX](https://github.com/skylot/jadx), [Apktool](https://apktool.org/), [Il2CppDumper](https://github.com/Perfare/Il2CppDumper) |
| Container layers | [Skopeo](https://github.com/containers/skopeo), [dive](https://github.com/wagoodman/dive) |
| Archive/password recovery | [bkcrack](https://github.com/kimci86/bkcrack), [John the Ripper](https://www.openwall.com/john/), [Hashcat](https://hashcat.net/hashcat/) |

## General analysis additions

| Tool | Purpose | Reference |
| --- | --- | --- |
| PhotoRec | Signature-based recovery when filesystem metadata is unavailable | [PhotoRec](https://www.cgsecurity.org/wiki/PhotoRec) |
| YARA | Structured byte/string matching with hit offsets | [YARA documentation](https://yara.readthedocs.io/) |
| Plaso / psort | Parse multiple event sources into a supertimeline | [Plaso](https://plaso.readthedocs.io/) |
| jq | Query JSON audit logs and exported records | [jq manual](https://jqlang.org/manual/) |
| steghide | Inspect/extract supported image and audio steganography | [Steghide](https://steghide.sourceforge.net/documentation.php) |
| Git | Inspect supplied repository objects, history, and unreachable content | [Git documentation](https://git-scm.com/docs) |

See [the reference library](REFERENCES.md) for standards and format documentation that explain how to interpret tool output.

## Version and execution notes

- Examples target Volatility **3**; Volatility 2 profiles and plugin syntax are different. Linux kernel symbols must match the acquisition.
- `vol`, `vol.py`, and `python3 vol.py` depend on installation. Use the entry point installed on your machine.
- Zimmerman examples run in PowerShell with the corresponding executable available locally.
- Some snippets need optional tools such as Pillow, FFmpeg, or SoX. The documentation checker needs only Python 3.9+ and its standard library.
- Tool output and decoded evidence are data. Inspect recovered scripts and executables statically instead of launching them.

## Validation scope

The local checker verifies Markdown paths, heading anchors, fenced blocks, and each topic's setup/recipe structure. The helper test suite uses synthetic fixtures; it does not install tools or reproduce source challenges. Windows EVTX integration and real-memory parsing have not been exercised here. Run recipes against your challenge evidence and record versions before claiming case-specific recovery is validated.
