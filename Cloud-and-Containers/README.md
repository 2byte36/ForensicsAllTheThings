# Cloud, container, and repository artifacts

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Investigate supplied audit exports, image archives, and repository history without needing a live account or running the image.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Cloud audit export triage](#cloud-audit-export-triage)
- [Container archive map](#container-archive-map)
- [Recover older layer content](#recover-older-layer-content)
- [Git and build history](#git-and-build-history)
- [Questions to answer](#questions-to-answer)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| jq | JSON queries | `sudo apt install jq`. [Source](https://jqlang.org/download/) | `jq --version` |
| Git | Local repository history | `sudo apt install git`. [Source](https://git-scm.com/downloads) | `git --version` |
| Skopeo | OCI/archive conversion | `sudo apt install skopeo`. [Source](https://github.com/containers/skopeo/blob/main/install.md) | `skopeo --version` |
| dive | Container layer inspection | Download a platform release/package using upstream installation instructions. [Source](https://github.com/wagoodman/dive#installation) | `dive --version` |

## Script and command recipe

Helper: [cloudtrail_summary.py](../scripts/helpers/cloudtrail_summary.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/cloudtrail_summary.py "$CASE/cloudtrail.json" > "$CASE/work/cloud-events.jsonl"
```

Reads an uncompressed CloudTrail Records-array export up to 64 MiB and preserves source indices plus nullable fields. No cloud credentials, API calls, sorting, or deduplication. Other providers need their own schemas.

## Cloud audit export triage

For an AWS CloudTrail JSON file containing a `Records` array:

```bash
jq -r '.Records[] | [.eventTime, .eventSource, .eventName,
  (.userIdentity.arn // .userIdentity.principalId // ""),
  (.sourceIPAddress // ""), (.errorCode // ""), .eventID] | @tsv' \
  cloudtrail.json > work/cloud-events.tsv
```

Keep full original events. Correlate role-session identity, request IDs, region, event IDs, and target resources. Distinguish attempted actions with errors from successful calls; a null response body alone does not imply failure. Data-event coverage depends on collection settings, so no object-read record is not proof of no read.

Azure activity/sign-in exports, Google Cloud audit records, and Kubernetes audit events use different schemas. Inspect a sample record before writing a query; do not map AWS fields onto them by name similarity.

## Container archive map

| Artifact | Inspect |
| --- | --- |
| Docker archive | `manifest.json`, image configuration, ordered layer tar files |
| OCI image layout | `oci-layout`, `index.json`, manifest/config/layer blobs by digest |
| Exported root filesystem | Final visible files; history/layers may be absent |
| Runtime collection | Container logs, writable layer, mounts/volumes, runtime metadata |

```bash
tar -tf image.tar > work/image-members.txt
# Only for a Docker archive containing this exact member:
tar -xOf image.tar manifest.json | jq .
```

Keep immutable image layers separate from runtime writes and externally mounted volumes. A clean image does not imply the running container was clean.

## Recover older layer content

Follow the manifest's layer order. Inspect candidate layer members before selectively extracting them. OCI whiteouts such as `.wh.filename` remove a lower-layer path from the merged view; they do not erase its historical bytes. An opaque-directory marker hides lower entries in that directory.

Do not simply overlay all tar files and expect a correct reconstructed root filesystem. Preserve duplicate paths by layer, apply whiteout semantics when building a view, and check each blob's declared compression/media type. See [Linux container workflow](../Linux-Forensics/README.md#container-layer-recovery) for Skopeo and dive.

## Git and build history

For a supplied local checkout, inspect history without running build scripts:

```bash
git -C extracts/repo --no-pager log --all --date=iso-strict --format='%H %aI %cI %s'
git -C extracts/repo --no-pager log --all --name-status --no-renames
git -C extracts/repo fsck --full --no-reflogs --unreachable
```

Review selected blobs with `git show COMMIT:path` once the commit and path are known. Unreachable objects may retain removed content; absence can follow pruning or a shallow acquisition. Author and committer dates differ and are user-controlled.

Correlate CI workflow revision, run ID, job/step, artifacts, and logs. A workflow edited after the incident does not describe what an earlier run executed. Treat discovered credentials as evidence strings; local history analysis does not require using them.

## Questions to answer

Who or which session acted, against which resource, from where, using which API or process, and with what outcome? Link audit events to image digest, deployment revision, repository commit, and artifact hashes where available. Preserve ingestion time separately from event time.

## References

- [AWS CloudTrail event fields](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-record-contents.html)
- [OCI layer specification](https://github.com/opencontainers/image-spec/blob/main/layer.md)
- [OCI image layout](https://github.com/opencontainers/image-spec/blob/main/image-layout.md)
- [Git fsck](https://git-scm.com/docs/git-fsck)
- [Git log](https://git-scm.com/docs/git-log)
- [jq manual](https://jqlang.org/manual/)
