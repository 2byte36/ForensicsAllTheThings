# USB and peripheral captures

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

A PCAP can contain keyboard reports or display bytes rather than ordinary IP traffic.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Identify the device and report format](#identify-the-device-and-report-format)
- [HID keyboard reconstruction](#hid-keyboard-reconstruction)
- [Linux input events](#linux-input-events)
- [Custom display and image framing](#custom-display-and-image-framing)
- [Preserve peripheral context](#preserve-peripheral-context)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| Wireshark / TShark | Offline packet analysis | `sudo apt install tshark`; desktop installer available upstream. [Source](https://www.wireshark.org/download.html) | `tshark --version` |

## Script and command recipe

Helper: [hid_boot_decode.py](../scripts/helpers/hid_boot_decode.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/hid_boot_decode.py "$CASE/reports.hex" > "$CASE/work/keyboard-events.jsonl"
```

Input is one hexadecimal 8-byte boot-keyboard report per line, from a single device/endpoint and direction. Emits new keypress events with modifier masks, US-layout text, and explicit unknown usages. No report IDs/NKRO, host auto-repeat, or final document editing; rollover errors stop decoding.

## Identify the device and report format

```bash
tshark -r usb.pcapng -q -z io,phs
tshark -r usb.pcapng -Y usb -V > work/usb-details.txt
# Inspect which payload fields your installed dissector exposes:
tshark -G fields | rg 'usb\.capdata|usbhid\.data'
```

Inspect GET_DESCRIPTOR, interface class, report descriptors, endpoint direction, and report length. Isolate the intended device and interrupt endpoint before decoding reports. Field availability depends on capture format and dissector version.

## HID keyboard reconstruction

For a standard boot keyboard report, modifier bits and usage codes need to be interpreted together. Other report protocols can use report IDs, different lengths, or NKRO bitmaps; do not force them into an eight-byte layout.

Track Shift, Caps Lock, held keys, releases, Backspace, Enter, and keyboard layout. Repeated reports of a held key are not necessarily separate keystrokes. Decode usage IDs using the HID usage tables, not ASCII values.

**the yuesbi** used USB enumeration and HID keyboard reports. **iuesbitaipsi** is another keyboard-capture reference in the NULL CTF post.

## Linux input events

**Tattletale** recovered a keylogger's binary `input_event` stream. The observed 64-bit little-endian layout was equivalent to `<QQHHi`: seconds, microseconds, event type, code, and signed value. Architecture and ABI can change the structure size.

For EV_KEY, distinguish press (1), release (0), and repeat (2). Apply modifiers and editing keys as stateful operations rather than merely printing every key name. Confirm the source program's structure before choosing the unpack format.

## Custom display and image framing

For a raw display stream, determine width, height, pixel format, row stride, header size, chunk count, ordering, and any sequence numbers. Validate `width × height × bytes_per_pixel` against the recovered pixel payload, accounting for row padding.

**DpDp** described a 400 × 100 image with 100 chunks of 1,200 bytes, consistent with three bytes per pixel. **Traceee** used application records carrying PNG fragments. Reassemble TCP first, then parse the application framing. Protocol labels and magic values in these cases are not general display standards.

## Preserve peripheral context

Retain bus/device address, endpoint, transfer type, direction, timestamps, status, and actual versus requested length. Host submission and completion records can describe the same transfer; avoid decoding both as independent input.

Map payloads through the captured descriptor and report ID before interpreting usages. Mouse movement may need signed relative deltas; touch/tablet reports can use absolute coordinates. A keyboard decoder is not appropriate merely because an interrupt endpoint exists.

For raw screen reconstruction, test channel order, row stride, orientation, and partial updates independently. A plausible image dimensions guess should be validated against all records and the expected payload length.

## References

- [USB HID specifications and usage tables](https://usb.org/hid)
- [Wireshark USB capture notes](https://wiki.wireshark.org/CaptureSetup/USB)
- [USB HID usage tables](https://usb.org/hid)
- [NCLP — the yuesbi](https://2byte36.github.io/blog/nclp-ctf-s1)
- [NULL CTF — iuesbitaipsi](https://2byte36.github.io/blog/null-ctf-2025)
- [C2C — Tattletale](https://2byte36.github.io/blog/c2c26-quals)
- [TECHFEST quals — DpDp](https://2byte36.github.io/blog/techfest-2026-quals)
- [Teknocomp — Traceee](https://2byte36.github.io/blog/teknocom-25)
