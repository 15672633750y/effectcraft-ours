#!/usr/bin/env python3
"""预合成剩下几处英文：菜单项、单层基底名、撤销记录名。（默认 `预合成 N` 已由 20 号补丁负责）

Idempotent and tolerant: each replacement happens only where the English text still exists, so this
never fights the earlier patch that already localized the default name.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PRECOMPOSE_STRINGS_V1"

EDITS = (
    ('"Pre-compose...",', '"预合成…",'),
    ('s.edit("Pre-compose", None, |proj, st|', 's.edit("预合成", None, |proj, st|'),
    ('first.map(|l| format!("{} Comp 1", l.name))', 'first.map(|l| format!("{} 合成 1", l.name))'),
    ('name: base.unwrap_or_else(|| format!("Pre-comp {n}")),', 'name: base.unwrap_or_else(|| format!("预合成 {n}")),'),
)


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    files = [
        root / "crates/engine/src/cmd/layer.rs",
        root / "crates/engine/src/cmd/layer/timing.rs",
        root / "crates/ui-egui/src/panels/precomp.rs",
    ]
    done = []
    for path in files:
        src = path.read_text(encoding="utf-8")
        if MARKER in src:
            continue
        changed = False
        for old, new in EDITS:
            if old in src:
                src = src.replace(old, new)
                changed = True
        if changed:
            path.write_text("// " + MARKER + "\n" + src, encoding="utf-8")
            done.append(path.name)
    print("预合成文案：" + (", ".join(done) if done else "无改动"))


if __name__ == "__main__":
    main()
