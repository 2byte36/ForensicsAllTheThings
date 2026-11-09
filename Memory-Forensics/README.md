# Memory forensics

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Use process relationships, mapped files, and runtime data to recover what disk artifacts no longer contain.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Windows first pass](#windows-first-pass)
- [Runtime keys and missing executables](#runtime-keys-and-missing-executables)
- [Process core dumps](#process-core-dumps)
- [Go metadata and module-relative keys](#go-metadata-and-module-relative-keys)
- [Linux memory](#linux-memory)
- [Targeted process and registry inspection](#targeted-process-and-registry-inspection)
- [Choose the acquisition path](#choose-the-acquisition-path)
- [MemProcFS and Linux MemNixFS](#memprocfs-and-linux-memnixfs)
- [User minidumps and existing Discord parser](#user-minidumps-and-existing-discord-parser)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| Volatility 3 | Memory plugins | In the Python venv: `python -m pip install volatility3`. [Source](https://github.com/volatilityfoundation/volatility3#quick-start) | `vol -h` |
| MemProcFS | Memory-backed file/process views | Install the release and platform filesystem dependency documented upstream. [Source](https://github.com/ufrisk/MemProcFS/wiki) | Run its help command for your release |
| bulk_extractor | Bulk memory/disk scanning | Use a packaged release or upstream source-build instructions. [Source](https://github.com/simsong/bulk_extractor) | `bulk_extractor -h` |
| GDB / objdump | Static core/binary inspection | `sudo apt install gdb binutils`. [Source](https://www.sourceware.org/gdb/download/) | `gdb --version`; `objdump --version` |
| WinDbg | Windows dump inspection | Install on Windows using Microsoft’s setup instructions. [Source](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/) | Open debugger Help/About |

## Script and command recipe

Use Volatility directly; the installed interactive `vol` alias already supplies the symbol cache:

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work"
vol -f "$CASE/memory.raw" windows.info > "$CASE/work/info.txt"
vol -f "$CASE/memory.raw" windows.pslist > "$CASE/work/pslist.txt"
vol -f "$CASE/memory.raw" windows.pstree > "$CASE/work/pstree.txt"
vol -f "$CASE/memory.raw" windows.cmdline > "$CASE/work/cmdline.txt"
vol -f "$CASE/memory.raw" windows.netscan > "$CASE/work/netscan.txt"
```

Inspect stderr and command status before using each report. Missing symbols or unsupported acquisitions can cause partial results. [Local aliases](../LOCAL-TOOLBOX.md#relevant-bash-aliases) explain the equivalent invocation outside interactive Bash. Optional existing wrapper: [memory_triage.py](../scripts/helpers/memory_triage.py).

## Windows first pass

Examples use the Volatility 3 `vol` entry point; some installations use `vol.py`. Check `vol -h` for installed plugins and use each plugin's `--help` for version-specific options.

```bash
vol -f memory.raw windows.info
vol -f memory.raw windows.pslist
vol -f memory.raw windows.pstree
vol -f memory.raw windows.psscan
vol -f memory.raw windows.cmdline
vol -f memory.raw windows.netscan
vol -f memory.raw windows.filescan > work/filescan.txt
rg -i '\.exe|\.pdf|\.enc' work/filescan.txt
# Example file-object virtual address from filescan:
vol -f memory.raw -o extracts windows.dumpfiles --virtaddr 0xffff800000001000
```

Compare active and scanned processes. A scanned object may be stale; its presence does not prove the process was running at acquisition time. Resolve process ancestry before selecting a dump target.

## Runtime keys and missing executables

```bash
bulk_extractor -o work/bulk memory.raw
strings -a -t x -n 8 process.dmp > work/process-strings.txt
```

Inspect generated outputs; scanners and output filenames vary by build. AES key-schedule candidates need validation against the recovered mode, IV, ciphertext layout, and file structure. They are not automatically usable keys.

**Basic** used Notepad's parent process to find malware, a registry value for the IV, and memory for the AES key. **Claudio Maximus** found Go remnants in a child `cmd.exe` dump after the original executable could not be recovered. MemProcFS can expose process dumps, registry hives, and memory-backed files as another analysis view.

## Process core dumps

```bash
file core.dump
readelf -h -l core.dump
# Inspect an ELF core without running its executable:
gdb -nx -nh -iex 'set auto-load off' -c core.dump
```

Inside GDB, use `info files`, `info proc mappings`, and `x/64bx ADDRESS`. Disable auto-loading before opening untrusted targets. An ELF core is not necessarily a Linux kernel-memory acquisition: **Ryomen Inscription** was a QEMU ELF dump containing Windows memory.

In WinDbg, inspect a matching minidump with `lm`, `!address`, `db ADDRESS L40`, `u ADDRESS`, and `.writemem output.bin START END`. Available pages depend on how the dump was captured. A virtual address is not a raw file offset; map it through dump segment descriptors.

## Go metadata and module-relative keys

For Go remnants, search for function names and candidate `pclntab` structures. Validate version, pointer size, address ranges, and function counts before resolving symbols. Use recovered names to identify actual crypto call sites.

In **Claudio Maximus**, the final call-site analysis identified AES-CTR, correcting an earlier GCM hypothesis. The key came from bytes at a module-relative offset in the captured `ntdll.dll`. That offset and module build belong to the challenge; they are not a universal key location.

## Linux memory

```bash
vol -f memory.lime banners.Banners
vol -f memory.lime linux.pslist
vol -f memory.lime linux.pstree
vol -f memory.lime linux.bash
```

Linux analysis often requires an exact matching kernel symbol table; a similar version is insufficient. Check available VMA, YARA, and injected-code plugins in your installed release. Narrow scans by process and memory range when possible.

**Incident Trace** recovered separate parts from a process heap and a C2 response buffer. **It Wrecked (Again)** followed a suspicious process's RWX mapping to encoded data remaining in memory. An RWX region is a lead, not proof by itself.

## Targeted process and registry inspection

```bash
# PID 1234 is illustrative; select a process from pslist/pstree.
vol -f memory.raw windows.dlllist --pid 1234
vol -f memory.raw windows.handles --pid 1234
vol -f memory.raw windows.vadinfo --pid 1234
vol -f memory.raw -o extracts windows.memmap --pid 1234 --dump
vol -f memory.raw windows.registry.hivelist
# Select the corresponding user hive offset from hivelist.
vol -f memory.raw windows.registry.printkey --offset 0xffff800000001000 \
  --key 'Software\Microsoft\Windows\CurrentVersion\Run'
```

Correlate executable path, command line, parent, loaded modules, handles, mapped regions, and network endpoints. Memory-mapped file content can be partial or differ from the disk file. Record missing pages instead of silently filling them and hashing the result as if complete.

For injection triage, check installed `malfind` plugins: newer releases may expose `windows.malware.malfind` alongside compatibility aliases. Inspect suspicious bytes, mapping permissions, backing files, and thread context. Legitimate JIT runtimes can generate executable private memory.

## Choose the acquisition path

| Artifact | Starting constraint |
| --- | --- |
| Full physical RAM | OS/layer detection and matching symbols |
| Process minidump/core | Only captured process regions and metadata are available |
| Hibernation or crash dump | Supported conversion/layer and potentially partial physical pages |
| Pagefile / swap alone | Fragmentary paged data; not a substitute for all RAM |
| VM memory plus metadata | Keep companion files and virtual-machine configuration |

If process plugins fail, verify acquisition format and symbols before assuming corruption. Strings and [YARA](../Search-and-YARA/README.md) can still identify leads, but cannot replace address-space reconstruction.

## MemProcFS and Linux MemNixFS

The [local toolbox](../LOCAL-TOOLBOX.md) contains both Windows MemProcFS binaries and a MemNixFS source checkout. Use [MemProcFS setup](https://github.com/ufrisk/MemProcFS/wiki) for the release's filesystem driver/runtime prerequisites and [MemNixFS build instructions](https://github.com/MemNixFS/MemNixFS/blob/main/docs/building.md) for its Windows/Linux requirements.

PowerShell, Windows memory with MemProcFS (choose a free mount letter):

```powershell
& 'C:\Users\ACER\dfir_tools\MemProcFS_files_and_binaries-win_x64-latest\MemProcFS.exe' -device 'C:\cases\memory\memory.raw' -mount M -forensic 1
```

Keep the process running while browsing the mount. Inspect the generated process/module/network/forensic views, copy selected results to the case directory, and record the source process/address. [MemProcFS command-line reference](https://github.com/ufrisk/MemProcFS/wiki/_CommandLine) describes forensic modes; the older local release may differ.

For Linux memory after installing/building MemNixFS and adding it to PATH:

```bash
memnixfs --dump memory.lime list
memnixfs --dump memory.lime cat /sys/findevil/triage.txt
memnixfs --dump memory.lime export work/memnixfs
```

This avoids requiring a mount for first-pass analysis. Inspect available exported paths rather than assuming every kernel feature was recovered. Symbol/BTF compatibility and memory coverage affect results; cached files are not a complete disk image. Source: [MemNixFS CLI](https://github.com/MemNixFS/MemNixFS/blob/main/docs/cli-reference.md).

The existing Bash `vol` alias supplies the symbol cache. In an interactive shell:

```bash
vol -f memory.raw windows.info
vol -f memory.raw windows.pslist
vol -f memory.raw windows.pstree
vol -f memory.raw windows.cmdline
vol -f memory.raw windows.netscan
```

Save outputs separately and pivot from process ancestry to the suspicious process, rather than dumping everything without context.

## User minidumps and existing Discord parser

The local `parser.exe` is **udmp-parser**, not a physical-memory Volatility plugin. Download a compatible [upstream release/build](https://github.com/0vercl0k/udmp-parser), or use the installed path listed in the toolbox. With its directory on PATH, PowerShell:

```powershell
parser.exe -mods 'C:\cases\memory\process.dmp'
parser.exe -mem 'C:\cases\memory\process.dmp'
parser.exe -t 'C:\cases\memory\process.dmp'
# Example virtual address: substitute an address present in this dump's map.
parser.exe -dump 0x7ff00000 'C:\cases\memory\process.dmp'
```

A virtual address is not a file offset. Missing pages can reflect the minidump's collection flags, not deleted data. Use the module base and memory mapping when following pointers or module-relative offsets.

The existing local `parse_discord.py` accepts a renderer dump and optional JSON output. Its public upstream is unknown; it is not copied into this repository. WSL, Python 3.10+ for its type syntax:

```bash
python3 /mnt/c/Users/ACER/dfir_tools/parse_discord.py --help
python3 /mnt/c/Users/ACER/dfir_tools/parse_discord.py \
  /absolute/path/to/case/renderer.dmp -o /absolute/path/to/case/work/discord.json
```

Review its source and output schema. A string recovered from renderer memory can be cached/stale or lack a complete message object; correlate message/channel/user IDs and source locations before claiming authorship or chronology.

## References

- [Volatility 3 Windows plugin reference](https://volatility3.readthedocs.io/en/latest/volatility3.plugins.windows.html)
- [Volatility 3 documentation](https://volatility3.readthedocs.io/)
- [MemProcFS](https://github.com/ufrisk/MemProcFS)
- [JOINTS — Claudio Maximus](https://2byte36.github.io/blog/joints-2026-quals)
- [TECHFEST quals — Basic](https://2byte36.github.io/blog/techfest-2026-quals)
- [GCW quals — Ryomen Inscription](https://2byte36.github.io/blog/gcw-2026-quals)
- [NCLP — Incident Trace](https://2byte36.github.io/blog/nclp-ctf-s1)
- [Wreck-IT — It Wrecked (Again)](https://2byte36.github.io/blog/wreck-it-7-quals)
