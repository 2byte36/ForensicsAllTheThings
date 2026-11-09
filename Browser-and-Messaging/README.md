# Browser and messaging artifacts

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Identify the right profile and protection layers before querying history or attempting decryption.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Collect the complete profile](#collect-the-complete-profile)
- [Query a working copy](#query-a-working-copy)
- [Encrypted browser secrets](#encrypted-browser-secrets)
- [Signal, Outlook, and chat data](#signal-outlook-and-chat-data)
- [Firefox history and download context](#firefox-history-and-download-context)
- [Correlate rather than equate](#correlate-rather-than-equate)
- [Cache, downloads, and ClickFix](#cache-downloads-and-clickfix)
- [Sessions, unsaved text, and local application stores](#sessions-unsaved-text-and-local-application-stores)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| SQLite CLI | Copied database queries | `sudo apt install sqlite3`. [Source](https://www.sqlite.org/download.html) | `sqlite3 --version` |
| dfindexeddb | IndexedDB/LevelDB parsing | Follow the project installation instructions in a separate venv. [Source](https://github.com/google/dfindexeddb#installation) | Use the installed CLI help listed upstream |
| pypykatz | LSASS/DPAPI parsing | In the Python venv: `python -m pip install pypykatz`. [Source](https://github.com/skelsec/pypykatz#installation) | `pypykatz --help` |

## Script and command recipe

Helper: [browser_history.py](../scripts/helpers/browser_history.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/browser_history.py chromium "$CASE/work/profile/History" --limit 1000 > "$CASE/work/chromium-visits.jsonl"
python3 scripts/helpers/browser_history.py firefox "$CASE/work/firefox/places.sqlite" --limit 1000 > "$CASE/work/firefox-visits.jsonl"
```

Reads a copied database in SQLite read-only mode and exports visit rows, raw timestamps, UTC seconds, URLs, and titles. Preserve originals and matching sidecars first. Schema mismatch returns an error; this is not a password/chat decryptor.

## Collect the complete profile

For Chromium-based applications, preserve `History`, `Login Data`, cookie databases, `Local State`, IndexedDB/LevelDB stores, and SQLite sidecars. Search `Default`, `Profile 1`, and other profiles. For Firefox, inspect `places.sqlite` and the matching profile's login/key files.

Windows Chromium profiles commonly live under `AppData/Local/<vendor>/<browser>/User Data`. Electron applications often store data under `AppData/Roaming/<application>`. These locations and encryption schemes vary by application and version.

## Query a working copy

Preserve originals and sidecars first; see [SQLite and WAL](../SQLite-and-WAL/README.md). Then inspect a copied, coherent database set:

```bash
sqlite3 -readonly work/browser/History '.tables'
sqlite3 -readonly work/browser/History '.schema urls'
sqlite3 -readonly work/browser/History "
SELECT datetime(last_visit_time / 1000000.0 - 11644473600, 'unixepoch') AS utc,
       url, title, visit_count
FROM urls ORDER BY last_visit_time DESC LIMIT 50;"
sqlite3 -readonly work/browser/History '.schema downloads'
sqlite3 -readonly work/browser/History '.schema downloads_url_chains'
```

Chromium times here are microseconds since 1601; do not apply that conversion to every browser or table. `urls.last_visit_time` is only the latest visit; join the `visits` table for individual visit events. Inspect the schema before writing download queries.

## Encrypted browser secrets

Map the format before decrypting:

1. Determine application version and encrypted blob prefix.
2. Recover the correct user's DPAPI master key when applicable.
3. Decode and unwrap the application key from the relevant configuration.
4. Parse nonce, ciphertext, and tag according to that blob version.
5. Verify authentication and interpret plaintext encoding.

Newer application-bound encryption and platform-specific protection can require more than a user password and `Local State`. Do not assume an older DPAPI/AES recipe applies universally.

**Traitor** used `Profile 1`, not `Default`. The supplied evidence supported its DPAPI recovery chain; the exact steps belong to that application version.

## Signal, Outlook, and chat data

- **Signal:** collect configuration, encrypted database, and relevant key-protection files together. **gratisan mulu sih** required unwrapping the configuration key and interpreting its hex encoding before export.
- **New Outlook:** inspect the `Olk/EBWebview` browser-backed store. **The Apex Affair** recovered mail metadata from IndexedDB/LevelDB using `dfindexeddb`.
- **Zoom and other encrypted chat stores:** identify the application-specific key wrapping, database cipher settings, and DPAPI requirements before selecting a tool.

A partial parser result may still contain useful records; preserve its errors and treat truncated fields as incomplete. Correlate message timestamps, attachments, download records, and execution artifacts rather than assuming a downloaded file was launched.

## Firefox history and download context

On a preserved working copy of the Firefox profile:

```bash
sqlite3 -readonly work/firefox/places.sqlite '.schema moz_historyvisits'
sqlite3 -readonly work/firefox/places.sqlite "
SELECT datetime(v.visit_date / 1000000.0, 'unixepoch') AS utc,
       p.url, p.title, v.visit_type
FROM moz_historyvisits AS v JOIN moz_places AS p ON p.id = v.place_id
ORDER BY v.visit_date DESC LIMIT 100;"
```

Firefox visit timestamps here use Unix microseconds, unlike Chromium's 1601 epoch. Inspect schema and application version for download metadata, session recovery, and cache formats. Preserve `logins.json` with its matching key database when investigating saved credentials.

## Correlate rather than equate

A history row indicates a recorded browser event, not necessarily deliberate user navigation. Redirects, background requests, sync, and prefetching can contribute records. Use visit type, referrer chains, downloaded target paths, file hashes, and execution artifacts to distinguish browsing, download completion, and execution.

Cookie expiry is not the time a user last logged in. Cached content is not proof that the visible page displayed it. Keep raw URL encoding and query strings alongside normalized values.

## Cache, downloads, and ClickFix

ChromeCacheView is already in the local Windows toolbox. Download/unpack it from [NirSoft's setup and CLI page](https://www.nirsoft.net/utils/chrome_cache_view.html); no custom helper is needed. In the GUI, use **File → Select Cache Folder** and choose the acquired profile's cache, then search URL/content type and copy selected entries to the case output. For current Chromium layouts, inspect `Cache\Cache_Data`; preserve the entire cache directory.

PowerShell:

```powershell
$CacheView = 'C:\Users\ACER\dfir_tools\chromecacheview\ChromeCacheView.exe'
& $CacheView -folder 'C:\cases\browser\profile\Cache\Cache_Data' /scomma 'C:\cases\browser\reports\cache.csv'
```

Hash exported bodies and retain their URL/cache metadata. Server time, cache access time, browser visit time, and extraction time describe different events. Review recovered JavaScript as text; a cache entry does not prove code execution.

For copied Chromium/Edge History databases, inspect schemas first, then query individual visits and download chains:

```bash
sqlite3 -readonly work/browser/History '.schema visits'
sqlite3 -readonly work/browser/History '.schema downloads'
sqlite3 -readonly work/browser/History '.schema downloads_url_chains'
sqlite3 -readonly -header -csv work/browser/History "
SELECT v.id, v.visit_time AS raw_time,
       datetime(v.visit_time/1000000.0-11644473600,'unixepoch') AS utc,
       v.visit_duration/1000000.0 AS recorded_duration_seconds,
       v.from_visit, v.transition, u.url
FROM visits v JOIN urls u ON u.id=v.url ORDER BY v.visit_time;" > work/visits.csv
sqlite3 -readonly -header -csv work/browser/History "
SELECT d.id, d.target_path, d.start_time, d.end_time, d.state,
       d.received_bytes, d.total_bytes, c.chain_index, c.url
FROM downloads d LEFT JOIN downloads_url_chains c ON c.id=d.id
ORDER BY d.start_time, d.id, c.chain_index;" > work/downloads.csv
```

The recorded visit duration is not proof of continuous human attention. Zero/unset end times should not become historical dates. Interpret download states and byte counts using the browser version, then verify the target file/hash. Source schemas: [Chromium visits](https://github.com/chromium/chromium/blob/main/components/history/core/browser/visit_database.cc), [downloads](https://github.com/chromium/chromium/blob/main/components/history/core/browser/download_database.cc).

In [GotFish](https://2byte36.github.io/blog/tryhards-ctf-2026), cached JavaScript and [RunMRU](../Windows-Registry/README.md#user-activity-and-execution) expose the ClickFix input chain. Compare exact strings, profile/SID, and times with process/PowerShell evidence before asserting execution.

## Sessions, unsaved text, and local application stores

| Store | Collect and inspect | Limit |
| --- | --- | --- |
| Chromium sessions | Profile `Sessions` and available older session files | Open/closed tab context is not equivalent to a new navigation |
| Firefox sessions | `sessionstore-backups` and matching profile | Compressed/session-specific format; do not treat as plain JSON without decoding |
| Sublime Text | `AppData\Roaming\Sublime Text\Local\Session.sublime_session` | Can retain buffers/unsaved text; exact keys/version vary |
| Electron/Discord renderer memory | Correct process dump plus local profile/LevelDB | Strings can be stale, duplicated, or unrelated to the visible channel |
| Delta Chat | Acquired account database, configuration, contacts and messages | Inspect schema and encryption before querying; do not assume a browser schema |

For an acquired JSON Sublime session, inspect keys and strings directly:

```bash
jq 'keys' work/Session.sublime_session
jq -r '.. | strings' work/Session.sublime_session > work/session-strings.txt
rg -n -i 'note|key|invoice|password' work/session-strings.txt
```

Retain the original object path when a string matters; flattened output is only triage. GotFish demonstrates unsaved editor evidence; [RECURSION 2.0](https://2byte36.github.io/blog/recursion-2-final) contributes a Delta Chat/macOS example. See the [existing Discord parser recipe](../Memory-Forensics/README.md#user-minidumps-and-existing-discord-parser) for memory-specific limits.

## References

- [Mozilla Places design](https://firefox-source-docs.mozilla.org/toolkit/components/places/index.html)
- [Chromium time representation](https://chromium.googlesource.com/chromium/src/+/main/base/time/time.h)
- [ITFEST — Traitor](https://2byte36.github.io/blog/itfest-2026)
- [IFEST quals — gratisan mulu sih](https://2byte36.github.io/blog/ifest-2026-quals)
- [Compfest — The Apex Affair](https://2byte36.github.io/blog/compfest18-quals)
- [Google dfindexeddb](https://github.com/google/dfindexeddb)
