"""Fail when a Markdown or HTML file links to a repository file that does not exist."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
HTML_LINK = re.compile(r'href="([^"]+)"')


def targets(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    pattern = HTML_LINK if path.suffix == ".html" else MD_LINK
    return pattern.findall(text)


def main() -> int:
    broken = []
    files = [p for p in ROOT.rglob("*") if p.suffix in {".md", ".html"} and ".git" not in p.parts]
    for path in files:
        for target in targets(path):
            if re.match(r"^(https?:|mailto:|#|/)", target):
                continue
            # links in site/index.html point at GitHub blob URLs or are relative to the repo root
            file_part = target.split("#", 1)[0]
            if not file_part:
                continue
            resolved = (path.parent / file_part).resolve()
            if not resolved.exists():
                broken.append(f"{path.relative_to(ROOT)} -> {target}")
    for line in broken:
        print(f"BROKEN {line}")
    print(f"checked {len(files)} files, {len(broken)} broken links")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
