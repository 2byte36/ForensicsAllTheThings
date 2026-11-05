# Documents and email

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Look beyond the rendered page: attachments, objects, revisions, and formatting can preserve hidden content.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [PDF triage](#pdf-triage)
- [Office containers and macros](#office-containers-and-macros)
- [Email attachments](#email-attachments)
- [Password-protected documents](#password-protected-documents)
- [Embedded content and external relationships](#embedded-content-and-external-relationships)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| 7-Zip | Archive listing and extraction | `sudo apt install 7zip` (see SETUP.md for executable names). [Source](https://www.7-zip.org/download.html) | `7z i` or `7zz i` |
| ExifTool | Metadata | `sudo apt install libimage-exiftool-perl`. [Source](https://exiftool.org/install.html) | `exiftool -ver` |
| qpdf | PDF structure and validation | `sudo apt install qpdf`. [Source](https://qpdf.readthedocs.io/en/stable/installation.html) | `qpdf --version` |
| Poppler utilities | PDF text and attachments | `sudo apt install poppler-utils`. [Source](https://poppler.freedesktop.org/) | `pdfinfo -v` |
| oletools | Static Office macro analysis | In the Python venv: `python -m pip install oletools`. [Source](https://github.com/decalage2/oletools/wiki/Install) | `olevba --help` |

## Script and command recipe

Helper: [email_extract.py](../scripts/helpers/email_extract.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/email_extract.py "$CASE/message.eml" "$CASE/extracts/mail" > "$CASE/work/attachments.jsonl"
```

Creates a new attachment directory using generated filenames and reports original names, types, sizes, and hashes. Does not execute macros or follow links. Inputs are capped at 64 MiB; nested encapsulated messages are reported as unsupported.

## PDF triage

```bash
pdfinfo document.pdf
pdftotext -layout document.pdf work/document.txt
pdfdetach -list document.pdf
qpdf --check document.pdf
qpdf --qdf --object-streams=disable document.pdf work/expanded.pdf
rg -a -n '/(JavaScript|JS|EmbeddedFile|OpenAction|Filter)|startxref|%%EOF' work/expanded.pdf
```

A black rectangle may cover text without removing it. Test text extraction and inspect objects. Preserve the original: rewriting a PDF may discard historical objects or incremental revisions.

In **Redaction Fail**, an older object used ASCII85 and Flate filters. Apply PDF filters in their declared decode order to the actual stream bytes, respecting stream boundaries. An obsolete object can contain a prior revision even when the current rendered page looks clean.

## Office containers and macros

```bash
7z l document.docx
mkdir -p extracts/office
7z x document.docx -oextracts/office
rg -n 'w:t|w:vanish|w:color' extracts/office/word/document.xml
olevba document.docm > work/macros.txt
```

DOCX/DOCM/XLSX are ZIP-based containers; legacy DOC/XLS use a different format. White text, hidden runs, comments, relationships, and embedded objects can all matter. XML tags may split a visible word across multiple runs; use an XML-aware reader when simple searches fail.

Extract macro code without enabling it. **Disk Cleaner** recovered a DOCX whose white text concealed the flag. **Incident 2** used a macro-derived key tied to host identifiers, then correlated execution through Windows artifacts.

## Email attachments

Preserve headers, MIME boundaries, Content-Disposition filenames, and transfer encodings. Extract attachments with a MIME parser instead of splitting by eye:

```bash
python3 - <<'PYCODE'
from email import policy
from email.parser import BytesParser
from pathlib import Path
msg = BytesParser(policy=policy.default).parsebytes(Path('message.eml').read_bytes())
out = Path('extracts/mail'); out.mkdir(parents=True, exist_ok=True)
for i, part in enumerate(msg.walk()):
    if part.get_content_disposition() == 'attachment' or part.get_filename():
        data = part.get_payload(decode=True)
        if data is not None:
            # Generated names avoid trusting attachment paths.
            target = out / f'attachment-{i}.bin'
            target.write_bytes(data)
            print(target, repr(part.get_filename()), part.get_content_type())
PYCODE
```

Correlate attachment hashes with downloaded and executed files. The visible From header alone does not establish sender identity; retain delivery headers and timestamps.

## Password-protected documents

Determine the actual protection type before selecting a recovery tool. Prioritize passwords hinted by nearby artifacts and authorized CTF wordlists. A successful password recovery should be followed by structural validation and text/object inspection: the next clue may still be hidden in the decrypted file.

## Embedded content and external relationships

Inspect PDF attachments, Office `*_rels/*.rels` relationship files, document properties, comments, tracked changes, and embedded objects. An external relationship is a link reference; it does not prove the target was fetched.

For OOXML, list every member instead of restricting the search to `word/document.xml`: spreadsheets can place values in shared strings or cells, and presentations have multiple slides and notes. Preserve formula text separately from cached cell values. For legacy OLE files, use an OLE-aware parser such as oletools.

For PDFs, distinguish visible text, OCR output, embedded text, and rendered pixels. A scanned page may require OCR; a successful text extraction may still omit important visual content. Validate recoveries with both structure and rendering when feasible.

For password recovery, see [archives and passwords](../Archives-and-Passwords/README.md). For timestamps, use [timestamp conversion](../Timestamps-and-Timelines/README.md) rather than assuming all metadata is UTC.

## References

- [qpdf command-line documentation](https://qpdf.readthedocs.io/en/stable/cli.html)
- [Python email parsing](https://docs.python.org/3/library/email.parser.html)
- [NCLP — Redaction Fail and Reward Runner](https://2byte36.github.io/blog/nclp-ctf-s1)
- [JOINTS — Disk Cleaner](https://2byte36.github.io/blog/joints-2026-quals)
- [The ACE — Incident 2](https://2byte36.github.io/blog/the-ace)
- [oletools](https://github.com/decalage2/oletools)
