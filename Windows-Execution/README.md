# Windows execution and persistence evidence

[Home](../README.md) · [Registry](../Windows-Registry/README.md) · [Event logs](../Windows-Event-Logs/README.md) · [NTFS](../NTFS-Forensics/README.md)

Separate file presence, user interaction, configured persistence, and recorded execution. Use multiple artifacts to establish the executable, user, time, and surrounding behavior.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Evidence strength and locations](#evidence-strength-and-locations)
- [LNK and Jump Lists](#lnk-and-jump-lists)
- [Persistence triage](#persistence-triage)
- [ClickFix and sideloading pivots](#clickfix-and-sideloading-pivots)
- [References](#references)

## Tools and setup

| Tool | Setup / source | Verify |
| --- | --- | --- |
| PECmd | Existing `dfir_tools/PECmd`; download matching runtime/build from [Source](https://github.com/EricZimmerman/PECmd) | `PECmd.exe -h` |
| Registry Explorer / Timeline Explorer | Existing local Windows tools; [Source](https://ericzimmerman.github.io/) | Open copied hive / exported CSV |
| AmcacheParser | Optional Windows CLI from [Source](https://github.com/EricZimmerman/AmcacheParser) | `AmcacheParser.exe -h` |
| LECmd / JLECmd | Optional LNK/Jump List parsers. [LECmd source](https://github.com/EricZimmerman/LECmd), [JLECmd source](https://github.com/EricZimmerman/JLECmd) | `LECmd.exe -h`; `JLECmd.exe -h` |

Keep tool versions with exported reports. Newer CLI builds may work via `dotnet TOOL.dll` on other platforms; use the runtime and invocation supported by the particular release.

## Script and command recipe

PowerShell, using copied Windows Prefetch and a separate report folder:

```powershell
$Case = 'C:\cases\execution'
New-Item -ItemType Directory -Force "$Case\reports" | Out-Null
& 'C:\Users\ACER\dfir_tools\PECmd\PECmd.exe' -d "$Case\Windows\Prefetch" --csv "$Case\reports" --csvf prefetch.csv
# Optional tool after installation:
AmcacheParser.exe -f "$Case\Windows\AppCompat\Programs\Amcache.hve" --csv "$Case\reports"
```

PECmd exports artifact details and a run-time timeline. Inspect executable name, available run timestamps/count, referenced files/directories, and volume context. An older retained run is **not necessarily the first ever execution**. Prefetch availability, capacity, and timestamp slots vary with OS/configuration. See [PECmd's output notes](https://github.com/EricZimmerman/PECmd).

## Evidence strength and locations

| Artifact | Acquisition location | Supports / limitations |
| --- | --- | --- |
| Prefetch | `Windows\Prefetch\*.pf` | Recorded launch context and retained run times; not full command lines or all historical executions |
| UserAssist | User NTUSER hive | GUI-related interaction/execution and focus fields; see [registry decoding](../Windows-Registry/README.md#user-activity-and-execution) |
| BAM | SYSTEM hive | User SID/path/time for covered activity; limited retention and coverage |
| Amcache | `Windows\AppCompat\Programs\Amcache.hve` and logs | Application/file inventory; a record's presence alone is not universal execution proof |
| AppCompatCache / Shimcache | SYSTEM `ControlSet00N\Control\Session Manager\AppCompatCache` | Compatibility-cache information; semantics change by Windows version |
| LNK | User `AppData\Roaming\Microsoft\Windows\Recent`, Desktop, other folders | Target path, volume, arguments, metadata snapshot; link existence does not prove launch |
| Jump Lists | `Recent\AutomaticDestinations`, `Recent\CustomDestinations` | Application-associated items and interaction metadata; structures differ |
| PSReadLine history | User `AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt` | Saved interactive input; no default per-line timestamps, not every host/session |
| Process events | Security 4688 / Sysmon 1 | Recorded process creation and available user/command-line context |

Use [AmcacheParser](https://github.com/EricZimmerman/AmcacheParser), [AppCompatCacheParser](https://github.com/EricZimmerman/AppCompatCacheParser), and the [artifact decoder sources](https://github.com/EricZimmerman/RegistryPlugins) for version-specific interpretation. Do not turn inventory or cache hits into an unsupported exact execution time.

## LNK and Jump Lists

After installing the optional tools, export a copied user's Recent directory:

```powershell
LECmd.exe -d 'C:\cases\execution\user\Recent' --csv 'C:\cases\execution\reports' --csvf links.csv
JLECmd.exe -d 'C:\cases\execution\user\Recent\AutomaticDestinations' --csv 'C:\cases\execution\reports'
JLECmd.exe -d 'C:\cases\execution\user\Recent\CustomDestinations' --csv 'C:\cases\execution\reports'
```

Compare target path, arguments, working directory, volume serial, and embedded target timestamps with the current file and MFT. Embedded target metadata can describe an earlier state; distinguish it from the LNK file's own filesystem timestamps. A removable-drive letter can change, so compare volume identifiers and [USB registry data](../Windows-Registry/README.md#devices-and-networks).

## Persistence triage

| Mechanism | Collect | Verify execution with |
| --- | --- | --- |
| Run / RunOnce | User and machine hives, applicable 32-bit view | Logon and process events, Prefetch |
| Startup folder | User `AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`; system `ProgramData\Microsoft\Windows\Start Menu\Programs\Startup` | LNK target/arguments, MFT/USN creation, launch evidence |
| Scheduled task | `Windows\System32\Tasks` XML + TaskCache registry + TaskScheduler logs | Action, arguments, trigger, principal, enabled state, task execution events |
| Service | SYSTEM Services key + binary/DLL + System logs | ImagePath, ServiceDll, start type/account and process ancestry |
| WMI subscription | Available WMI repository/telemetry; Sysmon 19–21 when collected | Filter → consumer → binding plus resulting process/activity |

Read acquired task XML directly; querying `schtasks` on the analysis computer would show the wrong machine:

```powershell
[xml]$TaskXml = Get-Content -LiteralPath 'C:\cases\execution\Windows\System32\Tasks\ExampleTask' -Raw
$TaskXml.Task.Actions.Exec | Format-List Command,Arguments,WorkingDirectory
$TaskXml.Task.Principals.Principal | Format-List *
$TaskXml.Task.Triggers | Format-List *
```

A trigger definition is an intended schedule, not a record that it fired. Relative paths, environment variables, account context, and working directory can affect the executable actually reached.

## ClickFix and sideloading pivots

For ClickFix: cached page/JavaScript → recorded browser visit → RunMRU → PowerShell host/process → payload file/hash → persistence → outbound traffic. Preserve every command representation; whitespace/quoting can change between the page and recorded input. See [browser cache recipes](../Browser-and-Messaging/README.md#cache-downloads-and-clickfix).

For sideloading: archive/download → signed loader beside unexpected DLL → process creation → loaded DLL path/hash → behavior. “Signed loader ran” and “malicious DLL loaded” are separate findings; seek image-load telemetry, memory mappings, or static loader resolution evidence.

## References

- [PECmd](https://github.com/EricZimmerman/PECmd)
- [LECmd](https://github.com/EricZimmerman/LECmd) and [JLECmd](https://github.com/EricZimmerman/JLECmd)
- [Microsoft Shell Link format](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-shllink/)
- [Task Scheduler schema](https://learn.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-schema)
- [Sysmon WMI and process events](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon)
- [TryHards — GotFish](https://2byte36.github.io/blog/tryhards-ctf-2026)
- [Schematics — Ratatouille](https://2byte36.github.io/blog/schematics-2026-quals)
