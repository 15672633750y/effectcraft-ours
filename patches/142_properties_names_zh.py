#!/usr/bin/env python3
"""Properties panel row names in Chinese — at draw time only.

`build.rs` keeps the stored English names ("Opacity", "Scale", …): the expression pick whip builds
`thisComp.layer("X").transform.opacity` from them, and the panel's own percent/rotation handling
compares them. Renaming the stored strings (an earlier patch did) broke both — the engine's
pick-whip tests caught it. Only the painter goes through the name table now.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PROPS_NAMES_ZH_V1"

OLD = "    p.text(pos2(r.min.x + 42.0, cy), Align2::LEFT_CENTER, &pr.name, Tokens::ui(12.0), t.text);\n"
NEW = (
    "    // EFFECTCRAFT_OURS_PROPS_NAMES_ZH_V1 — 只翻显示：存储名必须是英文（表达式用）\n"
    "    p.text(pos2(r.min.x + 42.0, cy), Align2::LEFT_CENTER, crate::i18n::prop::name(&pr.name, \"\"), Tokens::ui(12.0), t.text);\n"
)


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/properties.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("properties names already translated at draw time")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("properties panel names go through the table")


if __name__ == "__main__":
    main()
