# macOS artifacts

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Investigate macOS property lists, launchd persistence, shell history, keychains, and unified logs from an offline acquisition. For systemd, Linux authentication logs, and container storage, use the separate [Linux guide](../Linux-Forensics/README.md).

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [macOS pivots](#macos-pivots)
- [Launch agents and daemons](#launch-agents-and-daemons)
- [Correlate host activity](#correlate-host-activity)
- [References](#references)

## Tools and setup

The Python recipes work on macOS or a Linux analysis workstation. They inspect extracted files rather than the live system. See [SETUP.md](../SETUP.md) for the shared Python environment and [the helper catalog](../SCRIPTS.md) for requirements.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Inventory helper and plist parsing | On macOS, install the official Python package; on Debian/Ubuntu, use `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/macos/) | `python3 --version` |
| plistlib | Read XML and binary property lists | Included in Python's standard library; no extra package. [Source](https://docs.python.org/3/library/plistlib.html) | `python3 -c "import plistlib; print(plistlib.__name__)"` |

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

## References

- [Python for macOS](https://www.python.org/downloads/macos/)
- [Python plist reader](https://docs.python.org/3/library/plistlib.html)
- [Apple — creating launch daemons and agents](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [ARA final — wilson disaster](https://2byte36.github.io/blog/ara-7-final)
