# Owner: shared · announce changes; 01 reviews
"""Everyone: every tracked file is listed in OWNERS.md and says the same owner in its first lines.

    pytest -q

When you create a file, add a row to OWNERS.md and an owner line at the top of the file, in the same PR:
`# Owner: ...` in code and config, `**Owner:** ...` under the title in Markdown. The licence, the team's site notes
(INFO.md) and CSV data carry no owner line, but are still listed.
"""
from __future__ import annotations

import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROW = re.compile(r"^\| `([^`]+)` \| ([^|]+) \|")
HEADER = re.compile(r"(?:^# Owner: |^\*\*Owner:\*\* |^<!-- Owner: )(.+?)(?: -->)?\s*$")
CODES = re.compile(r"\b(0[1-6]|shared|all)\b")
NO_HEADER = {"LICENSE", "INFO.md", "README.md"}   # the README is the public front page: no owner line


def owners() -> dict[str, str]:
    rows = {}
    for line in (ROOT / "OWNERS.md").read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if m:
            rows[m.group(1)] = m.group(2).strip()
    return rows


def tracked() -> list[str]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    except FileNotFoundError:
        out = []
    return [f for f in out if (ROOT / f).is_file()]


def entry_for(path: str, rows: dict[str, str]) -> str | None:
    if path in rows:
        return path
    dirs = [d for d in rows if d.endswith("/") and path.startswith(d)]
    return max(dirs, key=len) if dirs else None


def header_owner(path: str) -> str | None:
    try:
        head = (ROOT / path).read_text(encoding="utf-8").splitlines()[:6]
    except UnicodeDecodeError:
        return None
    for line in head:
        m = HEADER.match(line)
        if m:
            return m.group(1)
    return None


def test_every_file_has_an_owner():
    rows = owners()
    missing = [f for f in tracked() if entry_for(f, rows) is None]
    assert not missing, f"add these to OWNERS.md (and an owner line in the file): {missing}"


def test_owner_lines_match_owners_md():
    rows, wrong = owners(), []
    for f in tracked():
        entry = entry_for(f, rows)
        if entry != f or f in NO_HEADER or f.endswith((".csv", ".json", ".geojson", ".png", ".tif", ".pptx")):
            continue
        got = header_owner(f)
        if got is None:
            wrong.append(f"{f}: no owner line in its first 6 lines")
        elif set(CODES.findall(got)) != set(CODES.findall(rows[f])):
            wrong.append(f"{f}: says '{got}', OWNERS.md says '{rows[f]}'")
    assert not wrong, "\n".join(wrong)
