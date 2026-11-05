# Timestamps and timeline construction

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Normalize time while preserving the original value, timezone, precision, and event meaning.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Recognize the timestamp format](#recognize-the-timestamp-format)
- [Convert without floating-point loss](#convert-without-floating-point-loss)
- [Timezones and clock skew](#timezones-and-clock-skew)
- [Filesystem time meaning](#filesystem-time-meaning)
- [Build a supertimeline](#build-a-supertimeline)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| Plaso / psort | Supertimeline extraction | Use a supported packaged release per upstream guidance; avoid assuming a plain pip install includes native dependencies. [Source](https://plaso.readthedocs.io/en/latest/sources/user/Users-Guide.html) | `log2timeline.py --version`; `psort.py --help` |
| Sleuth Kit | Filesystem analysis | `sudo apt install sleuthkit`. [Source](https://www.sleuthkit.org/sleuthkit/download.php) | `mmls -V` |

## Script and command recipe

Helper: [timestamps.py](../scripts/helpers/timestamps.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/timestamps.py filetime 133444736000000001
python3 scripts/helpers/timestamps.py chromium 13344473600000000
```

Prints JSON containing raw value, format, UTC, and leftover FILETIME 100 ns ticks. Accepts signed decimal integers; caller must identify the epoch and distinguish sentinel values. It does not guess timezone or unit.

## Recognize the timestamp format

| Format | Epoch / unit | Common context |
| --- | --- | --- |
| Unix time | 1970-01-01 UTC, seconds | Logs, filesystem APIs |
| Unix milliseconds / microseconds | Same epoch, scaled units | JSON APIs, databases |
| Windows FILETIME | 1601-01-01 UTC, 100 ns ticks | Windows structures and NTFS timestamps |
| Chromium time | 1601-01-01 UTC, microseconds | Many Chromium history columns |
| Apple CFAbsoluteTime | 2001-01-01 UTC, seconds | Some Apple application stores |
| DOS/FAT packed date/time | Packed calendar fields, often local time | ZIP and FAT metadata |

These are candidates, not automatic classifications. Confirm the field definition: Apple applications, browser tables, and archive tools may use several representations. Digit count alone is insufficient.

## Convert without floating-point loss

```bash
python3 - <<'PYCODE'
from datetime import datetime, timedelta, timezone
UTC = timezone.utc
unix_seconds = 1700000000  # Example input.
print('Unix:', datetime.fromtimestamp(unix_seconds, UTC).isoformat())
filetime = 133444736000000001  # Example input including a 100 ns remainder.
microseconds, remainder = divmod(filetime, 10)
converted = datetime(1601, 1, 1, tzinfo=UTC) + timedelta(microseconds=microseconds)
print('FILETIME:', converted.isoformat(), 'extra 100ns ticks:', remainder)
chromium = 13344473600000000
print('Chromium:', (datetime(1601, 1, 1, tzinfo=UTC) +
                     timedelta(microseconds=chromium)).isoformat())
PYCODE
```

Store the raw integer alongside formatted output. Python datetime has microsecond precision, so preserve FILETIME's remaining tick separately when exact ordering matters. Zero and maximum integer values may be sentinels, not real event times.

## Timezones and clock skew

A timestamp without an offset is not automatically UTC. Determine the host's timezone and whether the parser already converted it. Daylight-saving transitions can make local times ambiguous or nonexistent; retain both candidate interpretations until evidence resolves them.

Compare common events across sources to estimate skew. Keep the observed and adjusted times in separate columns. Network latency, buffered logging, and parser rounding can also explain small differences.

## Filesystem time meaning

| Field | Typical meaning | Common mistake |
| --- | --- | --- |
| mtime | Content modification | Treating it as download or creation time |
| ctime on Unix | Inode metadata change | Calling it creation time |
| atime | Access, subject to mount policies | Assuming every read updates it |
| birth / creation time | Creation in that filesystem | Assuming copies preserve original creation |

NTFS stores timestamps in multiple attributes, and copied/extracted files gain new host metadata. Compare original filesystem records, journal entries, and logs before attributing a modification to timestomping.

## Build a supertimeline

```bash
log2timeline.py --storage-file work/case.plaso evidence.E01
psort.py -o l2tcsv -w work/timeline.csv work/case.plaso
```

Use supported parsers and inspect warnings, timezone assumptions, and acquisition coverage. Narrow by a meaningful window and pivot on user, path, hash, or process. More events do not automatically give more certainty.

For a filesystem-only timeline, see [Sleuth Kit commands](../Disk-Forensics/README.md#sleuth-kit-workflow). Use [log analysis](../Logs-and-Timelines/README.md) to interpret application events rather than sorting timestamps without context.

## References

- [Microsoft FILETIME definition](https://learn.microsoft.com/en-us/windows/win32/api/minwinbase/ns-minwinbase-filetime)
- [Python datetime](https://docs.python.org/3/library/datetime.html)
- [Chromium time representation](https://chromium.googlesource.com/chromium/src/+/main/base/time/time.h)
- [Apple CFAbsoluteTime](https://developer.apple.com/documentation/corefoundation/cfabsolutetime)
- [Plaso log2timeline usage](https://plaso.readthedocs.io/en/latest/sources/user/Using-log2timeline.html)
