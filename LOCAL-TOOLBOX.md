# Maintainer's forensic toolbox

[Home](README.md) · [Portable setup](SETUP.md) · [Tool catalog](TOOLS.md)

Inventory reviewed on **2026-11-09** from `C:\Users\ACER\dfir_tools`, `~/ctf-tools`, and the interactive Bash aliases. This page maps existing tools to direct recipes. Paths are examples of the maintainer's installation; substitute your own tool root. Installed folders do not imply every tool/version was tested.

## Windows tools already present

| Local path below `C:\Users\ACER\dfir_tools` | Use / upstream | Recipe |
| --- | --- | --- |
| `RegistryExplorer\RegistryExplorer.exe` | [Registry Explorer](https://ericzimmerman.github.io/): offline hives, logs, bookmarks/plugins | [Registry](Windows-Registry/README.md) |
| `userassist_parser.py` | [Awad93 UserAssist parser](https://github.com/Awad93/Userassist_parser): program/focus/session fields; Python + python-registry | [Registry recipe](Windows-Registry/README.md#script-and-command-recipe) |
| `EvtxeCmd\EvtxECmd.exe` | [EvtxECmd](https://github.com/EricZimmerman/evtx): EVTX exports/maps | [Event logs](Windows-Event-Logs/README.md) |
| `MFTECmd\MFTECmd.exe` | [MFTECmd](https://github.com/EricZimmerman/MFTECmd): NTFS metadata | [MFT and USN](NTFS-Forensics/README.md) |
| `PECmd\PECmd.exe` | [PECmd](https://github.com/EricZimmerman/PECmd): Prefetch | [Execution](Windows-Execution/README.md) |
| `TimelineExplorer\TimelineExplorer\TimelineExplorer.exe` | [Timeline Explorer](https://ericzimmerman.github.io/): filter/sort exported CSV | [Event workflow](Windows-Event-Logs/README.md#script-and-command-recipe) |
| `chromecacheview\ChromeCacheView.exe` | [NirSoft ChromeCacheView](https://www.nirsoft.net/utils/chrome_cache_view.html): cache list/export | [Browser cache](Browser-and-Messaging/README.md#cache-downloads-and-clickfix) |
| `MemProcFS_files_and_binaries-win_x64-latest\MemProcFS.exe` | [MemProcFS](https://github.com/ufrisk/MemProcFS): Windows memory as a filesystem; a separate v5.9.8 folder is also present | [Memory](Memory-Forensics/README.md#memprocfs-and-linux-memnixfs) |
| `MemNixFS` | [MemNixFS](https://github.com/MemNixFS/MemNixFS): Linux memory; source checkout, follow build docs for binary path | [Memory](Memory-Forensics/README.md#memprocfs-and-linux-memnixfs) |
| `macos-UnifiedLogs` | [Mandiant macos-UnifiedLogs](https://github.com/mandiant/macos-UnifiedLogs): tracev3/logarchive | [macOS](macOS-Forensics/README.md#unified-logs-with-mandiant) |
| `ghidra_12.1.4_PUBLIC_20260921\ghidra_12.1.4_PUBLIC` | [Ghidra](https://github.com/NationalSecurityAgency/ghidra): static native-code analysis | [Malware recovery](Malware-Recovery/README.md) |
| `pycdc`, `pylingual` | [pycdc](https://github.com/zrax/pycdc), [PyLingual](https://github.com/syssec-utd/pylingual): bytecode disassembly/decompilation | [Python payloads](Malware-Recovery/README.md#python-bytecode-and-pyarmor-with-existing-tools) |
| `pyarmor-1shot-v0.4.0-windows-x86_64` | [Pyarmor Static Unpack 1shot](https://github.com/Lil-House/Pyarmor-Static-Unpack-1shot): static unpacking with matching runtime | [Python payloads](Malware-Recovery/README.md#python-bytecode-and-pyarmor-with-existing-tools) |
| `parser-windows-2025.msvc-x64.RelWithDebInfo-f49c33d97563567328bec0afa8491657e625a877\bin\parser.exe` | [udmp-parser](https://github.com/0vercl0k/udmp-parser): user minidump inspection; identified from included header author/library | [Minidumps](Memory-Forensics/README.md#user-minidumps-and-existing-discord-parser) |
| `parse_discord.py` | Existing local renderer-dump parser; no public upstream established | [Discord memory](Memory-Forensics/README.md#user-minidumps-and-existing-discord-parser) |

Installed CLI help was checked successfully for **EvtxECmd 1.5.2.0**, **MFTECmd 2026.5.0**, and **PECmd 2026.5.0**. Recipes use their supported flags. The local UserAssist script also matched its linked upstream source text. Current upstream releases can differ; record the binary/version actually used for each case.

## Relevant Bash aliases

These are the selected forensic aliases, not a dump of the shell configuration:

```bash
alias vol='vol -s $HOME/.cache/volatility3/symbols'
alias bmc-tools='python3 ~/ctf-tools/bmc-tools/bmc-tools.py'
alias usb-keyboard-parser='python3 ~/ctf-tools/CTF-Usb_Keyboard_Parser/main.py'
alias nest-extract='python3 ~/ctf-tools/nest_extract.py'
```

Aliases expand in interactive Bash; scripts and other shells may not load them. Use the explicit command when reproducing a recipe:

```bash
vol -s "$HOME/.cache/volatility3/symbols" -f /absolute/path/to/memory.raw windows.info
python3 "$HOME/ctf-tools/bmc-tools/bmc-tools.py" -h
python3 "$HOME/ctf-tools/CTF-Usb_Keyboard_Parser/main.py" /absolute/path/to/usb.pcapng
python3 "$HOME/ctf-tools/nest_extract.py" --help
```

The explicit `vol -s` invocation is intended for a shell without the alias; in your interactive shell use `vol -f ...` to avoid repeating `-s`. Check selected aliases with `alias vol bmc-tools usb-keyboard-parser nest-extract` and the underlying executable with `type -a vol`.

## Tools in the mixed CTF directory

| Folder/script under `~/ctf-tools` | Forensic use | Setup source / recipe |
| --- | --- | --- |
| `bmc-tools` | RDP bitmap cache recovery | [Upstream](https://github.com/ANSSI-FR/bmc-tools), [Windows recipe](Windows-Artifacts/README.md#rdp-cache-and-execution-chains) |
| `CTF-Usb_Keyboard_Parser` | Device-separated keyboard decoding from PCAP/PCAPNG | [Upstream](https://github.com/shark-asmx/CTF-Usb_Keyboard_Parser), [USB recipe](USB-and-Peripherals/README.md#existing-usb-keyboard-parser) |
| `bkcrack` | Legacy ZipCrypto known-plaintext recovery | [Build/install](https://github.com/kimci86/bkcrack#install), [archive guide](Archives-and-Passwords/README.md) |
| `cupp` | Small CTF clue-based password candidate list | [Upstream](https://github.com/Mebus/cupp), [archive recipe](Archives-and-Passwords/README.md#existing-nested-extractor-and-cupp) |
| `AperiSolve` | Combined image steganalysis interface | [Self-host setup](https://github.com/Zeecka/AperiSolve), [media guide](Steganography/README.md#aperisolve-and-multiple-image-fragments) |
| `nest_extract.py` | Existing local nested-archive script | No public upstream established; [observed CLI and limits](Archives-and-Passwords/README.md#existing-nested-extractor-and-cupp) |

JWT brute-force tooling and navigation/service-management aliases are outside these forensic workflows. Local scripts without verified public upstream are marked as such; this repository does not redistribute them or invent installation URLs.

## PowerShell versus WSL paths

PowerShell:

```powershell
$DfirTools = 'C:\Users\ACER\dfir_tools'
& "$DfirTools\MFTECmd\MFTECmd.exe" -h
```

WSL, calling the same Windows executable:

```bash
DFIR_TOOLS=/mnt/c/Users/ACER/dfir_tools
"$DFIR_TOOLS/MFTECmd/MFTECmd.exe" -h
# Input/output arguments to Windows programs must be Windows paths.
"$DFIR_TOOLS/MFTECmd/MFTECmd.exe" \
  -f "$(wslpath -w /mnt/c/cases/ntfs/artifacts/\$MFT)" \
  --csv "$(wslpath -w /mnt/c/cases/ntfs/reports)"
```

A Windows executable's location can use a WSL path while its data arguments still need Windows syntax. Create the case/report folders beforehand. Keep tool installations separate from evidence and reports.
