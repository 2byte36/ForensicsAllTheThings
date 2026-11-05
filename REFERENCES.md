# Reference library

[Home](README.md) · [Toolbox](TOOLS.md) · [Worked examples](WRITEUPS.md)

The cheatsheet draws on primary documentation and general forensic workflows. Use these sources to verify syntax, format boundaries, and version constraints. Worked examples illustrate applications; they do not define the scope of a topic.

## Method and evidence

- [NIST SP 800-86](https://csrc.nist.gov/pubs/sp/800/86/final) — integration of forensic techniques into incident response; foundational guidance, not a current tool manual.
- [Sleuth Kit manual pages](https://www.sleuthkit.org/sleuthkit/man/) — partition offsets, filesystem records, recovery, and timelines.
- [PhotoRec documentation](https://www.cgsecurity.org/wiki/PhotoRec) — signature-based recovery and its limits.
- [Plaso user documentation](https://plaso.readthedocs.io/en/latest/sources/user/Using-log2timeline.html) — event extraction and timeline storage.

## Memory and operating systems

- [Volatility 3 documentation](https://volatility3.readthedocs.io/) — acquisition layers, symbols, and plugin interfaces.
- [MemProcFS project](https://github.com/ufrisk/MemProcFS) — memory-backed process/filesystem views.
- [Microsoft Sysmon](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon) — provider event meanings and collection behavior.
- [Eric Zimmerman tools](https://ericzimmerman.github.io/) — offline Windows artifact parsers.
- [Microsoft FILETIME](https://learn.microsoft.com/en-us/windows/win32/api/minwinbase/ns-minwinbase-filetime) — Windows epoch and units.
- [systemd units](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html) — unit paths, precedence, and drop-ins.

- [Apple launch daemons and agents](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html) — launchd configuration and scope; see the [macOS guide](macOS-Forensics/README.md).
- [Mandiant macos-UnifiedLogs](https://github.com/mandiant/macos-UnifiedLogs) — cross-platform Unified Log parser; [current CLI source](https://github.com/mandiant/macos-UnifiedLogs/blob/main/examples/unifiedlog_iterator/src/main.rs).
- [Python plistlib](https://docs.python.org/3/library/plistlib.html) — XML/binary property-list parsing.

## Network and peripherals

- [TShark manual](https://www.wireshark.org/docs/man-pages/tshark.html) — filters, extraction, and stream analysis.
- [Wireshark display-filter reference](https://www.wireshark.org/docs/dfref/) — field names and supported versions.
- [Wireshark TLS](https://wiki.wireshark.org/TLS/) — decryption prerequisites and session secrets.
- [Wireshark WLAN keys](https://www.wireshark.org/docs/wsug_html_chunked/Ch80211Keys.html) — authentication/cipher-specific wireless decryption.
- [Zeek quick start](https://docs.zeek.org/en/current/quickstart.html) — offline capture logs and UID correlation.
- [USB HID specifications](https://usb.org/hid) — report interpretation and usage tables.

## Files, databases, and applications

- [SQLite file format](https://www.sqlite.org/fileformat.html) and [WAL behavior](https://www.sqlite.org/wal.html) — database pages, journals, and transactions.
- [SQLite PRAGMA reference](https://sqlite.org/pragma.html) — schema and integrity queries.
- [qpdf manual](https://qpdf.readthedocs.io/en/stable/cli.html) — PDF structure inspection and transformations.
- [oletools](https://github.com/decalage2/oletools) — static Office/OLE analysis.
- [Chromium time definitions](https://chromium.googlesource.com/chromium/src/+/main/base/time/time.h) — browser timestamp interpretation.
- [Android storage documentation](https://developer.android.com/training/data-storage/app-specific) — storage scope and app-private data.
- [Espressif partition tables](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/partition-tables.html) — flash layout interpretation.

## Decoding, search, and archives

- [RFC 4648](https://www.rfc-editor.org/rfc/rfc4648) — Base16, Base32, and Base64 representations.
- [Python binary structures](https://docs.python.org/3/library/struct.html), [Base64](https://docs.python.org/3/library/base64.html), and [zlib](https://docs.python.org/3/library/zlib.html) — explicit byte transformations.
- [YARA rules](https://yara.readthedocs.io/en/stable/writingrules.html) and [CLI](https://yara.readthedocs.io/en/stable/commandline.html) — matching syntax and scan output.
- [bkcrack](https://github.com/kimci86/bkcrack) — legacy ZipCrypto known-plaintext requirements.
- [John the Ripper](https://www.openwall.com/john/doc/EXAMPLES.shtml) and [Hashcat example hashes](https://hashcat.net/wiki/doku.php?id=example_hashes) — verifier formats and password-search mechanics.
- [FFmpeg documentation](https://ffmpeg.org/documentation.html) — media streams, filters, and frame extraction.

## Cloud, containers, and history

- [AWS CloudTrail event reference](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-record-contents.html) — audit field semantics and optional fields.
- [OCI image layout](https://github.com/opencontainers/image-spec/blob/main/image-layout.md) and [layer specification](https://github.com/opencontainers/image-spec/blob/main/layer.md) — blobs, layer ordering, and whiteouts.
- [Git log](https://git-scm.com/docs/git-log) and [Git fsck](https://git-scm.com/docs/git-fsck) — supplied repository history and object recovery.

## Adding sources

Prefer a direct link to the relevant manual or specification over a search result or generic homepage. Record tool versions when testing a recipe. Attribute a case study to its author, and retain any uncertainty or correction from the original investigation. A source's existence does not mean every claim or command has been independently reproduced.
