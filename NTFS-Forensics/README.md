# NTFS metadata and deleted files

[Home](../README.md) · [Disk acquisition](../Disk-Forensics/README.md) · [Windows Registry](../Windows-Registry/README.md)

Use MFT records to identify files and streams, USN to reconstruct recorded changes, and content recovery to validate what survived. Metadata alone cannot recreate overwritten data.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Artifact map](#artifact-map)
- [Extract from a disk image](#extract-from-a-disk-image)
- [Renames, deletion, and timestamps](#renames-deletion-and-timestamps)
- [Alternate streams and recycle bin](#alternate-streams-and-recycle-bin)
- [Recovery decision table](#recovery-decision-table)
- [References](#references)

## Tools and setup

| Tool | Install / source | Verify |
| --- | --- | --- |
| MFTECmd | Already in `dfir_tools/MFTECmd`; releases and runtime requirements at [Source](https://github.com/EricZimmerman/MFTECmd) | `MFTECmd.exe -h` |
| Timeline Explorer | Windows CSV viewer from [Source](https://ericzimmerman.github.io/) | Open the MFT/USN CSV |
| Sleuth Kit | Debian/Ubuntu/WSL: `sudo apt install sleuthkit`. [Source](https://www.sleuthkit.org/sleuthkit/download.php) | `mmls -V` |
| RBCmd | Optional Recycle Bin parser from [Source](https://github.com/EricZimmerman/RBCmd) | `RBCmd.exe -h` |

## Script and command recipe

PowerShell on copied metadata; single quotes preserve literal `$` characters:

```powershell
$Case = 'C:\cases\ntfs'
New-Item -ItemType Directory -Force "$Case\reports" | Out-Null
& 'C:\Users\ACER\dfir_tools\MFTECmd\MFTECmd.exe' -f "$Case\artifacts\`$MFT" --csv "$Case\reports" --csvf mft.csv
& 'C:\Users\ACER\dfir_tools\MFTECmd\MFTECmd.exe' -f "$Case\artifacts\`$J" --csv "$Case\reports" --csvf usn.csv
```

Open both CSVs in Timeline Explorer. Filter the executable/document name, record entry/sequence and parent identifiers, then follow rename/delete events. Newer MFTECmd builds support `-m` with the matching MFT for USN path resolution; confirm the installed help before using that optional flag. Keep parser warnings and unresolvable parents.

## Artifact map

| Artifact | What it contributes | What it does not establish alone |
| --- | --- | --- |
| `$MFT` | File records, attributes, names/parents, allocation state, resident content, stream runs | Who created/deleted a file, or a complete history |
| `$Extend\$UsnJrnl:$J` | Recorded file changes, reason flags, file/parent references, USN order | Complete file bytes or a perpetual audit log |
| `$LogFile` | Filesystem transaction material for supported parsers | The same semantics as USN or application event logs |
| Directory `$I30` | Index entries and possible residual names/metadata | Guaranteed current directory membership |
| `$Bitmap` | Cluster allocation state at acquisition | Which historical file occupied a free cluster |
| `$Recycle.Bin\<SID>` | `$I` metadata with corresponding `$R` content when retained | Every deleted file; bypassed/emptied bins leave different evidence |
| VSS | Older filesystem snapshots | Continuous coverage between snapshots |

NTFS attribute/stream structure is documented in [libfsntfs](https://github.com/libyal/libfsntfs/blob/main/documentation/New%20Technologies%20File%20System%20%28NTFS%29.asciidoc). [Microsoft's change-journal documentation](https://learn.microsoft.com/en-us/windows/win32/fileio/change-journals) explains why USN is a change record, not a content backup.

## Extract from a disk image

Linux/WSL; set the partition start **in sectors** from `mmls`, not bytes. For non-512-byte images supply the correct sector size with `-b` consistently.

```bash
mkdir -p work extracts
mmls disk.dd
PART_START=2048  # example only: replace from this image's partition table
fls -f ntfs -o "$PART_START" disk.dd > work/root.txt
fls -f ntfs -o "$PART_START" -r -p disk.dd > work/files.txt
rg -n '\$MFT|\$UsnJrnl|\$LogFile|Zone.Identifier|\$Recycle.Bin' work/files.txt
# $MFT is NTFS record 0; preserve holes/offsets (do not add icat -h).
icat -f ntfs -o "$PART_START" disk.dd 0 > 'extracts/$MFT'
# Replace with the actual record from fls, then inspect its attributes.
FILE_RECORD=42
istat -f ntfs -o "$PART_START" disk.dd "$FILE_RECORD"
# Example only: use the exact entry-type-id printed by fls/istat for the wanted stream.
STREAM_ID=42-128-3
icat -f ntfs -o "$PART_START" disk.dd "$STREAM_ID" > extracts/stream.bin
```

Export `$J` using its **named data stream** attribute, not a guessed record number or the unnamed stream. `128` denotes `$DATA`, but attribute IDs vary. [icat](https://www.sleuthkit.org/sleuthkit/man/icat.html) extracts a selected stream; [istat](https://www.sleuthkit.org/sleuthkit/man/istat.html) exposes the record's attributes and allocation information. Hash exported files and retain the extraction command and source image hash.

## Renames, deletion, and timestamps

- Join by file reference **including sequence number**, then parent reference and volume. MFT record numbers can be reused; matching only a filename or record number can join unrelated files.
- Pair USN rename old/new-name records using identity and order. Preserve all reason flags: one record may summarize multiple changes.
- Look for create/write/rename/delete patterns around a suspicious process's [execution time](../Windows-Execution/README.md). USN time is the recorded change time, not a universal file creation timestamp.
- Compare `$STANDARD_INFORMATION` and `$FILE_NAME` timestamp sets, file content, Prefetch, downloads, and event logs. A mismatch is a lead; copy/move/application behavior can also explain it.
- Distinguish filesystem metadata modification from content modification. Retain parser column names and raw precision instead of reducing every event to “modified”.

In [GotFish](https://2byte36.github.io/blog/tryhards-ctf-2026), this workflow connects tool deletion and Startup-folder activity to registry/log evidence. In a general case, require the actual retained records before inferring either action.

## Alternate streams and recycle bin

For a copied file on an NTFS analysis volume, PowerShell can inspect preserved ADS:

```powershell
Get-Item -LiteralPath 'C:\cases\ntfs\files\download.exe' -Stream *
Get-Content -LiteralPath 'C:\cases\ntfs\files\download.exe' -Stream Zone.Identifier
# Optional RBCmd, after installation:
RBCmd.exe -d 'C:\cases\ntfs\artifacts\$Recycle.Bin' --csv 'C:\cases\ntfs\reports'
```

An ordinary copy to a filesystem/archive that does not preserve ADS may lose `Zone.Identifier`; inspect the original image's stream list when possible. `ZoneId`, `HostUrl`, and `ReferrerUrl` are provenance clues when present, not proof of execution. For Recycle Bin pairs, retain SID, original path, deletion time, size, and matching `$R` bytes. Do not assume a `$R` name alone identifies the original pathname.

## Recovery decision table

| Observation | Next action |
| --- | --- |
| Deleted record still has data runs | Try `icat -r` with the confirmed record/stream; check for overwritten extents |
| Content resident in MFT | Inspect/export resident `$DATA`; validate size/signature |
| Name exists but content unavailable | Look for VSS, memory/cache, archives, backups, attachment copies |
| Fragmented file carved incorrectly | Reconstruct from valid run information; signature carving alone loses ordering |
| USN starts after the incident | State the retained interval; look for snapshots and other artifacts |
| SSD deletion yields zeros | Consider TRIM/acquisition effects; absence of bytes does not negate metadata evidence |

## References

- [MFTECmd CLI](https://github.com/EricZimmerman/MFTECmd)
- [Sleuth Kit fls](https://www.sleuthkit.org/sleuthkit/man/fls.html)
- [NTFS USN_RECORD_V2 fields and reason flags](https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-usn_record_v2)
- [RBCmd](https://github.com/EricZimmerman/RBCmd)
- [Windows file streams](https://learn.microsoft.com/en-us/windows/win32/fileio/file-streams)
