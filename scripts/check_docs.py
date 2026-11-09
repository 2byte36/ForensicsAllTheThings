#!/usr/bin/env python3
"""Check this repository's inline Markdown links, fences, and topic structure.

Standard library only. This intentionally supports the Markdown conventions used
here, not every CommonMark construct. External links are never fetched.
"""

import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^\s)]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.+?)(?:\s+#+)?$")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")


def markdown_lines(text):
    """Return lines outside fenced code and the opening line of an unclosed fence."""
    lines = []
    opened = None
    for number, line in enumerate(text.splitlines(), 1):
        match = FENCE.match(line)
        if match:
            marker, tail = match.groups()
            if opened is None:
                opened = (marker[0], len(marker), number)
            elif marker[0] == opened[0] and len(marker) >= opened[1] and not tail.strip():
                opened = None
            continue
        if opened is None:
            lines.append((number, line))
    return lines, opened[2] if opened else None


def anchors(lines):
    result = set()
    seen = Counter()
    for _, line in lines:
        match = HEADING.match(line)
        if not match:
            continue
        title = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", match[1])
        slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        suffix = f"-{seen[slug]}" if seen[slug] else ""
        seen[slug] += 1
        result.add(slug + suffix)
    return result


def check(root):
    files = sorted(p for p in root.rglob("*.md")
                   if not any(part.startswith(".") for part in p.relative_to(root).parts)
                   and p.relative_to(root).parts[0] not in {"work", "extracts", "carved", "evidence"})
    parsed = {p.resolve(): markdown_lines(p.read_text(encoding="utf-8")) for p in files}
    ids = {p: anchors(lines) for p, (lines, _) in parsed.items()}
    errors = []
    links = 0
    for path, (lines, unclosed) in parsed.items():
        relative = path.relative_to(root.resolve())
        if unclosed:
            errors.append(f"{relative}:{unclosed}: unclosed code fence")
        if not any(line.startswith("# ") for _, line in lines):
            errors.append(f"{relative}: missing document title")
        if path.name == "README.md" and path.parent != root.resolve():
            for required in ("## Summary", "## Tools and setup", "## Script and command recipe", "## References"):
                if not any(line == required for _, line in lines):
                    errors.append(f"{relative}: missing {required}")
            if not any('[Source](https://' in line for _, line in lines):
                errors.append(f"{relative}: missing upstream tool setup source")
        for number, line in lines:
            # Ignore inline-code examples of Markdown syntax.
            prose = re.sub(r"`[^`]*`", "", line)
            for match in LINK.finditer(prose):
                target = match[1].strip("<>")
                url = urlsplit(target)
                if url.scheme or url.netloc:
                    continue
                links += 1
                dest = (path.parent / unquote(url.path)).resolve() if url.path else path
                if not dest.is_relative_to(root.resolve()):
                    errors.append(f"{relative}:{number}: link leaves repository: {target}")
                elif not dest.exists():
                    errors.append(f"{relative}:{number}: missing target: {target}")
                elif url.fragment and dest.suffix == ".md" and unquote(url.fragment) not in ids.get(dest, set()):
                    errors.append(f"{relative}:{number}: missing heading: {target}")
    return files, links, errors


def main():
    files, links, errors = check(ROOT)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: {len(files)} Markdown files, {links} local links; fences and topic structure valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
