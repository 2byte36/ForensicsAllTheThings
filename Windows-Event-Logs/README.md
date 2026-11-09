# Windows event logs

[Home](../README.md) · [Registry](../Windows-Registry/README.md) · [General logs](../Logs-and-Timelines/README.md)

Export EVTX with EvtxECmd, inspect CSVs in Timeline Explorer, and return to XML for exact fields. Identify an event by provider, channel, ID, and version; the numeric ID alone is ambiguous.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [High-value events](#high-value-events)
- [Native offline queries](#native-offline-queries)
- [PowerShell fragments and policy](#powershell-fragments-and-policy)
- [Build a defensible sequence](#build-a-defensible-sequence)
- [References](#references)

## Tools and setup

| Tool | Setup / source | Verify |
| --- | --- | --- |
| EvtxECmd | Existing `dfir_tools/EvtxeCmd`; keep its Maps directory. [Source](https://github.com/EricZimmerman/evtx) | `EvtxECmd.exe -h` |
| Timeline Explorer | Existing `dfir_tools/TimelineExplorer/TimelineExplorer`; download/runtime at [Source](https://ericzimmerman.github.io/) | Open exported CSV |
| Get-WinEvent | Built into Windows PowerShell; no module installation. [Source](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.diagnostics/get-winevent) | `Get-Help Get-WinEvent` |

## Script and command recipe

PowerShell; use a case output directory and the Maps directory from the **same installed release**:

```powershell
$Case = 'C:\cases\events'
$Evtx = 'C:\Users\ACER\dfir_tools\EvtxeCmd\EvtxECmd.exe'
$Maps = 'C:\Users\ACER\dfir_tools\EvtxeCmd\Maps'
New-Item -ItemType Directory -Force "$Case\reports" | Out-Null
& $Evtx -d "$Case\winevt\Logs" --maps $Maps --csv "$Case\reports" --csvf events.csv
& $Evtx -f "$Case\winevt\Logs\Microsoft-Windows-PowerShell%4Operational.evtx" --maps $Maps --xml "$Case\reports"
& 'C:\Users\ACER\dfir_tools\TimelineExplorer\TimelineExplorer\TimelineExplorer.exe'
```

In Timeline Explorer, open `events.csv`, filter provider/channel and incident time, then inspect payload columns. Keep unfiltered output: maps normalize fields but may not describe every event version. XML retains the named EventData and original SystemTime. [EvtxECmd documents its maps and export formats](https://github.com/EricZimmerman/evtx).

## High-value events

Events depend on installed providers, audit policy, retention, and version. A missing record is not proof an action did not happen.

| Provider / channel | IDs | Useful pivot |
| --- | --- | --- |
| Microsoft-Windows-Security-Auditing / Security | 4624, 4625 | Successful/failed logon; type, account/SID, source IP, LogonId |
| Microsoft-Windows-Security-Auditing / Security | 4648, 4672 | Explicit credentials; privileged logon context |
| Microsoft-Windows-Security-Auditing / Security | 4688, 4689 | Process creation/termination when audited; command-line recording requires additional policy |
| Microsoft-Windows-Security-Auditing / Security | 4698, 4702 | Scheduled task creation/update; task XML and subject context |
| Microsoft-Windows-Eventlog / Security | 1102 | Security audit log cleared; retain subject and exact time |
| Service Control Manager / System | 7045 | Service installation; service path/type/account |
| Microsoft-Windows-Eventlog / System | 104 | A log was cleared; inspect event data to identify the affected channel |
| Microsoft-Windows-PowerShell / Operational | 4103, 4104 | Module/pipeline context; script-block text and fragments |
| PowerShell / Windows PowerShell | 400, 403 | Engine lifecycle/context; inspect HostApplication where present |
| Microsoft-Windows-Windows Defender / Operational | 1116, 1117 | Detection versus action; correlate threat ID, path, result |
| Same Defender provider/channel | 5001, 5007 | Real-time protection disabled; configuration changed (inspect old/new data) |
| Microsoft-Windows-Sysmon / Operational | 1, 3, 7 | Process, network, image/DLL load; collection filters affect coverage |
| Same Sysmon provider/channel | 11, 12–14, 22 | File creation, registry activity, DNS query |

Verify event semantics against [Security auditing](https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/advanced-security-auditing-faq), [Sysmon](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon), and [Defender's event catalog](https://learn.microsoft.com/en-us/defender-endpoint/troubleshoot-microsoft-defender-antivirus). A detection does not establish successful remediation; a service installation does not prove it started.

## Native offline queries

Run on Windows. The queries read supplied EVTX files, not the analyst machine's live log:

```powershell
Get-WinEvent -FilterHashtable @{Path='C:\cases\events\Security.evtx'; Id=4624,4625,4688,1102} -Oldest |
    Select-Object TimeCreated,ProviderName,Id,RecordId,Message

Get-WinEvent -Path 'C:\cases\events\System.evtx' -FilterXPath '*[System[Provider[@Name="Microsoft-Windows-Eventlog"] and EventID=104]]' -Oldest |
    ForEach-Object { $_.ToXml() } |
    Out-File 'C:\cases\events\reports\cleared-events.xml.txt' -Encoding utf8
```

The second output is a sequence of XML events, not one XML document. If rendered `Message` text is unavailable because a provider resource is missing, inspect `ToXml()` rather than treating the event as empty. SystemTime in XML is UTC; a displayed TimeCreated may be converted to local time.

For named process fields rather than positional property indices:

```powershell
Get-WinEvent -FilterHashtable @{Path='C:\cases\events\Security.evtx'; Id=4688} -Oldest | ForEach-Object {
    [xml]$EventXml = $_.ToXml()
    $Data = @{}
    foreach ($Field in $EventXml.Event.EventData.Data) { $Data[$Field.Name] = $Field.InnerText }
    [pscustomobject]@{
        Utc = $EventXml.Event.System.TimeCreated.SystemTime
        RecordId = $_.RecordId
        NewProcessId = $Data.NewProcessId
        Image = $Data.NewProcessName
        ParentImage = $Data.ParentProcessName
        CommandLine = $Data.CommandLine
        LogonId = $Data.SubjectLogonId
    }
} | Export-Csv 'C:\cases\events\reports\processes.csv' -NoTypeInformation
```

Field availability differs by [4688 version](https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688). Preserve missing fields rather than inventing values. Security process IDs can be hexadecimal; convert explicitly when joining to decimal IDs.

## PowerShell fragments and policy

For 4104, inspect `ScriptBlockId`, `MessageNumber`, `MessageTotal`, `ScriptBlockText`, and `Path` in XML. Filter one computer/provider/block, order by numeric MessageNumber, and verify that every expected fragment exists exactly once. Repeated identical fragments can be duplicates; conflicting text requires review. Do not concatenate all 4104 events by timestamp or assume every fragment is a separate command.

In Timeline Explorer, filter the block identifier and inspect each payload/XML fragment. Export selected rows for notes. Retain both the assembled text and the original event identifiers; never execute the recovered text to reconstruct it.

Windows PowerShell and PowerShell 7 use different provider/channel and policy contexts. Inspect the actual source and [Microsoft's logging documentation](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_logging_windows). Policy state in an acquired registry hive describes that snapshot; a command attempting to change logging does not prove the change succeeded or disclose the preceding effective policy.

## Build a defensible sequence

1. Anchor on a known path/hash/account or browser download; record UTC interval and host.
2. Link Sysmon ProcessGuid/ParentProcessGuid or Security PID + creation time + host. PID reuse makes PID-only joins unsafe.
3. Follow child command lines, DLL loads, registry writes, file changes, and network connections.
4. Match task/service definitions with their actual execution events and target files.
5. Check clearing events, record gaps, retention, and parser failures before interpreting silence.

For DLL sideloading, combine the signed executable path, adjacent DLL path/hash, Sysmon image-load records when collected, and process/network behavior. A signed parent alone does not establish that the loaded DLL is trusted. This is a useful pivot in [Schematics — Ratatouille](https://2byte36.github.io/blog/schematics-2026-quals); [GotFish](https://2byte36.github.io/blog/tryhards-ctf-2026) demonstrates the browser/PowerShell/Defender/cleanup sequence.

## References

- [EvtxECmd and event maps](https://github.com/EricZimmerman/evtx)
- [Get-WinEvent examples](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.diagnostics/get-winevent)
- [4624 logon fields](https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4624)
- [4698 scheduled tasks](https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4698)
- [1102 audit log clearing](https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-1102)
- [Sysmon event reference](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon)
