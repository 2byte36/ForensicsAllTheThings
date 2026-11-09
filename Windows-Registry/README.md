# Windows Registry forensics

[Home](../README.md) · [Windows overview](../Windows-Artifacts/README.md) · [Execution](../Windows-Execution/README.md)

Start with Registry Explorer for an individual hive, then use RECmd for repeatable searches and batch exports. Paths below are **relative to the named hive**, unless they explicitly start with HKLM/HKCU. Work on copies with their matching transaction logs.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Hive and acquisition map](#hive-and-acquisition-map)
- [Identity and control sets](#identity-and-control-sets)
- [User activity and execution](#user-activity-and-execution)
- [Persistence and configuration](#persistence-and-configuration)
- [Devices and networks](#devices-and-networks)
- [Transactions and deleted records](#transactions-and-deleted-records)
- [GotFish investigation pivots](#gotfish-investigation-pivots)
- [Interpretation checklist](#interpretation-checklist)
- [References](#references)

## Tools and setup

| Tool | Setup and source | First use |
| --- | --- | --- |
| Registry Explorer | Windows release from [Source](https://ericzimmerman.github.io/); unpack with Plugins/Bookmarks and install its matching .NET runtime. Already present in the maintainer's `dfir_tools/RegistryExplorer` | Open `RegistryExplorer.exe`; File → Load Hive; inspect its included manual |
| RECmd / rla | Download both from [Source](https://github.com/EricZimmerman/RECmd). Keep RECmd's Plugins and BatchExamples alongside the binary | `RECmd.exe -h`; `rla.exe -h` |
| UserAssist parser | Existing `dfir_tools/userassist_parser.py` by Awadh Aljuaid; clone [Source](https://github.com/Awad93/Userassist_parser) and install `python-registry` in a venv | `python3 userassist_parser.py -h` |
| Timeline Explorer | Open exported CSVs without losing the wide artifact columns. [Source](https://ericzimmerman.github.io/) | Open CSV, filter path/SID, sort time |

See [the local toolbox](../LOCAL-TOOLBOX.md) for actual installed paths and [setup](../SETUP.md) for portable installations. RECmd is an optional addition; it was not found beside the installed Registry Explorer.

## Script and command recipe

For the already-installed Registry Explorer:

1. Open a **copy** of NTUSER.DAT using File → Load Hive, with matching logs beside it. Record any replay/recovery decision.
2. Navigate to `Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU` and inspect commands, `MRUList`, and the key timestamp.
3. Navigate to `Explorer\UserAssist` under the same CurrentVersion branch, or use its bookmark/plugin view; retain the decoded fields and raw value data.
4. Export selected results to the case directory and open CSV output in Timeline Explorer. Repeat with SYSTEM/SOFTWARE and the correct user hives.

For repeatable batch processing, install the optional RECmd tool from the table above. PowerShell, after adding the downloaded CLI directories to PATH; use fresh output directories:

```powershell
$Case = 'C:\cases\registry'
New-Item -ItemType Directory -Force "$Case\reports" | Out-Null
RECmd.exe -f "$Case\hives\SYSTEM" --kn 'Select'
RECmd.exe -f "$Case\hives\NTUSER.DAT" --kn 'Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU' --details
RECmd.exe -f "$Case\hives\NTUSER.DAT" --kn 'Software\Microsoft\Windows\CurrentVersion\Run' --details
RECmd.exe -d "$Case\hives" --bn 'C:\tools\RECmd\BatchExamples\DFIRBatch.reb' --csv "$Case\reports"
RECmd.exe -f "$Case\hives\SOFTWARE" --sv 'LastRtpTurnedOffTime'
```

Open the batch CSV in Timeline Explorer. Follow its `PluginDetailFile` column for decoded UserAssist, MRU, or other plugin output. Retain console errors and the batch/plugin versions: a successful exit alone does not guarantee every hive/key was parsed.

For the existing local UserAssist script, WSL/Linux Python:

```bash
python3 -m venv /tmp/userassist-venv
/tmp/userassist-venv/bin/python -m pip install python-registry
mkdir -p /absolute/path/to/case/reports/userassist
/tmp/userassist-venv/bin/python /mnt/c/Users/ACER/dfir_tools/userassist_parser.py \
  /absolute/path/to/case/hives/NTUSER.DAT /absolute/path/to/case/reports/userassist
```

This is the user's existing script, not shipped here; its text matched the linked Awad93 upstream when reviewed on 2026-11-09. Compare its decoded fields with Registry Explorer; do not assume it replays logs. No custom repository helper is required.

## Hive and acquisition map

| File on the acquired Windows volume | Logical root / useful contents |
| --- | --- |
| `Windows\System32\config\SYSTEM` | HKLM\SYSTEM; control sets, services, devices, timezone |
| `Windows\System32\config\SOFTWARE` | HKLM\SOFTWARE; OS/application configuration, profiles, machine persistence |
| `Windows\System32\config\SAM` | Local account records; correlate RID/SID and profile directory |
| `Windows\System32\config\SECURITY` | Security policy and LSA-related data; needs context from the matching machine |
| `Users\<user>\NTUSER.DAT` | That user's HKCU; Explorer activity, application settings, user persistence |
| `Users\<user>\AppData\Local\Microsoft\Windows\UsrClass.dat` | Per-user Classes; ShellBags and class registrations |
| `Windows\AppCompat\Programs\Amcache.hve` | Application inventory; see [execution evidence](../Windows-Execution/README.md) |
| `Windows\System32\config\DEFAULT` | HKEY_USERS\.DEFAULT; not the same as the template `Users\Default\NTUSER.DAT` |

Preserve same-named `.LOG1`, `.LOG2`, and any `.LOG` files, original directory, hashes, acquisition time, and user SID. Include available VSS copies, RegBack files, and TxR material as separate sources; their presence and usefulness vary. A `.reg` text export omits hive structure, deleted cells, and key timestamps. The system hive locations and supporting files are described in [Microsoft's hive documentation](https://learn.microsoft.com/en-us/windows/win32/sysinfo/registry-hives).

## Identity and control sets

| Question | Hive / path / values | Interpretation |
| --- | --- | --- |
| Which OS/build? | SOFTWARE `Microsoft\Windows NT\CurrentVersion`: `ProductName`, `DisplayVersion`, `CurrentBuild`, `UBR` | Preserve build values; branding strings can lag upgrades |
| Which user owns this profile? | SOFTWARE `Microsoft\Windows NT\CurrentVersion\ProfileList\<SID>`: `ProfileImagePath` | Map SID → profile → NTUSER/UsrClass; do not infer solely from directory name |
| Which control set? | SYSTEM `Select`: `Current`, `Default`, `LastKnownGood` | `Current=1` maps to `ControlSet001`; inspect every acquired set separately |
| Host name? | SYSTEM `ControlSet00N\Control\ComputerName\ComputerName` | Compare with EVTX Computer field and network capture |
| Timezone configuration? | SYSTEM `ControlSet00N\Control\TimeZoneInformation` | Configuration at acquisition is not proof of historical offset/DST |
| Machine identifier? | SOFTWARE `Microsoft\Cryptography`: `MachineGuid` | A configuration identifier, not a secret or a guaranteed globally unique forensic identity |

`CurrentControlSet` is a live-system alias. An offline parser may expose only `ControlSet001`, `ControlSet002`, etc. Never hardcode `001` before checking `Select`.

## User activity and execution

The shorthand `Explorer` below means NTUSER `Software\Microsoft\Windows\CurrentVersion\Explorer`. These are starting points, with version-dependent layouts; use the [RECmd artifact definitions](https://github.com/EricZimmerman/RECmd/blob/master/BatchExamples/Kroll_Batch.reb) and [decoder plugins](https://github.com/EricZimmerman/RegistryPlugins) to resolve binary data.

| Artifact | Location | Useful fields and limits |
| --- | --- | --- |
| Run dialog | `Explorer\RunMRU` | Lettered command values and `MRUList`; preserve exact whitespace and suffixes. Not general shell history or standalone proof the command succeeded |
| UserAssist | `Explorer\UserAssist\{GUID}\Count` | ROT13 value names; decoder exposes counts, last execution, and version-specific focus fields. Focus time is not process lifetime |
| RecentDocs | `Explorer\RecentDocs` and extension subkeys | MRU ordering and shell-item data; file interaction clue, not full contents |
| Open/save dialogs | `Explorer\ComDlg32\OpenSavePidlMRU` | Per-extension dialog history; opening a dialog entry does not prove execution |
| Last visited dialog | `Explorer\ComDlg32\LastVisitedPidlMRU` | Application/directory relationship; decode shell items |
| Typed paths | `Explorer\TypedPaths` | Explorer address-bar paths; values do not have independent last-write times |
| ShellBags | UsrClass `Local Settings\Software\Microsoft\Windows\Shell\BagMRU` and `Bags`; also inspect NTUSER variants | Folder navigation/view context, including paths no longer present; distinguish embedded filesystem times from registry time |
| BAM | SYSTEM `ControlSet00N\Services\bam\State\UserSettings\<SID>`; older `bam\UserSettings` layout | Executable paths and timestamps; retention/coverage depend on Windows build, not an exhaustive execution log |
| RDP client history | NTUSER `Software\Microsoft\Terminal Server Client\Default` and `Servers` | Destination and username hints; correlate with [RDP caches](../Windows-Artifacts/README.md#rdp-cache-and-execution-chains) and event logs |

ROT13 only decodes the value **name**, not its binary payload:

```bash
printf '%s\n' 'P:\Jvaqbjf\flfgrz32\pnyp.rkr' | tr 'A-Za-z' 'N-ZA-Mn-za-m'
```

Use parser output for UserAssist fields rather than applying offsets from another Windows version. Record the GUID, original value name, decoded name, value bytes, and parser version. For MRU lists, order and time are different facts; one key timestamp cannot date every listed item.

## Persistence and configuration

| Mechanism | Hive-relative location | Correlate with |
| --- | --- | --- |
| User logon autoruns | NTUSER `Software\Microsoft\Windows\CurrentVersion\Run` and `RunOnce` | Target file/hash, user logon, process creation |
| Machine logon autoruns | SOFTWARE `Microsoft\Windows\CurrentVersion\Run` and `RunOnce`; inspect applicable `Wow6432Node` views | Scope and architecture; compare with user entries |
| Services | SYSTEM `ControlSet00N\Services\<name>`: `ImagePath`, `Start`, `Type`, `ObjectName`, `Parameters\ServiceDll` | Service events, executable/DLL, account, process ancestry |
| Winlogon | SOFTWARE `Microsoft\Windows NT\CurrentVersion\Winlogon`: `Shell`, `Userinit` | Baseline for that host and logon execution |
| Image execution options | SOFTWARE `Microsoft\Windows NT\CurrentVersion\Image File Execution Options\<exe>` | `Debugger` value and related process chain; legitimate debugging exists |
| Scheduled tasks | SOFTWARE `Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Tree` and `Tasks` | GUID/path with `Windows\System32\Tasks` XML and TaskScheduler events |
| PowerShell policy | SOFTWARE `Policies\Microsoft\Windows\PowerShell`; NTUSER `Software\Policies\Microsoft\Windows\PowerShell` | ScriptBlockLogging/ModuleLogging/Transcription settings and historical logs |
| Custom payload/key storage | Any application-created key, including NTUSER `Software\...` | Exact value type/bytes, loader's lookup code, decoding/crypto parameters |

Run and RunOnce configure execution at logon, with different deletion and retry behavior. A value's absence after execution is not proof it never existed. See [Microsoft's Run/RunOnce rules](https://learn.microsoft.com/en-us/windows/win32/setupapi/run-and-runonce-registry-keys).

Search rather than assume where a malware-created value lives:

```powershell
RECmd.exe -d 'C:\cases\registry\hives' --sa 'DiskCleanup'
RECmd.exe -f 'C:\cases\registry\hives\NTUSER.DAT' --minSize 1024
# Substitute a confirmed key and value; preserve raw bytes for decoding.
RECmd.exe -f 'C:\cases\registry\hives\NTUSER.DAT' --kn 'Software\ExampleApp' --vn 'Blob' --saveTo 'C:\cases\registry\reports\blob.bin'
```

Large binary/Base64 values are leads, not automatically malware. Compare decoded content with file signatures and the code that reads it.

## Devices and networks

| Question | Starting keys | Next evidence |
| --- | --- | --- |
| USB storage device? | SYSTEM `ControlSet00N\Enum\USBSTOR`, `Enum\USB` | Serial/instance ID, SetupAPI device logs, device-property timestamps |
| Drive mapping? | SYSTEM `MountedDevices` | Volume identity with disk serial, LNK target volume, mounted-device records |
| User browsed a volume? | NTUSER `Software\Microsoft\Windows\CurrentVersion\Explorer\MountPoints2` | ShellBags, RecentDocs, LNK, copied files |
| Network profile? | SOFTWARE `Microsoft\Windows NT\CurrentVersion\NetworkList\Profiles` and `Signatures` | Profile GUID/name and network events; dates require a format-aware decoder |
| Interface settings? | SYSTEM `ControlSet00N\Services\Tcpip\Parameters\Interfaces` | DHCP/static address, lease context, PCAP |

A USB key's last-write time is not universally its first insertion or last removal. NetworkList dates use structured date fields; do not feed them blindly to a FILETIME converter.

## Transactions and deleted records

Registry Explorer can offer log replay when opening a dirty hive. Keep the original set and save recovered results separately. Record whether each report represents the original or replayed view. For a saved replayed copy:

```powershell
rla.exe -d 'C:\cases\registry\hives' --out 'C:\cases\registry\replayed' --ca
```

Do not mix logs between users, snapshots, or acquisition times. A recovered deleted cell may be stale, partially overwritten, or disconnected from its original parent. Validate paths, types, and surrounding records before treating it as an active setting. Hive sequence/checksum issues and transaction replay are covered by [REGF format research](https://github.com/libyal/libregf/blob/main/documentation/Windows%20NT%20Registry%20File%20%28REGF%29%20format.asciidoc).

## GotFish investigation pivots

[TryHards CTF 2026 — GotFish](https://2byte36.github.io/blog/tryhards-ctf-2026) supplies a worked ClickFix/ransomware example:

1. Recover the page's JavaScript from browser cache; compare its offered command with RunMRU **character for character**. A copied command and the input retained by Windows can differ.
2. Correlate PowerShell logging, Defender detection, Prefetch, and UserAssist with that user's profile. Use [event logs](../Windows-Event-Logs/README.md) to establish recorded execution and security changes.
3. Search SOFTWARE for `LastRtpTurnedOffTime`; retain the actual parent key, raw value, and decoded timestamp. Do not substitute the key's last-write time for the time stored in the value.
4. Investigate the case-specific NTUSER key `Software\Microsoft\Windows\CurrentVersion\Apps\D15kCl34nUp` as key material. Recover the mode/IV/padding from the code and note before attempting [decryption](../Malware-Recovery/README.md).
5. Correlate deleted tools and Startup entries using [MFT/USN](../NTFS-Forensics/README.md). A log showing policy being enabled does not alone prove what the policy was before that event.

The writeup is a case study, not a universal path list. Focus-time counters should stay labeled as focus time even if a challenge calls them runtime.

## Interpretation checklist

For each answer retain: source hive/hash, user/SID, original versus replayed state, full key path, value name/type/raw data, decoder/version, timestamp field/epoch/timezone, and corroborating artifact. Key last-write timestamps apply to keys; values do not each carry a universal modification timestamp. An absent key may reflect collection scope, cleanup, policy, version, or parser limitations.

## References

- [Registry Explorer downloads and documentation](https://ericzimmerman.github.io/)
- [RECmd and rla CLI](https://github.com/EricZimmerman/RECmd)
- [RECmd DFIR batch](https://github.com/EricZimmerman/RECmd/blob/master/BatchExamples/DFIRBatch.md)
- [Registry decoder plugins](https://github.com/EricZimmerman/RegistryPlugins)
- [Windows shell-item format](https://github.com/libyal/libfwsi/blob/main/documentation/Windows%20Shell%20Item%20format.asciidoc)
- [Microsoft registry hives](https://learn.microsoft.com/en-us/windows/win32/sysinfo/registry-hives)
- [TryHards — GotFish](https://2byte36.github.io/blog/tryhards-ctf-2026)
