#!/usr/bin/env python3
"""Nuke (`.nk`) support is dropped.

It only ever extracted the paths a Nuke script's Read nodes point at — of no use here, and it took a
row in the import window that NodeVideo now uses. A `.nk` file is no longer treated as a recipe, so
it falls through to the ordinary import and shows up as an unreadable file instead of being expanded.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NO_NUKE_V1"

OLD = '''    if path.to_ascii_lowercase().ends_with(".nk") || lower.ends_with(".nv") {
        return true;
    }'''
NEW = '''    // EFFECTCRAFT_OURS_NO_NUKE_V1 — 不再当 Nuke 脚本处理；NodeVideo 的 .nv 仍然要
    if lower.ends_with(".nv") {
        return true;
    }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/import_ext.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("Nuke already dropped")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("Nuke .nk no longer a recipe")


if __name__ == "__main__":
    main()
