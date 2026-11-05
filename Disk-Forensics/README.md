# Disk and filesystem forensics

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Locate partitions, recover files, and preserve metadata that may itself hold key material.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Choose the right image parser](#choose-the-right-image-parser)
- [Sleuth Kit workflow](#sleuth-kit-workflow)
- [Read-only filesystem access](#read-only-filesystem-access)
- [Extended attributes and timestamps](#extended-attributes-and-timestamps)
- [LUKS and LVM](#luks-and-lvm)
- [Recover deleted files and unallocated space](#recover-deleted-files-and-unallocated-space)
- [NTFS streams, journals, and snapshots](#ntfs-streams-journals-and-snapshots)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| Sleuth Kit | Filesystem analysis | `sudo apt install sleuthkit`. [Source](https://www.sleuthkit.org/sleuthkit/download.php) | `mmls -V` |
| PhotoRec / TestDisk | Signature recovery | `sudo apt install testdisk`. [Source](https://www.cgsecurity.org/wiki/TestDisk_Download) | `photorec /version` |
| libewf utilities | E01 inspection/export | `sudo apt install ewf-tools`. [Source](https://github.com/libyal/libewf/wiki/Building) | `ewfinfo -V` |
| cryptsetup | LUKS metadata and opening | `sudo apt install cryptsetup`. [Source](https://gitlab.com/cryptsetup/cryptsetup) | `cryptsetup --version` |
| Autopsy | GUI image examination | Download the platform release and follow its prerequisites. [Source](https://www.autopsy.com/download/) | Open Help/About |

## Script and command recipe

Helper: [carve.py](../scripts/helpers/carve.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/carve.py "$CASE/image.dd" "$CASE/carved/partition.bin" --offset 1048576 --length 1048576
```

This is byte carving, not partition discovery. The example starts at sector 2048 only for 512-byte sectors; derive offset and full length from the image before using it.

## Choose the right image parser

| Input | Starting point |
| --- | --- |
| Raw DD / IMG | Sleuth Kit, Autopsy |
| E01 | EWF-capable tool such as FTK Imager or Autopsy |
| AD1 | FTK Imager or a compatible logical-image extractor |
| VMDK / VHDX / OVA | Supporting image viewer; an OVA is an archive containing virtual-disk files |
| Corrupt image | Inspect container records and recover intact chunks on a copy |

A logical AD1 collection is not necessarily a sector-addressed disk. Do not apply partition offsets or raw carving assumptions to it without understanding the container. **minami** required a custom recovery of compressed AD1 chunks; its prefix lengths were specific to that artifact.

## Sleuth Kit workflow

```bash
mmls image.dd
# Example start sector from mmls; replace 2048 for your image.
fsstat -o 2048 image.dd
fls -r -p -o 2048 image.dd > work/files.txt
fls -r -d -p -o 2048 image.dd > work/deleted.txt
# Replace 12345 with the file metadata address from fls.
icat -o 2048 image.dd 12345 > extracts/recovered.bin
fls -r -m / -o 2048 image.dd > work/bodyfile.txt
mactime -b work/bodyfile.txt -z UTC -d > work/timeline.csv
```

`-o` uses sectors, not bytes. Verify the device sector size; provide the appropriate `-b` where needed. Recovery may fail if data blocks were overwritten or the logical collection omitted them.

## Read-only filesystem access

Prefer a forensic viewer. For a raw image on Linux, a loop device can expose partitions:

```bash
sudo losetup --find --show --read-only --partscan image.dd
# Use the actual returned device, not an assumed loop number.
# For an ext4 partition, suppress journal replay:
sudo mount -o ro,noload /dev/loop0p1 /mnt/evidence
# After analysis:
sudo umount /mnt/evidence
sudo losetup -d /dev/loop0
```

Create the mount point first. `noload` is ext-specific; use filesystem-appropriate options for other formats. Do not boot the seized operating system to inspect its files.

## Extended attributes and timestamps

```bash
getfattr -d -m - /mnt/evidence/path/to/file
getfattr -n user.luks_key --only-values /mnt/evidence/path/to/file
stat /mnt/evidence/path/to/file
```

Preserve raw xattr bytes, encoding, and filesystem metadata. An exported file's host timestamps may reflect extraction, not its original creation. Unix ctime is metadata-change time, not birth time; birth time may be unavailable.

In **dead box**, a log referenced `user.luks_key`; its hex value had to be decoded. In **Tombstone**, environment values, `user.upl_b`, backup content, and file birth time contributed to recovery.

## LUKS and LVM

```bash
cryptsetup luksDump partition.img
# Only when key.bin is the recovered passphrase/keyfile bytes:
sudo cryptsetup open --readonly --key-file work/key.bin partition.img ctf_luks
# Inspect the mapped device before mounting; it may contain LVM.
sudo cryptsetup close ctf_luks
```

A passphrase/keyfile and a raw volume key are different inputs. Use the volume-key option supported by your cryptsetup version only when the recovered data is demonstrably a volume key. Check `cryptsetup open --help`. LVM adds another layer between the decrypted device and the filesystem.

If key data is hex text, decode it once into bytes and verify the byte count. Avoid adding a newline. **durja otw magang** recovered original key arrays from syslog after the on-disk binary's arrays had changed.

## Recover deleted files and unallocated space

```bash
# Replace start sector 2048 and metadata address 12345 from your own image.
istat -o 2048 image.dd 12345
# Default: unallocated files; -e: allocated and unallocated files.
tsk_recover -o 2048 image.dd extracts/deleted
tsk_recover -e -o 2048 image.dd extracts/all-files
blkls -o 2048 image.dd > work/unallocated.bin
blkls -s -o 2048 image.dd > work/slack.bin
```

Prefer filesystem-aware recovery before signature carving: it can preserve names and allocation information. Carve with PhotoRec when metadata is missing or damaged, and write recovered output to separate storage. Carving may lose names, timestamps, and fragment order.

Offsets inside `blkls` output are not original disk offsets: it concatenates selected blocks. Keep the mapping or return to the source filesystem to locate a hit. Deleted metadata may survive while its data blocks have been reused, discarded by TRIM, or omitted from the acquisition.

## NTFS streams, journals, and snapshots

Inspect alternate `$DATA` streams when a file's visible contents do not explain its size or behavior. Sleuth Kit metadata addresses may include an attribute type and ID; use the complete address shown by `fls` when extracting a stream with `icat`.

Correlate `$MFT`, `$LogFile`, and `$UsnJrnl` for file lifecycle evidence. The USN journal describes changes, not complete old file contents. Volume Shadow Copies may preserve earlier versions when included in the image; use a compatible VSS parser and record the snapshot time separately from the file's own times.

## References

- [Sleuth Kit tsk_recover](https://www.sleuthkit.org/sleuthkit/man/tsk_recover.html)
- [Sleuth Kit blkls](https://www.sleuthkit.org/sleuthkit/man/blkls.html)
- [PhotoRec recovery](https://www.cgsecurity.org/wiki/PhotoRec)
- [Sleuth Kit manual pages](https://www.sleuthkit.org/sleuthkit/man/)
- [IFEST quals — dead box](https://2byte36.github.io/blog/ifest-2026-quals)
- [GEMASTIK — Tombstone](https://2byte36.github.io/blog/gemastik-19-quals)
- [ITFEST — durja otw magang](https://2byte36.github.io/blog/itfest-2026)
- [ARA quals — kau siapo kampang](https://2byte36.github.io/blog/ara-7-quals)
- [Techcomfest — minami](https://2byte36.github.io/blog/techcompfest-26-quals)
