# Investigation methodology

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

A repeatable path from an unfamiliar attachment to an evidence-backed answer.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Preserve and inventory](#preserve-and-inventory)
- [Investigate one question at a time](#investigate-one-question-at-a-time)
- [Build an evidence chain](#build-an-evidence-chain)
- [Recover and validate](#recover-and-validate)
- [Avoid dead ends](#avoid-dead-ends)
- [Choose the next technique by evidence](#choose-the-next-technique-by-evidence)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| file / strings / xxd / rg | Type, bytes, and string triage | `sudo apt install file binutils xxd ripgrep coreutils`. [Source](https://github.com/BurntSushi/ripgrep#installation) | `file --version`; `rg --version` |

## Script and command recipe

Helper: [inventory.py](../scripts/helpers/inventory.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/inventory.py "$CASE/evidence" > "$CASE/work/inventory.jsonl"
```

One JSON record per regular file with size, SHA-256, and host mtime. Symlinks/special files are skipped. Keep the report outside the input tree; hash a frozen evidence copy.

## Preserve and inventory

Hash the supplied archive and extracted primary artifacts. Work on copies; preserve image metadata and database sidecars. Keep a short inventory of file type, size, hash, acquisition context, and expected parser.

```bash
find evidence -type f -print0 | sort -z | xargs -0 sha256sum > work/hashes.txt
find evidence -type f -print0 | xargs -0 file > work/types.txt
```

Do not treat a filename as a format specification. A `.raw` may contain an ELF/QEMU dump, and a media filename may contain an archive.

## Investigate one question at a time

1. Capture the exact question and answer format.
2. Identify the artifact most likely to contain direct evidence.
3. Run a narrow query and save the result.
4. Correlate the candidate with a second artifact when possible.
5. Record the answer and server response before advancing.

Use [case notes](../templates/case-notes.md). If an answer fails, retain it with the reason for the revision. A server accepting a guess does not explain the underlying artifact; record that limitation.

## Build an evidence chain

A useful chain is email attachment → download → execution → persistence → C2 → file access → exfiltration or encryption. Link records by filename, hash, PID and process start time, user SID, session cookie, socket, or timestamp.

A process name alone is weak evidence. A missing User-Agent or unusual port can identify a useful pivot, but neither proves maliciousness. Distinguish an observed fact from an inference and from a source-reported challenge answer.

## Recover and validate

Keep separate copies of original bytes, decoded intermediate stages, and recovered output. For every transformation record its input, parameters, output path, and hash. Validate a recovered file structurally before looking for its flag.

Useful checks include archive integrity, image decoding, PDF parsing, database integrity, CRCs, and authenticated-decryption tags. A recognizable header alone is insufficient to validate a whole file.

## Avoid dead ends

- Inventory all supplied artifacts before deep reversing; a key may be in a log or xattr.
- Follow process ancestry when the named executable is missing.
- Search every Chromium profile, not only `Default`.
- Inspect timestamps near a suspicious event rather than scanning an entire image manually.
- Preserve contradictory evidence. Some writeups contain accepted answers based on guesses or inconsistent question counts.

## Choose the next technique by evidence

Use the [quick reference](../QUICKSTART.md) to classify the artifact, then prioritize a question that the artifact can answer directly. Build a short hypothesis list with expected evidence and a stopping condition for each branch.

Separate three labels in notes: **observed** (direct bytes/records), **inferred** (supported interpretation), and **source-reported** (another investigation's result). Prefer primary format/tool documentation for command semantics; use writeups as examples of reasoning and pivots.

Validate small transformations on synthetic data when possible. A correct decoder on a fixture establishes its mechanics, not the correctness of a guessed key, offset, or format in the real case. See the [reference library](../REFERENCES.md) for starting sources.

## References

- [NIST SP 800-86 — forensic techniques](https://csrc.nist.gov/pubs/sp/800/86/final)
- [2byte — CTF writeups](https://2byte36.github.io/blog/)
