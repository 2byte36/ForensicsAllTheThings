# Network forensics

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Start with conversations and protocol structure, then reconstruct the relevant application data.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Capture triage](#capture-triage)
- [HTTP objects and redirect chains](#http-objects-and-redirect-chains)
- [DNS and ICMP exfiltration](#dns-and-icmp-exfiltration)
- [Timing channels and custom protocols](#timing-channels-and-custom-protocols)
- [TLS decryption](#tls-decryption)
- [Reconstruct files and sessions](#reconstruct-files-and-sessions)
- [Protocol filter cookbook](#protocol-filter-cookbook)
- [Zeek summaries and joins](#zeek-summaries-and-joins)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| Wireshark / TShark | Offline packet analysis | `sudo apt install tshark`; desktop installer available upstream. [Source](https://www.wireshark.org/download.html) | `tshark --version` |
| Zeek | Connection/protocol logs | Use official packages for your distribution or the documented build. [Source](https://docs.zeek.org/en/current/install.html) | `zeek --version` |
| jq | JSON queries | `sudo apt install jq`. [Source](https://jqlang.org/download/) | `jq --version` |

## Script and command recipe

Helper: [pcap_summary.py](../scripts/helpers/pcap_summary.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/pcap_summary.py "$CASE/capture.pcapng" "$CASE/work/network"
```

Creates protocol statistics, TCP/UDP conversation summaries, and DNS-query TSV using TShark. It does not extract objects or decrypt traffic; follow the protocol-specific commands below.

## Capture triage

```bash
capinfos capture.pcapng
tshark -r capture.pcapng -q -z io,phs
tshark -r capture.pcapng -q -z conv,tcp -z conv,udp
tshark -r capture.pcapng -Y 'http.request' -T fields \
  -e frame.number -e frame.time_epoch -e ip.src -e tcp.stream \
  -e http.request.method -e http.host -e http.request.uri
```

Inspect capture duration, missing traffic, truncation, and retransmissions before trusting counts. IPv6 traffic needs IPv6 address fields as well. Traffic volume is a prioritization clue, not attribution.

## HTTP objects and redirect chains

```bash
mkdir -p extracts/http
tshark -r capture.pcapng --export-objects http,extracts/http
tshark -r capture.pcapng -q -z follow,tcp,ascii,0
tshark -r capture.pcapng -Y 'http.response.code >= 300 && http.response.code < 400' \
  -T fields -e frame.number -e tcp.stream -e http.response.code -e http.location
```

The stream-follow command produces an annotated transcript, not a clean binary payload. Use Wireshark's Follow Stream → select direction → Raw → Save As for binary stream bytes, or the protocol's object exporter.

Match requests to responses and record the full URL, status, Location, and next request. JavaScript redirects and meta refresh will not appear as 3xx responses. Keep query strings intact. **Anomalous Beacon** used missing request headers and a redirect chain to separate the payload download from a fake-antivirus page.

## DNS and ICMP exfiltration

```bash
tshark -r capture.pcapng -Y 'dns.flags.response == 0' -T fields \
  -e frame.number -e frame.time_epoch -e ip.src -e dns.qry.name
tshark -r capture.pcapng -Y 'icmp.type == 8' -T fields \
  -e frame.number -e frame.time_epoch -e ip.src -e icmp.seq -e data.data
```

Identify the campaign/domain, marker, sequence number, and payload boundaries before decoding. Some dissectors expose ICMP payload under different fields; inspect a packet with `tshark -V` or Wireshark. Do not concatenate requests and echoed replies together.

For DNS, remove the exact suffix, preserve the sender's ordering, and deduplicate retransmissions using protocol evidence. Decode each fragment separately if the encoder resets at fragment boundaries. **Advance Persistent Threat** had separate domain streams. **Good to be true?** used an end marker to establish the correct ICMP payload slice.

## Timing channels and custom protocols

Export timestamps for a single direction and conversation. Plot inter-arrival deltas, inspect clusters, then test bit mappings, framing, and delimiters. There is no universal threshold separating short and long intervals.

**save the water** contained both ICMP payload exfiltration and a separate beacon timing channel. Its large UDP flow required Decode As RTP to inspect the SSRC. **mosquito** used MQTT credentials and a program timestamp as crypto inputs. Inspect CONNECT, topic names, and PUBLISH payloads together.

## TLS decryption

When a session key log is supplied:

```bash
tshark -o tls.keylog_file:tls.keys -r capture.pcapng \
  -Y http.request -T fields -e http.host -e http.request.uri
```

A server private key only helps for compatible older RSA key-exchange sessions with the necessary handshake; it does not decrypt modern ECDHE or TLS 1.3 sessions by itself. Recovered key logs, session secrets, or plaintext buffers may provide another path. Preserve the exact capture and key material used.

## Reconstruct files and sessions

Use TCP reassembly to account for sequence numbers, overlap, and retransmission. Custom protocols may then need a second reassembly pass for application records. Validate total size and hashes before decrypting or interpreting the output.

For login-attempt counts, count requests to the relevant endpoint and distinguish failed from successful responses. Packet totals are not automatically attempt totals. Correlate session cookies to login requests when attributing later changes, as in **Mistakez**.

## Protocol filter cookbook

| Question | Wireshark display filter / pivot |
| --- | --- |
| DNS responses with addresses | `dns.flags.response == 1 && (dns.a || dns.aaaa)` |
| TLS requested hostname | `tls.handshake.extensions_server_name` |
| HTTP uploads | `http.request.method == "POST" || http.request.method == "PUT"` |
| FTP commands | `ftp.request.command` |
| SMB file operations | `smb2`; inspect CREATE/READ/WRITE names and handles |
| Mail sessions | `smtp || imap || pop`; follow stream and MIME boundaries |
| TCP reliability issues | `tcp.analysis.retransmission || tcp.analysis.lost_segment` |
| One IPv4 host | `ip.addr == 192.0.2.10` |
| One IPv6 host | `ipv6.addr == 2001:db8::10` |

The addresses are documentation examples. TLS SNI may be absent, encrypted, or different from the final application host. Decode As can select a dissector on a nonstandard port, but cannot decrypt ciphertext.

```bash
mkdir -p extracts/smb
# Check supported exporters first; available names vary by build.
tshark --export-objects help
tshark -r capture.pcapng --export-objects smb,extracts/smb
tshark -r capture.pcapng -d tcp.port==8080,http -Y http.request
```

Objects can be incomplete when the capture starts mid-transfer or packets are missing. Keep stream IDs, directions, and object names alongside hashes.

## Zeek summaries and joins

```bash
mkdir -p work/zeek
(cd work/zeek && zeek -r ../../capture.pcapng LogAscii::use_json=T)
jq -r '[.ts, .uid, .["id.orig_h"], .["id.resp_h"], .service] | @tsv' work/zeek/conn.log
```

Join protocol logs using `uid`, not timestamp alone. Inspect `conn.log`, `dns.log`, `http.log`, `files.log`, and available TLS logs. Logs appear only for traffic the engine sees and parses. If checksum offload explains rejected packets, document it before using an option that ignores checksum validation.

See [wireless captures](../Wireless-Forensics/README.md) when the evidence is raw 802.11 rather than Ethernet/IP.

## References

- [Zeek offline analysis](https://docs.zeek.org/en/current/quickstart.html)
- [Wireshark TLS decryption](https://wiki.wireshark.org/TLS/)
- [Wireshark TShark manual](https://www.wireshark.org/docs/man-pages/tshark.html)
- [GEMASTIK internal — Anomalous Beacon](https://2byte36.github.io/blog/gemastik-internal)
- [Hack It Braw — DNS and ICMP](https://2byte36.github.io/blog/hib-chb-ctf)
- [Compfest — save the water](https://2byte36.github.io/blog/compfest18-quals)
- [Techcomfest — mosquito](https://2byte36.github.io/blog/techcompfest-26-quals)
- [C2C — react](https://2byte36.github.io/blog/c2c26-quals)
- [Schematics quals — Mistakez](https://2byte36.github.io/blog/sch-ctf-2025-quals)
