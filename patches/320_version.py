#!/usr/bin/env python3
"""版本号改成 0.52.1（用户要求），APK 文件名也会跟着变。"""
from __future__ import annotations

import os
import re
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_VERSION_V1"
VERSION = "0.52.1"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    changed = []
    for rel in ("Cargo.toml", "apps/effectcraft/Cargo.toml"):
        p = root / rel
        if not p.is_file():
            continue
        src = p.read_text(encoding="utf-8")
        if MARKER in src:
            continue
        new, n = re.subn(r'(?m)^version\s*=\s*"[^"]+"', f'version = "{VERSION}"', src, count=1)
        if n:
            p.write_text(new + f"\n# {MARKER}\n", encoding="utf-8")
            changed.append(rel)
    print("version set to", VERSION, "in", changed or "nothing")


if __name__ == "__main__":
    main()
