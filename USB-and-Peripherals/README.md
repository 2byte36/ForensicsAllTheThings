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
- [Existing USB keyboard parser](#existing-usb-keyboard-parser)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| Wireshark / TShark | Offline packet analysis | `sudo apt install tshark`; desktop installer available upstream. [Source](https://www.wireshark.org/download.html) | `tshark --version` |

## Script and command recipe

Use the existing USB keyboard parser directly on a copy of the capture:

```bash
python3 "$HOME/ctf-tools/CTF-Usb_Keyboard_Parser/main.py" /absolute/path/to/case/usb.pcapng
```

The interactive alias is `usb-keyboard-parser`; see [its setup and limits](#existing-usb-keyboard-parser). Check device IDs and report format against TShark. Optional existing [hid_boot_decode.py](../scripts/helpers/hid_boot_decode.py) accepts only hexadecimal 8-byte boot reports from a single device/endpoint; it is not needed for the upstream parser workflow.

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

## Existing USB keyboard parser

The current `usb-keyboard-parser` alias invokes [shark-asmx/CTF-Usb_Keyboard_Parser](https://github.com/shark-asmx/CTF-Usb_Keyboard_Parser). Setup: clone that repository into `~/ctf-tools/CTF-Usb_Keyboard_Parser`; its current `main.py` parses captures directly, while the older script uses TShark.

```bash
# Interactive shell with the existing alias:
usb-keyboard-parser capture.pcapng
# Equivalent invocation without requiring aliases:
python3 "$HOME/ctf-tools/CTF-Usb_Keyboard_Parser/main.py" capture.pcapng
```

Run in a case working directory because the tool may create output there. Inspect results per device ID and cross-check the capture's report descriptors, keyboard layout, Shift/Caps Lock, releases, and rollover. Supports the documented USBPcap/Linux link types; a non-keyboard endpoint or proprietary report format needs separate interpretation. A decoded character sequence does not automatically reconstruct cursor movement or editing history.

## References

- [USB HID specifications and usage tables](https://usb.org/hid)
- [Wireshark USB capture notes](https://wiki.wireshark.org/CaptureSetup/USB)
- [USB HID usage tables](https://usb.org/hid)
- [NCLP — the yuesbi](https://2byte36.github.io/blog/nclp-ctf-s1)
- [NULL CTF — iuesbitaipsi](https://2byte36.github.io/blog/null-ctf-2025)
- [C2C — Tattletale](https://2byte36.github.io/blog/c2c26-quals)
- [TECHFEST quals — DpDp](https://2byte36.github.io/blog/techfest-2026-quals)
- [Teknocomp — Traceee](https://2byte36.github.io/blog/teknocom-25)
