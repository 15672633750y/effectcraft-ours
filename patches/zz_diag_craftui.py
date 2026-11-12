#!/usr/bin/env python3
"""Diagnostic: report how craft_ui lays out dock splits (draggable or not) in the CI log."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_DIAG_CRAFTUI_V1"


def main() -> None:
    home = Path(os.environ.get("CARGO_HOME", str(Path.home() / ".cargo")))
    roots = [home / "git" / "checkouts", home / "registry" / "src"]
    hits = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("layout.rs"):
            if "craft" in str(path).lower():
                hits.append(path)
    print(f"[{MARKER}] craft_ui candidates: {len(hits)}")
    for path in hits[:4]:
        text = path.read_text(encoding="utf-8", errors="replace")
        print(f"[{MARKER}] {path} bytes={len(text)}")
        for key in ("drag", "Drag", "interact", "separator", "resize", "Ratio", "Fixed"):
            count = text.count(key)
            if count:
                print(f"[{MARKER}]   {key}: {count}")
        for line in text.splitlines():
            low = line.lower()
            if "separator" in low or "resize" in low or "dragged" in low:
                print(f"[{MARKER}]   | {line.strip()[:120]}")


if __name__ == "__main__":
    main()
