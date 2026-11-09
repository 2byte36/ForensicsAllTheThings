# Linux artifacts

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Follow Linux account activity, persistence, application data, and filesystem history from an offline acquisition. For Apple host artifacts, use the separate [macOS guide](../macOS-Forensics/README.md).

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Linux artifact map](#linux-artifact-map)
- [Persistence and hidden files](#persistence-and-hidden-files)
- [Container layer recovery](#container-layer-recovery)
- [General host investigation checklist](#general-host-investigation-checklist)
- [Offline journals, SSH, and deleted history](#offline-journals-ssh-and-deleted-history)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| file / strings / xxd / rg | Type, bytes, and string triage | `sudo apt install file binutils xxd ripgrep coreutils`. [Source](https://github.com/BurntSushi/ripgrep#installation) | `file --version`; `rg --version` |
| Git | Local repository history | `sudo apt install git`. [Source](https://git-scm.com/downloads) | `git --version` |
| Skopeo | OCI/archive conversion | `sudo apt install skopeo`. [Source](https://github.com/containers/skopeo/blob/main/install.md) | `skopeo --version` |
| dive | Container layer inspection | Download a platform release/package using upstream installation instructions. [Source](https://github.com/wagoodman/dive#installation) | `dive --version` |

## Script and command recipe

Helper: [inventory.py](../scripts/helpers/inventory.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/inventory.py "$CASE/extracts/etc" > "$CASE/work/etc-inventory.jsonl"
rg -n -i "ExecStart|EnvironmentFile|LD_PRELOAD" "$CASE/extracts/etc"
```

Hashes extracted configuration before searching persistence definitions. Host mtimes of extracted files are not original filesystem times. Use the system journal/history commands below to establish execution.

## Linux artifact map

| Location | Investigative use |
| --- | --- |
| `/var/log/auth.log*`, `/var/log/secure*` | SSH, sudo, account and authentication activity |
| `/var/log/syslog*`, journal files | Service activity and unexpected embedded data |
| User `.bash_history`, `.zsh_history`, `.python_history` | Commands and developer activity; timestamps may be absent |
| `/etc/crontab`, `/etc/cron.d`, spool crontabs | Scheduled persistence |
| `/etc/systemd/system`, user systemd directories | Services, timers, drop-ins, environment values |
| `/etc/ld.so.preload` | Libraries loaded into dynamically linked processes |
| `/tmp`, `/var/tmp`, `/dev/shm` | Staging, temporary payloads, encrypted output |
| `/var/lib/docker`, `/var/lib/containerd` | Images, snapshots, logs, deleted-in-later-layer files |

```bash
rg -n -i 'Accepted|Failed|sudo|COMMAND=|session opened' extracts/var/log/auth.log
zcat extracts/var/log/auth.log.2.gz > work/auth-rotated.txt
journalctl --directory=extracts/var/log/journal --utc --no-pager > work/journal.txt
last -f extracts/var/log/wtmp -F
```

Account for rotated logs, missing history, timezone configuration, and timestamp manipulation. History describes recorded commands, not guaranteed successful execution.

## Persistence and hidden files

Read service `ExecStart`, environment files, cron jobs, preload entries, and referenced scripts as text. Analyze an offline copy with trusted tools: a compromised live system's utilities may hide files or alter output.

**Whisper From The Basement** involved an `LD_PRELOAD` directory-hiding hook plus timer and cron persistence. **Wulung-2604** progressed through suspicious timestamp changes and nearby timeline events. **Tombstone** used a cron-provided environment value and file xattrs in encryption.

## Container layer recovery

```bash
# For an extracted OCI layout directory:
skopeo copy oci:extracted-layout docker-archive:work/image.tar
# Inspect the resulting archive with a compatible dive build:
dive --source docker-archive work/image.tar
```

Read manifest/config data to identify layer order and build history. A deletion in a later layer does not erase bytes from an earlier layer; whiteout entries describe deletions. Extract the relevant older layer without starting the container.

**Layers** recovered a file from a historical COPY layer. **Breached** required searching container snapshots for web logs and distinguishing host paths from paths inside the container.

## General host investigation checklist

- Resolve the installed OS and users from system files before interpreting paths or IDs.
- Inspect SSH `authorized_keys`, configuration includes, and authentication logs together.
- Review systemd unit drop-ins and referenced environment files, not only the main unit.
- Correlate package-manager history with binaries and service installation times.
- Keep user-level persistence separate from system-level persistence.

A command in a service definition proves configuration, not that the service ran. A library listed in `ld.so.preload` may have been removed or replaced by acquisition time. Use logs, hashes, and file metadata to establish the observed state.

For image layers and repository history, continue with [cloud and containers](../Cloud-and-Containers/README.md). For normalization across host logs, see [timestamps](../Timestamps-and-Timelines/README.md).

## Offline journals, SSH, and deleted history

Use the acquired journal directory, not the analyst machine's live journal. The existing systemd tools can inspect a working copy:

```bash
journalctl --directory=work/journal --verify
journalctl --directory=work/journal --list-boots
journalctl --directory=work/journal --utc --no-pager -o short-iso-precise > work/journal-utc.txt
journalctl --directory=work/journal --utc --no-pager -o json > work/journal.jsonl
rg -n -i 'sshd|sudo|session opened|authentication failure|cron' work/journal-utc.txt
```

`--verify` checks journal structure; authenticity verification needs the corresponding sealing material. Separate boot IDs and realtime versus monotonic timestamps. Correlate SSH source/account, authorized key files, sudo command/TTY, shell history, systemd/cron definitions, and resulting files. Unit names vary (`ssh.service` versus `sshd.service`), so inspect available records before filtering by unit. Source: [journalctl manual](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html).

A missing `.bash_history` is not proof no commands ran: history may be disabled, unflushed, redirected, or deleted. Look for other shells, root and service-account homes, editor backups, journal/audit records, memory, and filesystem recovery. Bash `#<epoch>` lines only timestamp commands if those records were actually saved; do not invent timestamps for plain lines.

[RECURSION development](https://2byte36.github.io/blog/recursion-2-final) combines Linux memory and encrypted disk recovery; [Schematics Ambatuboot](https://2byte36.github.io/blog/schematics-2026-quals) motivates residual/deleted-content searches. Follow [MemNixFS/Volatility](../Memory-Forensics/README.md#memprocfs-and-linux-memnixfs) and [read-only disk recovery](../Disk-Forensics/README.md) when disk logs are incomplete. A recovered LUKS volume key is not the user's passphrase; keep key length, cipher/mode, and volume association explicit.

## References

- [systemd unit documentation](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html)
- [NCLP — Layers and Whisper From The Basement](https://2byte36.github.io/blog/nclp-ctf-s1)
- [Wreck-IT — Wulung-2604](https://2byte36.github.io/blog/wreck-it-7-quals)
- [GEMASTIK — Tombstone](https://2byte36.github.io/blog/gemastik-19-quals)
- [C2C — Breached](https://2byte36.github.io/blog/c2c26-quals)
