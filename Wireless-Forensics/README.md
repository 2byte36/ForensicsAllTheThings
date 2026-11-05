# Wireless capture forensics

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Analyze supplied 802.11 captures by separating link-layer evidence from decrypted application traffic.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Verify capture type](#verify-capture-type)
- [Identify stations and sessions](#identify-stations-and-sessions)
- [Decryption prerequisites](#decryption-prerequisites)
- [Common failure checks](#common-failure-checks)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| Wireshark / TShark | Offline packet analysis | `sudo apt install tshark`; desktop installer available upstream. [Source](https://www.wireshark.org/download.html) | `tshark --version` |

## Script and command recipe

Helper: [pcap_summary.py](../scripts/helpers/pcap_summary.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/pcap_summary.py "$CASE/wireless.pcapng" "$CASE/work/wireless" --wireless
```

Adds management-frame BSSID/SSID TSV and EAPOL details to the standard capture reports. Requires raw 802.11 fields in the acquisition. No live capture, password recovery, or automatic decryption.

## Verify capture type

```bash
capinfos wireless.pcapng
tshark -r wireless.pcapng -q -z io,phs
tshark -r wireless.pcapng -Y 'wlan.fc.type == 0' -T fields \
  -e frame.number -e frame.time_epoch -e wlan.bssid -e wlan.ssid
tshark -r wireless.pcapng -Y eapol -V > work/eapol.txt
```

An Ethernet capture from a wireless host may contain no raw 802.11 headers. Radiotap describes radio metadata when present; channel and signal fields are not guaranteed. Missing management frames may reflect capture coverage rather than an absent association.

## Identify stations and sessions

| Evidence | Use |
| --- | --- |
| Beacon / probe response | SSID, BSSID, advertised security |
| Authentication / association | Station participation and negotiated capabilities |
| EAP / EAPOL | Authentication/key-exchange context |
| Deauthentication / disassociation | Session termination or disruption clues |
| Data frame direction bits | Interpret transmitter, receiver, source, and destination |

A station MAC can be randomized or spoofed. An SSID can appear on multiple access points. Count unique session events, not raw retransmitted frames. A burst of deauthentication frames needs context before attributing an attack.

## Decryption prerequisites

Use Wireshark's IEEE 802.11 preferences and the key type matching the capture's negotiated authentication/cipher suite. For ordinary WPA2-Personal sessions, a known passphrase/SSID plus a captured usable handshake may suffice; WPA3-SAE and enterprise/roaming cases can require session-specific secrets. Consult the upstream matrix for the exact case.

First verify that decryption exposes a plausible inner protocol. Then switch to [network forensics](../Network-Forensics/README.md) for DNS, HTTP, and stream reconstruction. Decrypting Wi-Fi does not decrypt HTTPS inside it.

## Common failure checks

- Correct BSSID, client, SSID bytes, and key type?
- Complete handshake for the session being inspected?
- Rekey or roaming event between handshake and data?
- Truncated frames, missing channel coverage, or unsupported cipher?
- Already-decapsulated Ethernet traffic rather than raw protected 802.11?

Preserve original packet numbers and timestamps when exporting decrypted or filtered traffic. A display filter changes visibility, not capture completeness.

## References

- [Wireshark WLAN decryption keys](https://www.wireshark.org/docs/wsug_html_chunked/Ch80211Keys.html)
- [Wireshark WLAN display fields](https://www.wireshark.org/docs/dfref/w/wlan.html)
- [Wireshark TShark manual](https://www.wireshark.org/docs/man-pages/tshark.html)
