# Tool setup

[Home](README.md) · [Toolbox](TOOLS.md) · [Runnable scripts](SCRIPTS.md)

Each topic has a Tools and setup table and a runnable recipe. Start with [the installed toolbox](LOCAL-TOOLBOX.md) to reuse existing tools and aliases; direct upstream commands are preferred over new custom helpers. This page covers the common environment. These are installation instructions, not an installer that has been run on your machine. Package availability and tool runtimes vary by OS release; follow the linked upstream instructions when they differ.

## Linux and WSL baseline

Commands target Debian/Ubuntu-family environments. They install analysis tools into the analysis system, not the evidence image:

```bash
sudo apt update
sudo apt install python3 python3-venv file binutils coreutils xxd ripgrep git
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Run this from the repository root, or create a dedicated analysis venv elsewhere. The repository's Python helpers require Python 3.9+; third-party tools may require newer versions. Windows users can use WSL for Linux commands and native Windows tools for EVTX/debugging. Do not mix Windows paths with Linux examples without translating them.

## Python tools

Activate the venv before these optional installs; choose the subset you need:

```bash
python -m pip install Pillow
python -m pip install volatility3 oletools pypykatz
python -m pip freeze > /tmp/forensics-python-versions.txt
```

Only the image-bitplane helper requires Pillow. All other repository Python helpers use the standard library, although packet and memory wrappers call TShark and Volatility externally. Upstream packages have their own native libraries and symbol requirements. Plaso, MemProcFS, and Ghidra are not installed by the commands above.

## Executable and platform notes

- Some distributions ship standalone 7-Zip as `7zz`; older ones use `7z` from a different package. Check `command -v 7z` and `command -v 7zz`, then substitute the installed executable in recipes.
- A minimal distro John package may lack Jumbo helpers. Use John Jumbo when a recipe needs `zip2john`, `pdf2john`, or other format converters, and locate them in its `run` directory.
- Volatility's entry point may be `vol`, `vol.py`, or a source checkout invoked with Python. The memory helper accepts `--vol /path/to/executable` for a single executable path.
- TShark is used for offline files; packet-capture privileges are not needed for these recipes.
- zsteg uses Ruby gems. After `gem install --user-install zsteg`, locate the user gem bin directory with `ruby -e 'puts Gem.user_dir'` and add its `bin` subdirectory to PATH.
- WinDbg, Registry Explorer, Timeline Explorer, and Get-WinEvent recipes here use Windows. Some current Zimmerman CLI builds also support `dotnet TOOL.dll` on Linux/macOS; consult that release's runtime requirements. Linux PowerShell does not provide Windows Get-WinEvent EVTX support.
- For release ZIPs, unpack into a dedicated tools directory, install documented prerequisites, and add the executable directory to PATH. Prefer versioned releases; record the actual version used in your case notes.

## Upstream installation catalog

The sources below are project-maintained installation/download pages or repositories. Where no stable package command is portable, follow the release's own instructions.

| Tool | Install / setup | Official source | Verify |
| --- | --- | --- | --- |
| Python 3 | `sudo apt install python3 python3-venv` | [Installation/source](https://www.python.org/downloads/) | `python3 --version` |
| file / strings / xxd / rg | `sudo apt install file binutils xxd ripgrep coreutils` | [Installation/source](https://github.com/BurntSushi/ripgrep#installation) | `file --version`; `rg --version` |
| 7-Zip | `sudo apt install 7zip` (see executable-name note below) | [Installation/source](https://www.7-zip.org/download.html) | `7z i` or `7zz i` |
| ExifTool | `sudo apt install libimage-exiftool-perl` | [Installation/source](https://exiftool.org/install.html) | `exiftool -ver` |
| Binwalk | `sudo apt install binwalk`; use upstream build for a newer major version | [Installation/source](https://github.com/ReFirmLabs/binwalk#installation) | `binwalk --help` |
| Sleuth Kit | `sudo apt install sleuthkit` | [Installation/source](https://www.sleuthkit.org/sleuthkit/download.php) | `mmls -V` |
| PhotoRec / TestDisk | `sudo apt install testdisk` | [Installation/source](https://www.cgsecurity.org/wiki/TestDisk_Download) | `photorec /version` |
| libewf utilities | `sudo apt install ewf-tools` | [Installation/source](https://github.com/libyal/libewf/wiki/Building) | `ewfinfo -V` |
| cryptsetup | `sudo apt install cryptsetup` | [Installation/source](https://gitlab.com/cryptsetup/cryptsetup) | `cryptsetup --version` |
| Autopsy | Download the platform release and follow its prerequisites | [Installation/source](https://www.autopsy.com/download/) | Open Help/About |
| Volatility 3 | In the Python venv: `python -m pip install volatility3` | [Installation/source](https://github.com/volatilityfoundation/volatility3#quick-start) | `vol -h` |
| MemProcFS | Install the release and platform filesystem dependency documented upstream | [Installation/source](https://github.com/ufrisk/MemProcFS/wiki) | Run its help command for your release |
| bulk_extractor | Use a packaged release or upstream source-build instructions | [Installation/source](https://github.com/simsong/bulk_extractor) | `bulk_extractor -h` |
| GDB / objdump | `sudo apt install gdb binutils` | [Installation/source](https://www.sourceware.org/gdb/download/) | `gdb --version`; `objdump --version` |
| WinDbg | Install on Windows using Microsoft’s setup instructions | [Installation/source](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/) | Open debugger Help/About |
| Wireshark / TShark | `sudo apt install tshark`; desktop installer available upstream | [Installation/source](https://www.wireshark.org/download.html) | `tshark --version` |
| Mandiant macos-UnifiedLogs | Download a compatible release or build the `examples` workspace with Rust/Cargo; see [the macOS recipe](macOS-Forensics/README.md#unified-logs-with-mandiant) | [Build instructions](https://github.com/mandiant/macos-UnifiedLogs/blob/main/BUILDING.md), [releases](https://github.com/mandiant/macos-UnifiedLogs/releases) | `unifiedlog_iterator --help`; `unifiedlog_iterator --version` |
| Zeek | Use official packages for your distribution or the documented build | [Installation/source](https://docs.zeek.org/en/current/install.html) | `zeek --version` |
| jq | `sudo apt install jq` | [Installation/source](https://jqlang.org/download/) | `jq --version` |
| Zimmerman tools | Windows: download Get-ZimmermanTools, inspect it, then run with `-Dest` as documented; install the matching .NET runtime | [Installation/source](https://ericzimmerman.github.io/) | Run the selected executable with `-h` |
| RECmd / rla | Download release ZIPs, keep Plugins/BatchExamples with RECmd, install matching .NET; see [registry recipe](Windows-Registry/README.md) | [Installation/source](https://github.com/EricZimmerman/RECmd) | `RECmd.exe -h`; `rla.exe -h` |
| UserAssist parser | Clone Awad93/Userassist_parser; in a venv run `python -m pip install python-registry` | [Installation/source](https://github.com/Awad93/Userassist_parser) | `python userassist_parser.py -h` |
| AmcacheParser / LECmd / JLECmd / RBCmd | Optional Zimmerman releases; keep each tool's runtime dependencies | [Installation/source](https://ericzimmerman.github.io/) | Run the selected executable with `-h` |
| ChromeCacheView | Windows ZIP from NirSoft, unpack and choose the acquired cache folder | [Installation/source](https://www.nirsoft.net/utils/chrome_cache_view.html) | Open File → Select Cache Folder |
| MemNixFS | Download/build for the analysis host; WinFsp (Windows) or FUSE (Linux) for mounts; `cat`/`export` work without a mount | [Build/source](https://github.com/MemNixFS/MemNixFS/blob/main/docs/building.md) | `memnixfs --help` |
| udmp-parser | Download a platform release or follow the CMake build | [Installation/source](https://github.com/0vercl0k/udmp-parser) | `parser.exe -h` |
| CTF USB Keyboard Parser | `git clone https://github.com/shark-asmx/CTF-Usb_Keyboard_Parser.git`; Python 3 | [Installation/source](https://github.com/shark-asmx/CTF-Usb_Keyboard_Parser) | Run `python3 main.py` for usage |
| libpff / pff-tools | `sudo apt install pff-tools` where available; otherwise upstream build | [Installation/source](https://github.com/libyal/libpff/wiki/Building) | `pffinfo -h`; `pffexport -h` |
| pycdc / pycdas | Clone zrax/pycdc; `cmake -S . -B build` then `cmake --build build`; add build directory to PATH | [Installation/source](https://github.com/zrax/pycdc) | `pycdc --help`; `pycdas --help` |
| PyLingual | Install uv; clone syssec-utd/pylingual; `uv tool install ./pylingual` | [Installation/source](https://github.com/syssec-utd/pylingual) | `pylingual --help` |
| Pyarmor Static Unpack 1shot | Download platform release; keep shot.py and executable together | [Installation/source](https://github.com/Lil-House/Pyarmor-Static-Unpack-1shot) | `python oneshot/shot.py --help` |
| CUPP | Clone Mebus/cupp; Python 3 | [Installation/source](https://github.com/Mebus/cupp) | `python3 cupp.py -h` |
| AperiSolve | Clone Zeecka/AperiSolve; install Docker/Compose; `docker compose up -d` in checkout | [Installation/source](https://github.com/Zeecka/AperiSolve) | `docker compose ps` |
| pypykatz | In the Python venv: `python -m pip install pypykatz` | [Installation/source](https://github.com/skelsec/pypykatz#installation) | `pypykatz --help` |
| bmc-tools | Clone the upstream source and use its Python CLI | [Installation/source](https://github.com/ANSSI-FR/bmc-tools) | `python3 bmc-tools.py -h` |
| SQLite CLI | `sudo apt install sqlite3` | [Installation/source](https://www.sqlite.org/download.html) | `sqlite3 --version` |
| dfindexeddb | Follow the project installation instructions in a separate venv | [Installation/source](https://github.com/google/dfindexeddb#installation) | Use the installed CLI help listed upstream |
| qpdf | `sudo apt install qpdf` | [Installation/source](https://qpdf.readthedocs.io/en/stable/installation.html) | `qpdf --version` |
| Poppler utilities | `sudo apt install poppler-utils` | [Installation/source](https://poppler.freedesktop.org/) | `pdfinfo -v` |
| oletools | In the Python venv: `python -m pip install oletools` | [Installation/source](https://github.com/decalage2/oletools/wiki/Install) | `olevba --help` |
| Pillow | In the Python venv: `python -m pip install Pillow` | [Installation/source](https://pillow.readthedocs.io/en/stable/installation/basic-installation.html) | `python -m PIL` |
| FFmpeg / SoX / pngcheck | `sudo apt install ffmpeg sox pngcheck` | [Installation/source](https://ffmpeg.org/download.html) | `ffmpeg -version`; `sox --version`; `pngcheck -h` |
| zsteg | Install Ruby, then `gem install --user-install zsteg`; add the gem executable directory to PATH | [Installation/source](https://github.com/zed-0xff/zsteg#installation) | `zsteg --help` |
| steghide | `sudo apt install steghide` | [Installation/source](https://steghide.sourceforge.net/download.php) | `steghide --version` |
| Ghidra | Download the release and use the JDK required by that release’s installation guide | [Installation/source](https://github.com/NationalSecurityAgency/ghidra#install) | Open Help/About |
| ILSpy | Download desktop release or install its CLI with the documented .NET SDK | [Installation/source](https://github.com/icsharpcode/ILSpy#downloads) | Open About or `ilspycmd --help` |
| pyinstxtractor | Clone the upstream script; read its Python-version compatibility notes | [Installation/source](https://github.com/extremecoders-re/pyinstxtractor) | Run the script without a sample to display usage |
| JADX | Download release ZIP; install required Java and add its bin directory to PATH | [Installation/source](https://github.com/skylot/jadx#download) | `jadx --version` |
| Apktool | Install Java plus the platform wrapper and JAR from the official guide | [Installation/source](https://apktool.org/docs/install/) | `apktool --version` |
| Il2CppDumper | Download a compatible release and follow its platform/runtime instructions | [Installation/source](https://github.com/Perfare/Il2CppDumper#usage) | Run its usage/help entry point |
| Plaso / psort | Use a supported packaged release per upstream guidance; avoid assuming a plain pip install includes native dependencies | [Installation/source](https://plaso.readthedocs.io/en/latest/sources/user/Users-Guide.html) | `log2timeline.py --version`; `psort.py --help` |
| YARA | `sudo apt install yara` | [Installation/source](https://yara.readthedocs.io/en/stable/gettingstarted.html) | `yara --version` |
| Git | `sudo apt install git` | [Installation/source](https://git-scm.com/downloads) | `git --version` |
| Skopeo | `sudo apt install skopeo` | [Installation/source](https://github.com/containers/skopeo/blob/main/install.md) | `skopeo --version` |
| dive | Download a platform release/package using upstream installation instructions | [Installation/source](https://github.com/wagoodman/dive#installation) | `dive --version` |
| John Jumbo | Install Jumbo from upstream; a minimal distro John may omit zip2john and other helpers | [Installation/source](https://github.com/openwall/john/blob/bleeding-jumbo/doc/INSTALL) | `john --list=build-info` |
| Hashcat | Download a release and install the backend/runtime appropriate for your hardware | [Installation/source](https://hashcat.net/hashcat/) | `hashcat --version`; `hashcat -I` |
| bkcrack | Use upstream release binaries or its CMake build instructions | [Installation/source](https://github.com/kimci86/bkcrack#install) | `bkcrack -h` |

## Check the repository helpers

```bash
python3 scripts/check_docs.py
python3 -m unittest discover -s tests -v
python3 scripts/helpers/carve.py --help
```

Tests use temporary synthetic files. They do not install third-party tools, run malware, or reproduce original CTF challenges. Optional image/packet checks skip when their dependencies are absent. Windows EVTX integration and real memory-image parsing require their respective platforms and evidence.
