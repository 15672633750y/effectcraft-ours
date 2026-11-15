#!/usr/bin/env python3
"""197 留下的不可达代码里引用了 `rect`（已改名为 r），补一行别名让它编译通过。

The direct-paint rewrite left the old Area code after an early `return;`; that dead code still names
`rect`. Aliasing it keeps the file compiling without rewriting the whole function again.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_UNREACHABLE_RECT_V1"
OLD = '''    return;
    #[allow(unreachable_code)]
'''
NEW = '''    return;
    #[allow(unreachable_code)]
    let rect = r;
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("alias already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("dead code compiles again")


if __name__ == "__main__":
    main()
