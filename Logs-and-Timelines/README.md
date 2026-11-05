# Logs and timelines

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Turn isolated records into a sequence while retaining the source of every timestamp and inference.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Normalize without losing evidence](#normalize-without-losing-evidence)
- [Blind SQL injection reconstruction](#blind-sql-injection-reconstruction)
- [Fragmented log payloads](#fragmented-log-payloads)
- [Correlate the incident](#correlate-the-incident)
- [Format exact answers](#format-exact-answers)
- [Repository and workflow history](#repository-and-workflow-history)
- [Structured logs and counting rules](#structured-logs-and-counting-rules)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| jq | JSON queries | `sudo apt install jq`. [Source](https://jqlang.org/download/) | `jq --version` |
| Plaso / psort | Supertimeline extraction | Use a supported packaged release per upstream guidance; avoid assuming a plain pip install includes native dependencies. [Source](https://plaso.readthedocs.io/en/latest/sources/user/Users-Guide.html) | `log2timeline.py --version`; `psort.py --help` |

## Script and command recipe

Helper: [timestamps.py](../scripts/helpers/timestamps.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/timestamps.py unix-ms 1700000000123
jq -r 'select(.event == "login") | [.timestamp, .user, .result] | @tsv' "$CASE/events.jsonl"
```

The first command converts an illustrative integer timestamp to UTC without floating-point epoch math. The second query assumes the shown JSONL schema; adapt fields to the actual log. Use Plaso below for multi-source timelines.

## Normalize without losing evidence

Keep columns for source path, record ID, raw time, source timezone, UTC, event type, actor, target, and interpretation. Preserve subsecond precision. Missing timezone information should remain explicitly unknown.

```bash
rg -n -i 'sqlmap|nuclei|dirsearch|wp-login|admin-ajax|powershell' extracts/logs
rg -n '219\.75\.27\.16' extracts/logs/access.log
```

The IP is an example from **log**, not a universal indicator. Decode URL encoding on a copy and preserve the original request. User-Agent strings can be spoofed; correlate request behavior before naming a tool.

## Blind SQL injection reconstruction

For boolean-based traces:

1. Parse the targeted table/column, character position, operator, and tested value.
2. Associate each request with its response or recorded response metrics.
3. Establish true/false behavior from known conditions.
4. Combine inequalities into character bounds; do not treat `> n` as equality.
5. Keep gaps and contradictions visible.

**Begadang Jangan Begadang** used response-length differences in ModSecurity logs. Those exact lengths were case-specific.

For time-based traces, prefer logged request duration. Gaps between adjacent access-log timestamps are only a heuristic when requests are sequential and timing noise is understood. **log** used such gaps and varying sleep values; its writeup also records a discrepancy in login-attempt counts. Do not turn that transcript into a universal counting rule.

## Fragmented log payloads

**chunking** used an `rb64` field, Base64 plus gzip, a campaign identifier, and numbered fragments. Group by campaign/session before ordering; unrelated decoys can share the same outer encoding.

Verify fragment count, missing indices, duplicates, and compression boundaries. A concatenated multi-member gzip stream is different from arbitrary chunks of a single compressed member. Reassemble at the layer indicated by the producer's format.

## Correlate the incident

Use explicit relationships where possible: process parent/child, logon ID, session cookie, request/response, attachment hash. Use time proximity as supporting evidence. A successful HTTP status may still contain an application error.

**Incident 1** followed discovery, login attempts, an uploaded archive, a shell stream, and database download. **Wulung-2604** narrowed the timeline around suspicious timestamp manipulation. In **Incident 2**, execution artifacts and file timestamps supplied different parts of the sequence.

## Format exact answers

Keep the requested format beside the evidence: UTC versus local, filename versus full path, user SID versus machine SID, count of attempts versus count of packets, host path versus container path. Never silently adjust a timestamp to match a server response; record both the observation and accepted answer.

## Repository and workflow history

For a supplied repository or workflow-log export, inspect commit history, workflow definitions, run IDs, timestamps, and archived logs. A later revision can remove evidence that remains in an earlier commit or run. Decode nested data as inert bytes and retain the intermediate stages.

**Sandworm Strike** pivoted through repository history and a particular workflow run after a nested Base64 artifact. The reusable lesson here is historical artifact correlation. Exposed credentials and historical challenge accounts are not needed to practice it on a local export.

## Structured logs and counting rules

Inspect the format before parsing: JSON arrays, newline-delimited JSON, CSV, and free-form text need different readers. Preserve escaped characters and multiline records. Define the unit being counted: event, request, session, unique user, or successful action.

```bash
# For newline-delimited JSON with these field names:
jq -r 'select(.event == "login") | [.timestamp, .user, .result] | @tsv' events.jsonl
```

Deduplicate only using stable event/request IDs or a justified retransmission rule. Two identical-looking lines may represent repeated actions. Access logs may omit request bodies, response bodies, subsecond precision, or proxy identity; do not infer missing fields from status codes alone.

Use [timestamps and timelines](../Timestamps-and-Timelines/README.md) for epochs, timezone conversion, and Plaso; [cloud exports](../Cloud-and-Containers/README.md) for service-specific audit schemas.

## References

- [jq manual](https://jqlang.org/manual/)
- [Plaso user documentation](https://plaso.readthedocs.io/en/latest/sources/user/Using-log2timeline.html)
- [NULL CTF — Sandworm Strike](https://2byte36.github.io/blog/null-ctf-2025)
- [C2C — log and Breached](https://2byte36.github.io/blog/c2c26-quals)
- [Hack It Braw — Begadang Jangan Begadang](https://2byte36.github.io/blog/hib-chb-ctf)
- [NCLP — chunking](https://2byte36.github.io/blog/nclp-ctf-s1)
- [The ACE — Incident 1 and Incident 2](https://2byte36.github.io/blog/the-ace)
- [Wreck-IT — Wulung-2604](https://2byte36.github.io/blog/wreck-it-7-quals)
