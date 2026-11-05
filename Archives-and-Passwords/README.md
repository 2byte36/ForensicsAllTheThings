# Archives and password recovery

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Identify archive structure and encryption before choosing extraction, repair, or a bounded password search.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Inspect before extracting](#inspect-before-extracting)
- [Split and damaged archives](#split-and-damaged-archives)
- [Extract a verifier and try targeted candidates](#extract-a-verifier-and-try-targeted-candidates)
- [ZipCrypto known plaintext](#zipcrypto-known-plaintext)
- [Encryption versus encoding](#encryption-versus-encoding)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| 7-Zip | Archive listing and extraction | `sudo apt install 7zip` (see SETUP.md for executable names). [Source](https://www.7-zip.org/download.html) | `7z i` or `7zz i` |
| John Jumbo | Password verifier extraction/search | Install Jumbo from upstream; a minimal distro John may omit zip2john and other helpers. [Source](https://github.com/openwall/john/blob/bleeding-jumbo/doc/INSTALL) | `john --list=build-info` |
| Hashcat | Offline password search | Download a release and install the backend/runtime appropriate for your hardware. [Source](https://hashcat.net/hashcat/) | `hashcat --version`; `hashcat -I` |
| bkcrack | Legacy ZipCrypto recovery | Use upstream release binaries or its CMake build instructions. [Source](https://github.com/kimci86/bkcrack#install) | `bkcrack -h` |

## Script and command recipe

Helper: [zip_inventory.py](../scripts/helpers/zip_inventory.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/zip_inventory.py "$CASE/evidence.zip" > "$CASE/work/zip-members.jsonl"
```

Lists members without decompression or password guessing. Reports central-directory metadata; does not validate all entry payloads or prove that an encryption flag is truthful. Use 7-Zip testing and the recovery commands below for content validation.

## Inspect before extracting

```bash
7z l -slt evidence.zip
7z t evidence.zip
unzip -Z -v evidence.zip
tar -tvf evidence.tar
```

Check entry names, compressed/uncompressed sizes, method, encryption, comments, and volume numbering. An archive may contain mixed methods or only some encrypted entries. Password protection of content and encryption of filenames are different features.

Extract into a dedicated case directory after checking absolute paths, parent-directory traversal, and links. Preserve duplicate names and archive order when they matter; an ordinary extraction can overwrite an earlier entry.

## Split and damaged archives

Open the first volume with a format-aware tool (`.7z.001`, `.part1.rar`, or the format's appropriate starting file). Verify all parts and their order. Concatenate only when the evidence is a raw byte split, not a multi-volume format with per-volume structure.

For a damaged ZIP, try repair on a copy using Info-ZIP:

```bash
zip -FF damaged.zip --out work/repaired.zip
unzip -t work/repaired.zip
```

Local headers may survive when the central directory is damaged. Recovered entries can be incomplete; compare declared sizes, CRCs, and internal file structure. An entry marked encrypted is not by itself proof of valid ciphertext: inspect flags and headers when a CTF suggests metadata tampering, and retain the original bytes.

## Extract a verifier and try targeted candidates

John Jumbo includes format-specific extraction helpers; their installation paths vary:

```bash
zip2john evidence.zip > work/zip.hash
john --session=ctf-zip --wordlist=case-candidates.txt work/zip.hash
john --show work/zip.hash
```

Use the matching helper for RAR, 7z, PDF, Office, or another supported format. Identify the actual cipher/version from the extracted verifier. Hashcat uses its own input conventions and mode IDs; do not feed it a filename-prefixed John line without checking the mode's example format.

Build candidates from case evidence: document hints, nearby history, usernames, dates, or recovered password-generation logic. Start with a small justified list, then bounded rules or masks. Save session state and record the search space; failure to find a password does not prove the archive is corrupt.

## ZipCrypto known plaintext

`bkcrack` applies to legacy ZipCrypto, not AES ZIP encryption. It needs at least 12 known plaintext bytes, including 8 contiguous bytes, matching the encrypted entry's compressed-byte representation. A known uncompressed document is insufficient if the compressed stream differs.

```bash
# For a stored/uncompressed entry whose exact bytes are known:
bkcrack -C evidence.zip -c known.txt -p known.txt
# Substitute the three recovered internal keys:
bkcrack -C evidence.zip -k 11111111 22222222 33333333 -D work/unlocked.zip
```

The second line's keys are placeholders. Recovery of internal keys can unlock compatible entries without recovering the original password. Validate the resulting archive and each needed file.

## Encryption versus encoding

A Base64 wrapper is not password protection. A ZIP header does not imply all nested data is ZIP data. After every extraction, rerun `file` and inspect the next layer. For ransomware-wrapped archives, recover the outer crypto recipe first via [malware recovery](../Malware-Recovery/README.md).

## References

- [7-Zip](https://www.7-zip.org/)
- [Info-ZIP](https://infozip.sourceforge.net/)
- [John usage examples](https://www.openwall.com/john/doc/EXAMPLES.shtml)
- [John Jumbo source and helpers](https://github.com/openwall/john)
- [bkcrack documentation](https://github.com/kimci86/bkcrack)
- [Hashcat example hashes](https://hashcat.net/wiki/doku.php?id=example_hashes)
