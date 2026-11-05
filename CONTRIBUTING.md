# Maintaining ForensicsAllTheThings

[Home](README.md) · [Topic template](templates/topic.md)

## Add a useful recipe

1. Choose an existing artifact category, or copy the topic template into a new directory.
2. Describe when to use the technique and what evidence it requires.
3. Include a focused command or workflow, expected interpretation, and known pitfalls.
4. Distinguish generic examples from challenge-specific offsets, keys, and guesses.
5. Cite primary documentation for formats and tool behavior. Add relevant worked examples from any author; update the example index when adding a case study. A personal writeup is not required.
6. Add the category to the root README and quick reference if needed.
7. Include Tools and setup plus Script and command recipe sections, with upstream installation sources and verification commands.
8. Run `python3 scripts/check_docs.py` and `python3 -m unittest discover -s tests -v`, then review the rendered Markdown.

## Scope and source policy

Cover reusable techniques across common forensic artifacts. Prioritize a missing capability or a clearer workflow over adding another description of a solved challenge. A new topic should be useful without knowing an event name, flag, or challenge-specific key.

Use upstream manuals, implementation documentation, and format specifications for mechanics. Use reputable technical investigations and CTF writeups for examples, with attribution and explicit limitations. Verify changing tool syntax against its installed help or current documentation. Keep general instructions before case-specific observations.

## Editorial conventions

- Use English for navigation and explanations; retain original challenge names.
- Keep each topic in its own directory with a `README.md` and Summary links.
- Use relative links for local content and direct URLs for sources.
- Use language-tagged code fences; label shell, PowerShell, debugger, and SQL contexts.
- Prefer commands that inspect evidence. Write derived data to a separate case workspace.
- Explain sector versus byte offsets, encodings, timestamp epochs, and placeholder values.
- A source-reported solve is not an independently tested recipe. State what was actually validated.
- Do not add live malware, real credentials, challenge archives, memory images, or generated case output.
- Avoid pasting full writeups or third-party tools into the cheatsheet. Link them and explain the reusable method.

Repository helpers should read evidence, require explicit parameters, refuse existing generated outputs, and explain partial-failure behavior. Add meaningful synthetic fixtures for parsing, boundary conditions, and failure paths; do not test with live malware or private evidence.

This checkout is prepared for local review. The included GitHub workflow, if later pushed, checks documentation and helper tests; it has no publishing or deployment step.
