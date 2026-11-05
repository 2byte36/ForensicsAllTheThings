# SQLite and WAL recovery

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Historical and uncommitted page versions can contain data absent from the current database.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Preserve before opening](#preserve-before-opening)
- [Understand the layout](#understand-the-layout)
- [Reconstruct a candidate state](#reconstruct-a-candidate-state)
- [Inspect uncommitted and deleted data](#inspect-uncommitted-and-deleted-data)
- [Challenge-derived recovery paths](#challenge-derived-recovery-paths)
- [Schema-first database queries](#schema-first-database-queries)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| SQLite CLI | Copied database queries | `sudo apt install sqlite3`. [Source](https://www.sqlite.org/download.html) | `sqlite3 --version` |

## Script and command recipe

Helper: [wal_frames.py](../scripts/helpers/wal_frames.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/wal_frames.py "$CASE/work/database.db-wal" > "$CASE/work/wal-frames.jsonl"
```

Validates the WAL header, salts, and rolling checksums before listing frame offsets, page numbers, and commit sizes. A failure returns nonzero and leaves a prefix report. No replay, decryption, or guarantee of consistency with a chosen base database.

## Preserve before opening

Copy the main database, `-wal`, and `-shm` files as a set from a consistent acquisition. Hash them before using any SQLite client. An ordinary open/close workflow can checkpoint or remove sidecars under some conditions; use disposable copies for analysis.

A read-only connection is useful for queries but does not guarantee that every client workflow preserves historical sidecars. `immutable=1` is also not a WAL-history recovery method. Keep an untouched evidence set.

## Understand the layout

A WAL begins with a 32-byte header. Each frame has a 24-byte header followed by one database page.

| Field | Meaning |
| --- | --- |
| WAL header page size | Page payload size used for frame stepping |
| Frame page number | Which database page this frame replaces |
| Frame database size | Nonzero on the final frame of a committed transaction |
| Frame salts | Must match the WAL generation |
| Rolling checksums | Validate the header/frame chain using the format's byte order |

For page size `P`, frame `i` (one-based) starts at `32 + (i - 1) * (24 + P)`. Its page bytes start 24 bytes later. In the main database, page `n` begins at `(n - 1) * P`.

Validate magic, supported page size, frame lengths, salts, and rolling checksums. A nonzero commit marker in a corrupt or stale frame is not sufficient evidence of a valid transaction.

## Reconstruct a candidate state

1. Identify the correct base database and compatible WAL generation.
2. Select a checksum-valid transaction boundary.
3. Make a separate candidate database copy.
4. Replay frames through that boundary in order, replacing each numbered page.
5. Apply the committed database-size field to the reconstructed file size.
6. Open the candidate without unrelated sidecars and check its structure.

```bash
sqlite3 -readonly work/candidate.db 'PRAGMA integrity_check;'
sqlite3 -readonly work/candidate.db '.tables'
sqlite3 -readonly work/candidate.db '.schema'
```

A database already checkpointed past the historical state may not be reversible using only the surviving WAL: older versions of untouched pages may be missing. Document that limit instead of labeling every replay as a valid historical snapshot.

## Inspect uncommitted and deleted data

Retain uncommitted frames as separate forensic candidates. They can contain useful bytes, but they do not prove a committed application state. Compare multiple versions of the same page, including overflow chains, and correlate row/attachment identifiers.

SQLite `.recover` may help salvage damaged database content, but is not a general deleted-row or WAL-history reconstruction tool:

```bash
sqlite3 work/damaged-copy.db '.recover' > work/recovered.sql
sqlite3 work/recovered.db < work/recovered.sql
```

## Challenge-derived recovery paths

**revenant:** enumerate frames and commits → compare versions of a changed page → rebuild selected states → match attachment bytes → decrypt the relevant attachment. Its frame ranges and page 52 were challenge-specific.

**cinder:** preserve WAL history → inspect encrypted records → recover parameters from Android `shared_prefs/secure_prefs.xml` → decrypt the historical payload. A standard SQLite query cannot decrypt application-level ciphertext on its own.

## Schema-first database queries

After preservation, query a disposable working copy:

```bash
sqlite3 -readonly work/copy.db "SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name;"
sqlite3 -readonly work/copy.db 'PRAGMA page_size; PRAGMA freelist_count;'
# Replace messages with a table actually present in the schema.
sqlite3 -readonly work/copy.db 'PRAGMA table_info(messages);'
```

Check column types and sample values before decoding timestamps or blobs. A BLOB can contain compressed, serialized, or encrypted data. A freelist count indicates pages available for reuse, not a count of recoverable deleted records. VACUUM, secure deletion, overwritten pages, and incomplete acquisition can remove recoverable history.

A `-journal` file uses rollback-journal semantics; it is not a WAL and cannot be parsed with the WAL frame layout. SQLCipher and application-level encryption require the matching crypto parameters before ordinary SQLite interpretation.

## References

- [SQLite database format](https://www.sqlite.org/fileformat.html)
- [SQLite PRAGMA reference](https://sqlite.org/pragma.html)
- [SQLite WAL format](https://www.sqlite.org/walformat.html)
- [SQLite recovery](https://www.sqlite.org/recovery.html)
- [JOINTS — revenant](https://2byte36.github.io/blog/joints-2026-quals)
- [GEMASTIK — cinder](https://2byte36.github.io/blog/gemastik-19-quals)
