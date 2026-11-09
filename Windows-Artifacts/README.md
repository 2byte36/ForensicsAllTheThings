# Windows artifacts

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Correlate execution, persistence, identity, and file activity across independent artifact types.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Artifact map](#artifact-map)
- [Parse event logs and Prefetch](#parse-event-logs-and-prefetch)
- [Registry pivots](#registry-pivots)
- [DPAPI and credential artifacts](#dpapi-and-credential-artifacts)
- [RDP cache and execution chains](#rdp-cache-and-execution-chains)
- [Offline event query and artifact selection](#offline-event-query-and-artifact-selection)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| Zimmerman tools | EVTX, registry, Prefetch, MFT parsers | Windows: download Get-ZimmermanTools, inspect it, then run with `-Dest` as documented; install the matching .NET runtime. [Source](https://ericzimmerman.github.io/) | Run the selected executable with `-h` |
| pypykatz | LSASS/DPAPI parsing | In the Python venv: `python -m pip install pypykatz`. [Source](https://github.com/skelsec/pypykatz#installation) | `pypykatz --help` |
| bmc-tools | RDP bitmap recovery | Clone the upstream source and use its Python CLI. [Source](https://github.com/ANSSI-FR/bmc-tools) | `python3 bmc-tools.py -h` |
| WinDbg | Windows dump inspection | Install on Windows using Microsoft’s setup instructions. [Source](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/) | Open debugger Help/About |

## Script and command recipe

Use the installed EvtxECmd directly in **Windows PowerShell**:

```powershell
$Case = 'C:\cases\windows'
New-Item -ItemType Directory -Force "$Case\reports" | Out-Null
& 'C:\Users\ACER\dfir_tools\EvtxeCmd\EvtxECmd.exe' -f "$Case\Security.evtx" --maps 'C:\Users\ACER\dfir_tools\EvtxeCmd\Maps' --csv "$Case\reports"
```

Open the CSV in Timeline Explorer. See the detailed [event-log workflow](../Windows-Event-Logs/README.md), [registry guide](../Windows-Registry/README.md), [execution guide](../Windows-Execution/README.md), and [NTFS guide](../NTFS-Forensics/README.md) for focused commands and interpretation.

Optional existing script: [evtx_export.ps1](../scripts/helpers/evtx_export.ps1) exports raw XML/metadata as JSONL using Windows Get-WinEvent; see [the catalog](../SCRIPTS.md) for its output behavior.

## Artifact map

| Artifact | Typical location | Useful for |
| --- | --- | --- |
| EVTX | `Windows/System32/winevt/Logs` | Authentication, process events, PowerShell, Defender |
| SOFTWARE / SYSTEM / SAM / SECURITY | `Windows/System32/config` | OS/build, services, accounts, protected secrets |
| NTUSER.DAT | User profile root | Per-user configuration and persistence |
| UsrClass.dat | `AppData/Local/Microsoft/Windows` | Shell and application artifacts |
| Prefetch | `Windows/Prefetch` | Program execution clues and referenced files |
| Amcache.hve | `Windows/AppCompat/Programs` | Application inventory and file metadata |
| `$MFT` / `$Extend/$UsnJrnl:$J` | NTFS metadata | File paths, timestamps, rename/delete activity |
| LNK / Jump Lists | User profile and `AppData/Roaming/Microsoft/Windows/Recent` | Recently opened items and targets |
| RDP bitmap cache | `AppData/Local/Microsoft/Terminal Server Client/Cache` | Fragments of remote desktop screens |

## Parse event logs and Prefetch

PowerShell examples using Eric Zimmerman's tools:

```powershell
.\EvtxECmd.exe -d .\evidence\evtx --csv .\work\evtx
.\PECmd.exe -d .\evidence\Prefetch --csv .\work\prefetch
.\MFTECmd.exe -f '.\evidence\$MFT' --csv .\work\mft
```

Search parsed records by filename, parent command line, SID, or a narrow time interval. Preserve the event provider and record ID. Event ID alone is ambiguous across providers.

| Provider / event | Lead |
| --- | --- |
| Security 4624 / 4625 | Successful / failed logon |
| Security 4672 | Special privileges assigned to a logon |
| Security 4688 | Process creation, if enabled |
| PowerShell Operational 4104 | Script block content, if logged |
| Sysmon 1 / 3 / 11 / 13 | Process / network / file creation / registry value activity, depending on configuration |

Reassemble multipart script-block events by their identifiers and sequence fields. Prefetch is supporting execution evidence; Amcache and ShimCache presence alone do not prove execution. Correlate timestamps with logs and file metadata.

## Registry pivots

- OS/build: `SOFTWARE\Microsoft\Windows NT\CurrentVersion`.
- User SID/profile mapping: `SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList`.
- Per-user persistence: `NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Run` and `RunOnce`.
- Services: the active control set in SYSTEM; resolve it using `Select` rather than assuming `ControlSet001`.
- MachineGuid: `SOFTWARE\Microsoft\Cryptography`.

Load offline hives in Registry Explorer or another forensic parser. Preserve transaction logs for recovery. A key's last-write time is not a timestamp for every value stored under it.

## DPAPI and credential artifacts

A common recovery chain is user SID + password/hash → DPAPI master key → application-protected key → encrypted database values. Collect the user's `Microsoft/Protect/<SID>` directory, relevant application configuration, and the correct profile databases before choosing a decoder.

For a challenge-supplied LSASS minidump:

```bash
pypykatz lsa minidump lsass.dmp
```

This does not work on arbitrary process dumps and depends on captured pages and OS support. Keep recovered credentials in case notes, not this repository. See [browser and messaging](../Browser-and-Messaging/README.md) for application-specific layers.

## RDP cache and execution chains

Use `bmc-tools` to reconstruct bitmap tiles from RDP cache files, then inspect the collage and individual tiles. **Forgotten Fragments** recovered visible text this way.

The existing alias points to the [ANSSI upstream parser](https://github.com/ANSSI-FR/bmc-tools). Collect the user's `AppData/Local/Microsoft/Terminal Server Client/Cache` directory. In WSL:

```bash
mkdir -p work/rdp-tiles
python3 "$HOME/ctf-tools/bmc-tools/bmc-tools.py" -s extracts/rdp-cache -d work/rdp-tiles -b
# Interactive alias equivalent:
bmc-tools -s extracts/rdp-cache -d work/rdp-tiles -b
```

Choose one invocation. The collage groups recovered tiles; it does not guarantee their original screen positions or chronological order. Preserve source cache names and inspect individual tiles when interpreting text.


In **The Apex Affair**, Outlook IndexedDB, Sysmon, Defender, registry, and memory supplied different parts of the chain. **Alice in DFIRland** instead exposed a challenge setup script through PowerShell logs: label that as an unintended shortcut, not a complete intrusion reconstruction.

## Offline event query and artifact selection

On a Windows analysis machine, PowerShell can query a supplied EVTX without importing it into the live log:

```powershell
Get-WinEvent -FilterHashtable @{Path='.\evidence\Security.evtx'; Id=4624,4625,4688} |
  Select-Object TimeCreated, Id, RecordId, ProviderName, Message |
  Export-Csv .\work\security-events.csv -NoTypeInformation
```

Message rendering depends on provider resources installed on the analysis machine. Preserve raw event XML when messages fail to render; `TimeCreated` display may use the analysis machine's timezone. Prefer named XML fields over assumptions about positional fields across versions.

| Question | Cross-check artifacts |
| --- | --- |
| Where did a downloaded file originate? | Browser downloads, Zone.Identifier stream, email, proxy logs |
| Was it executed? | Process events, Prefetch, relevant application logs |
| What persisted? | Run keys, scheduled-task XML, services, Startup links |
| What was deleted? | Recycle Bin `$I` metadata and `$R` content, MFT, USN |
| What external media was used? | USBSTOR/device records, setup logs, LNK volume metadata |
| What did the user type? | PowerShell PSReadLine history and script-block logs, when present |

Collections often omit one or more of these sources. Record collection scope and logging configuration before treating absence as evidence of non-execution.

## References

- [Microsoft Sysmon documentation](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon)
- [PowerShell Get-WinEvent](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.diagnostics/get-winevent)
- [Eric Zimmerman tools](https://ericzimmerman.github.io/)
- [Compfest — The Apex Affair](https://2byte36.github.io/blog/compfest18-quals)
- [HackToday — Alice in DFIRland](https://2byte36.github.io/blog/hacktoday-2026)
- [The ACE — Incident 2](https://2byte36.github.io/blog/the-ace)
- [ARA quals — dumpling and horseman](https://2byte36.github.io/blog/ara-7-quals)
- [NCLP — Forgotten Fragments](https://2byte36.github.io/blog/nclp-ctf-s1)
