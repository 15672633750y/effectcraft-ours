#!/usr/bin/env python3
"""预合成弹窗的标题还是英文：`modal(ctx, "Pre-compose", ...)` → 「预合成」。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PRECOMPOSE_TITLE_V1"
OLD = 'super::dialogs::modal(ctx, "Pre-compose", vec2(520.0, 360.0), t, |ui| {'
NEW = 'super::dialogs::modal(ctx, "预合成", vec2(520.0, 360.0), t, |ui| {'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/precomp.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("pre-compose title already Chinese")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text("// " + MARKER + "\n" + src.replace(OLD, NEW, 1), encoding="utf-8")
    print("pre-compose dialog title is Chinese")


if __name__ == "__main__":
    main()
