# macOS artifacts

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Investigate macOS property lists, launchd persistence, shell history, keychains, and unified logs from an offline acquisition. For systemd, Linux authentication logs, and container storage, use the separate [Linux guide](../Linux-Forensics/README.md).

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [macOS pivots](#macos-pivots)
- [Unified logs with Mandiant](#unified-logs-with-mandiant)
- [Launch agents and daemons](#launch-agents-and-daemons)
- [Correlate host activity](#correlate-host-activity)
- [LaunchAgent and staged-command correlation](#launchagent-and-staged-command-correlation)
- [References](#references)

## Tools and setup

The Python recipes work on macOS or a Linux analysis workstation. They inspect extracted files rather than the live system. See [SETUP.md](../SETUP.md) for the shared Python environment and [the helper catalog](../SCRIPTS.md) for requirements.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Inventory helper and plist parsing | On macOS, install the official Python package; on Debian/Ubuntu, use `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/macos/) | `python3 --version` |
| plistlib | Read XML and binary property lists | Included in Python's standard library; no extra package. [Source](https://docs.python.org/3/library/plistlib.html) | `python3 -c "import plistlib; print(plistlib.__name__)"` |
| Mandiant macos-UnifiedLogs | Parse acquired Unified Logs into CSV/JSONL | Download a compatible [release](https://github.com/mandiant/macos-UnifiedLogs/releases) or build `unifiedlog_iterator` with Rust/Cargo as shown below. [Source](https://github.com/mandiant/macos-UnifiedLogs/blob/main/BUILDING.md) | `unifiedlog_iterator --help`; `unifiedlog_iterator --version` |

Choose a unified-log or keychain parser compatible with the acquired format and OS version. Neither the inventory helper nor plistlib decrypts a keychain or parses raw unified-log stores.

## Script and command recipe

Helper: [inventory.py](../scripts/helpers/inventory.py). Run from the repository root with an existing case directory outside the repository:

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work"
python3 scripts/helpers/inventory.py "$CASE/extracts/Library/LaunchDaemons" > "$CASE/work/launchdaemons-inventory.jsonl"
python3 - "$CASE/extracts/System/Library/CoreServices/SystemVersion.plist" <<'PYCODE'
import plistlib
import pprint
import sys
from pathlib import Path
with Path(sys.argv[1]).open('rb') as source:
    pprint.pp(plistlib.load(source))
PYCODE
```

Replace the paths with those in your extraction. The inventory reports file hashes and host metadata; extracted-file mtimes are not necessarily original macOS timestamps. The plist reader prints parsed values and supports XML/binary plists. A parse error should be investigated rather than treated as an empty artifact.

## macOS pivots

| Location | Use |
| --- | --- |
| `/System/Library/CoreServices/SystemVersion.plist` | OS version/build |
| User `.zsh_history` | Commands and possible extended timestamps |
| `/Library/LaunchDaemons`, `/Library/LaunchAgents`, user `Library/LaunchAgents` | Persistence definitions |
| `/private/tmp` | Temporary payloads; `/tmp` commonly resolves here |
| User `Library/Keychains` | Protected secrets; choose a format-compatible parser |
| Unified logs | Process, service, and account activity |

Read a plist portably:

```bash
python3 - <<'PYCODE'
import plistlib
from pathlib import Path
p = Path('extracts/System/Library/CoreServices/SystemVersion.plist')
print(plistlib.loads(p.read_bytes()))
PYCODE
```

Use a unified-log parser appropriate to the acquisition. In **wilson disaster**, email, shell history, a helper binary, unified logs, and a file-timestamp-derived key connected the stages. Preserve the distinction between the observed timestamp and the answer accepted by the challenge service.

## Unified logs with Mandiant

[Mandiant macos-UnifiedLogs](https://github.com/mandiant/macos-UnifiedLogs) provides a cross-platform Rust parser. The current example executable is `unifiedlog_iterator`; older instructions in `RUNNING.md` refer to different binaries. These commands follow the [iterator CLI source](https://github.com/mandiant/macos-UnifiedLogs/blob/main/examples/unifiedlog_iterator/src/main.rs). Check the help output for your selected release.

### Build and verify

Install Rust/Cargo using the [official Rust instructions](https://www.rust-lang.org/tools/install) and the platform prerequisites in [BUILDING.md](https://github.com/mandiant/macos-UnifiedLogs/blob/main/BUILDING.md). Build the example workspace, not just the library:

```bash
UL_TOOLS=/absolute/path/to/tools
mkdir -p "$UL_TOOLS"
git clone https://github.com/mandiant/macos-UnifiedLogs.git "$UL_TOOLS/macos-UnifiedLogs"
cargo build --release --manifest-path "$UL_TOOLS/macos-UnifiedLogs/examples/Cargo.toml" --bin unifiedlog_iterator
UL_PARSER="$UL_TOOLS/macos-UnifiedLogs/examples/target/release/unifiedlog_iterator"
"$UL_PARSER" --help
"$UL_PARSER" --version
git -C "$UL_TOOLS/macos-UnifiedLogs" rev-parse HEAD
```

Record the source commit and compiler version with your case. Prebuilt binaries are an alternative; set `UL_PARSER` to the downloaded executable's full path. Windows builds use the `.exe` suffix and require the C++ build tools described upstream.

### Prepare an offline archive

Keep the complete `.logarchive` and its supporting data together. For an extracted filesystem, upstream documents combining the contents of `/private/var/db/uuidtext` and `/private/var/db/diagnostics` in a new archive directory. Preserve the originals and directory structure, including timesync and string data. A lone `.tracev3` may lack information needed to resolve timestamps or messages. See [the acquisition/layout notes](https://github.com/mandiant/macos-UnifiedLogs/blob/main/RUNNING.md#manually-create-logarchive).

### Export and inspect

With `CASE` and `UL_PARSER` set to your case directory and executable:

```bash
mkdir -p "$CASE/work"
# Bash noclobber prevents replacement of existing reports.
(
  set -o noclobber
  "$UL_PARSER" --mode log-archive --input "$CASE/evidence/system.logarchive" \
    --format csv > "$CASE/work/unifiedlogs.csv" 2> "$CASE/work/unifiedlogs.stderr.txt"
)
```

Use `--format jsonl` with a new output filename for JSONL. This example redirects stdout rather than using `--output`: the inspected source opens that destination in append mode. Review stderr and actual records; a zero exit code alone does not guarantee complete parsing. Output can be large, and records need not arrive in chronological order.

Filter CSV with a CSV-aware reader so quoted commas and multiline messages remain intact:

```bash
python3 - "$CASE/work/unifiedlogs.csv" <<'PYCODE'
import csv
import json
import sys
with open(sys.argv[1], newline='', encoding='utf-8') as source:
    for row in csv.DictReader(source):
        fields = ('Process', 'Subsystem', 'Message')
        haystack = ' '.join(row.get(field, '') or '' for field in fields).lower()
        if any(term in haystack for term in ('launchd', 'sudo', 'ssh')):
            print(json.dumps(row))
PYCODE
```

These keywords are starting points, not indicators by themselves. Pivot by timestamp, process, PID, subsystem, and boot UUID. Missing UUID/string data can yield incomplete messages; upstream also notes unsupported object encodings and differences from native error-message rendering. Preserve warnings and compare relevant records with another parser when necessary. See [upstream limitations](https://github.com/mandiant/macos-UnifiedLogs#limitations).

The commands were checked against upstream source and for shell syntax; parsing a real logarchive has not been reproduced here.

## Launch agents and daemons

Inspect both system-wide and per-user launch definitions. Read `Label`, `Program`, `ProgramArguments`, `RunAtLoad`, `KeepAlive`, and scheduling fields when present. Resolve referenced executables and environment values against the acquired filesystem.

Use the same plist parser on a selected definition:

```bash
python3 - "$CASE/extracts/Library/LaunchDaemons/example.plist" <<'PYCODE'
import plistlib
import pprint
import sys
from pathlib import Path
with Path(sys.argv[1]).open('rb') as source:
    job = plistlib.load(source)
for field in ('Label', 'Program', 'ProgramArguments', 'RunAtLoad', 'KeepAlive',
              'StartInterval', 'StartCalendarInterval', 'EnvironmentVariables'):
    if field in job:
        print(field)
        pprint.pp(job[field])
PYCODE
```

The filename is illustrative. A launch definition establishes configuration, not successful execution. Correlate the executable's hash, file metadata, and log records. Inspect recovered definitions without loading them into launchd.

## Correlate host activity

- Identify the acquired OS version and user directories before resolving paths.
- Preserve shell-history bytes and any recorded timestamps; a recorded command does not establish success.
- Keep plist files, quarantine/provenance artifacts, application databases, keychains, and unified-log archives when included in the collection.
- Separate per-user LaunchAgents from system-wide launch definitions when identifying the affected account.
- Record the acquisition scope and parser version; missing records may reflect collection or parsing limits.

Use [browser and messaging](../Browser-and-Messaging/README.md) for profile data and [timestamps](../Timestamps-and-Timelines/README.md) for epoch/timezone conversion. Keep observed timestamps separate from challenge-service accepted answers.

## LaunchAgent and staged-command correlation

For each acquired LaunchAgent/LaunchDaemon, inspect the plist as data, then the target file and associated logs. On a macOS analysis host:

```bash
plutil -lint work/com.example.agent.plist
plutil -p work/com.example.agent.plist
shasum -a 256 work/agent-binary
file work/agent-binary
strings -a work/agent-binary > work/agent-strings.txt
rg -n -i 'https?://|token|nonce|launch|package' work/agent-strings.txt
```

Map `Label`, `Program`/`ProgramArguments`, `RunAtLoad`, `KeepAlive`, environment, working directory, and output paths. A label resembling `com.apple.*` is not a signature or trust decision; verify the target, source location, user/system scope, and supporting execution evidence. A plist's presence alone does not prove it loaded. Source: [Apple launchd jobs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html).

The [RECURSION macOS case](https://2byte36.github.io/blog/recursion-2-final) combines chat, application logs, LaunchAgent persistence, staged crypto, and package-service traffic. For similar evidence, preserve request headers, package/version identifiers, polling intervals, task/result ordering, and the precise key derivation. A legitimate package service hostname does not explain the content carried through it. Use [Mandiant Unified Logs](#unified-logs-with-mandiant), [network extraction](../Network-Forensics/README.md), and [crypto validation](../Malware-Recovery/README.md) to test each connection.

## References

- [Mandiant macos-UnifiedLogs](https://github.com/mandiant/macos-UnifiedLogs)
- [Mandiant build instructions](https://github.com/mandiant/macos-UnifiedLogs/blob/main/BUILDING.md)
- [Current iterator implementation and CLI](https://github.com/mandiant/macos-UnifiedLogs/blob/main/examples/unifiedlog_iterator/src/main.rs)
- [Python for macOS](https://www.python.org/downloads/macos/)
- [Python plist reader](https://docs.python.org/3/library/plistlib.html)
- [Apple — creating launch daemons and agents](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [ARA final — wilson disaster](https://2byte36.github.io/blog/ara-7-final)
