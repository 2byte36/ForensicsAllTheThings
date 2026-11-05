# Android and firmware forensics

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Connect package data and configuration to static application code and captured transfers.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Android artifact map](#android-artifact-map)
- [APK inspection](#apk-inspection)
- [Unity IL2CPP](#unity-il2cpp)
- [Firmware and flash dumps](#firmware-and-flash-dumps)
- [Acquisition scope and general pivots](#acquisition-scope-and-general-pivots)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| 7-Zip | Archive listing and extraction | `sudo apt install 7zip` (see SETUP.md for executable names). [Source](https://www.7-zip.org/download.html) | `7z i` or `7zz i` |
| JADX | DEX/APK decompilation | Download release ZIP; install required Java and add its bin directory to PATH. [Source](https://github.com/skylot/jadx#download) | `jadx --version` |
| Apktool | APK resources and smali | Install Java plus the platform wrapper and JAR from the official guide. [Source](https://apktool.org/docs/install/) | `apktool --version` |
| Il2CppDumper | IL2CPP metadata recovery | Download a compatible release and follow its platform/runtime instructions. [Source](https://github.com/Perfare/Il2CppDumper#usage) | Run its usage/help entry point |
| Binwalk | Embedded-format signatures | `sudo apt install binwalk`; use upstream build for a newer major version. [Source](https://github.com/ReFirmLabs/binwalk#installation) | `binwalk --help` |

## Script and command recipe

Helper: [zip_inventory.py](../scripts/helpers/zip_inventory.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/zip_inventory.py "$CASE/suspect.apk" > "$CASE/work/apk-members.jsonl"
```

Lists ZIP/APK members without extraction, including duplicate-entry indices, methods, CRCs, header offsets, and suspicious paths. Does not parse DEX or Android binary XML. For raw flash, use the byte-carving helper and measured partition boundaries.

## Android artifact map

| Location | Lead |
| --- | --- |
| `/data/data/<package>` or `/data/user/0/<package>` | App-private files, databases, preferences |
| `shared_prefs/*.xml` | Configuration, salts, wrapped keys, flags |
| `databases/` | SQLite stores and sidecars |
| `/data/media/0/Download` | Downloaded APKs, documents, staged files |
| Chrome `app_chrome` | Browser profiles and history |
| Telephony provider databases | SMS/MMS; actual path varies with Android version/user |

Logical dumps may omit protected app data or deleted blocks. Record the acquisition scope before assuming a missing database means no activity occurred.

## APK inspection

```bash
7z l suspect.apk
apktool d suspect.apk -o work/apk
jadx -d work/jadx suspect.apk
rg -n -i 'Cipher|getInstance|SecretKeySpec|IvParameterSpec|https?://' work/apk work/jadx
```

Follow data flow into crypto calls, network destinations, and file enumeration. A variable named `AES_KEY` is a clue; confirm its bytes and how they are used. Look at native libraries and embedded Python code when Java/smali does not explain behavior.

**VoltPN** found a cryptor in smali and then followed a recovered image to another artifact. **seorang CEO** correlated SMS, browser history, embedded Python bytecode, Downloads, and PCAP transfers. **cinder** obtained crypto settings from preferences for WAL recovery.

## Unity IL2CPP

Pair `libil2cpp.so` with `assets/bin/Data/Managed/Metadata/global-metadata.dat`. Use compatible tooling to recover names/offsets, then verify actual instructions and referenced data in a disassembler.

**petani durr** used distinct small-file and large-file encryption routines. Its large-file chunk layout and trailing IV positions could not be inferred from the small-file decryptor. Validate branch thresholds, chunk boundaries, and IV placement independently.

## Firmware and flash dumps

```bash
file flash.bin
binwalk flash.bin
strings -a -t x -n 6 flash.bin > work/flash-strings.txt
rg -n -i 'device_cfg|key|nonce|ssid|token|https?://' work/flash-strings.txt
xxd -s 4096 -l 256 flash.bin
```

The offset above is illustrative. Identify the board/platform and partition layout before assuming strings are configuration or carving executable regions. Validate key candidates against the encryption routine and resulting structure.

**Durrr Intern** used two encrypted fragments and configuration-adjacent key material in an ESP32 flash dump. Preserve stream position across fragments when the producer uses one continuous keystream; restarting the cipher can decrypt the first fragment correctly and corrupt the second.

## Acquisition scope and general pivots

Identify the OS version, user/profile IDs, acquisition type, and whether app-private storage is included. Shared storage alone cannot answer every question about messages or app databases. File-based encryption, hardware-backed secrets, and excluded data can limit recovery even when an APK is available.

Correlate package identifiers and install/update information with permissions, app-private records, shared downloads, and captured traffic. A permission declaration describes capability, not proof of use. A hardcoded endpoint in an APK does not establish that the captured device contacted it.

For firmware, distinguish raw flash bytes, partition images, filesystem images, and executable images. Respect declared offsets and compression; identify strings in the correct partition before calling them active configuration. A deleted or backup configuration block can coexist with the current one.

## References

- [Android app-specific storage](https://developer.android.com/training/data-storage/app-specific)
- [Android APK Analyzer](https://developer.android.com/studio/debug/apk-analyzer)
- [Espressif partition tables](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-guides/partition-tables.html)
- [TECHFEST final — VoltPN](https://2byte36.github.io/blog/techfest-2026-final)
- [The ACE — seorang CEO](https://2byte36.github.io/blog/the-ace)
- [ITFEST — petani durr](https://2byte36.github.io/blog/itfest-2026)
- [HackToday — Durrr Intern](https://2byte36.github.io/blog/hacktoday-2026)
- [GEMASTIK — cinder](https://2byte36.github.io/blog/gemastik-19-quals)
