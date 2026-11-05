# File triage and carving

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Identify the real format before choosing a parser or attempting recovery.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [First pass](#first-pass)
- [Extract an embedded region](#extract-an-embedded-region)
- [Repair a signature](#repair-a-signature)
- [Reassemble fragments](#reassemble-fragments)
- [Archive passwords](#archive-passwords)
- [Recovery decision tree](#recovery-decision-tree)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| file / strings / xxd / rg | Type, bytes, and string triage | `sudo apt install file binutils xxd ripgrep coreutils`. [Source](https://github.com/BurntSushi/ripgrep#installation) | `file --version`; `rg --version` |
| 7-Zip | Archive listing and extraction | `sudo apt install 7zip` (see SETUP.md for executable names). [Source](https://www.7-zip.org/download.html) | `7z i` or `7zz i` |
| ExifTool | Metadata | `sudo apt install libimage-exiftool-perl`. [Source](https://exiftool.org/install.html) | `exiftool -ver` |
| Binwalk | Embedded-format signatures | `sudo apt install binwalk`; use upstream build for a newer major version. [Source](https://github.com/ReFirmLabs/binwalk#installation) | `binwalk --help` |
| PhotoRec / TestDisk | Signature recovery | `sudo apt install testdisk`. [Source](https://www.cgsecurity.org/wiki/TestDisk_Download) | `photorec /version` |

## Script and command recipe

Helper: [carve.py](../scripts/helpers/carve.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/carve.py "$CASE/artifact.bin" "$CASE/carved/region.bin" --offset 0x1000 --length 4096
```

Copies the specified byte range and prints its hash. Replace the illustrative offset/length with measured boundaries; rejects out-of-range requests and existing output.

## First pass

```bash
file -k artifact
xxd -l 256 artifact
exiftool artifact
7z l artifact
binwalk artifact
strings -a -t x -n 6 artifact > work/strings-offsets.txt
```

Use `strings -el` for UTF-16LE. Offset output lets you return to the original bytes instead of treating an isolated string as a complete finding. Binwalk signatures are candidates and can be false positives.

## Extract an embedded region

After confirming the offset and size from the container structure:

```bash
# Example byte range; replace both values with measured boundaries.
dd if=artifact of=carved/region.bin bs=1 skip=4096 count=8192 status=none
file carved/region.bin
sha256sum carved/region.bin
```

List archives before extracting. Use a dedicated directory and inspect nested layers without running included programs. In **Vault**, a JPEG contained gzip data; in **pemanasan**, nested archives led to an image with a damaged signature.

## Repair a signature

Compare the actual structure with the suspected format before modifying a copy.

| Format | Starting bytes or marker |
| --- | --- |
| PNG | `89 50 4e 47 0d 0a 1a 0a` |
| JPEG | `ff d8 ff` |
| PDF | `%PDF-` |
| ZIP | Often `50 4b 03 04`; empty/spanned archives differ |
| ELF | `7f 45 4c 46` |
| PE | `MZ`, then a valid PE header at the offset in `e_lfanew` |
| SQLite | `SQLite format 3` followed by NUL |

For PNG, validate chunk lengths and CRCs. Changing IHDR width or height also changes the chunk CRC. **Evaporated** required signature and height repair; that is a case-specific repair, not a reason to blindly enlarge every PNG.

## Reassemble fragments

Find the header, trailer, internal offsets, sequence IDs, and expected total length. Reassemble by those constraints rather than filename order. Verify the recovered document with its native parser.

**tidak terurut** contained shuffled PDF fragments. **Traceee** used records with a `USBI` marker, a header, a big-endian length, and PNG bytes. Parse those record boundaries; concatenating full TCP packets would retain framing and retransmissions.

## Archive passwords

Start with nearby email, shell history, hints, and known password-generation logic. For legacy ZipCrypto, known plaintext may permit `bkcrack`; this does not apply to AES-encrypted ZIP entries. The known bytes must match the actual encrypted entry representation and compression method.

**Reward Runner** used predictable `.git/HEAD` content as known plaintext. Follow the original writeup for its exact archive parameters. Treat any executable recovered afterward as static evidence.

## Recovery decision tree

| Finding | Next step |
| --- | --- |
| Valid container with accessible directory | List and extract using its parser |
| Damaged container directory, intact members | Recover local records on a copy |
| Filesystem metadata available | Recover by inode/record before carving |
| Metadata missing, recognizable signatures | Carve; then validate length and internal structure |
| Encrypted or high-entropy region | Find producer/key material before blind carving |
| Multiple plausible formats | Inspect offsets and container relationships; possible embedded data or polyglot |

An apparent end marker can occur inside a payload; use format lengths, chunk tables, and parser checks to select boundaries. For file concatenations, retain the start offset of each extracted member and hash the exact byte range.

See [archive recovery](../Archives-and-Passwords/README.md), [encoding](../Encoding-and-Binary/README.md), and [search/YARA](../Search-and-YARA/README.md) for focused recipes.

## References

- [PhotoRec documentation](https://www.cgsecurity.org/wiki/PhotoRec)
- [GNU Binutils strings](https://sourceware.org/binutils/docs/binutils/strings.html)
- [Teknocomp — Vault and Traceee](https://2byte36.github.io/blog/teknocom-25)
- [NCLP — Evaporated and Reward Runner](https://2byte36.github.io/blog/nclp-ctf-s1)
- [GCW quals — tidak terurut](https://2byte36.github.io/blog/gcw-2026-quals)
- [Techcomfest quals — pemanasan](https://2byte36.github.io/blog/techcompfest-26-quals)
