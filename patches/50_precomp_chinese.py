#!/usr/bin/env python3
"""Chinese text in the Pre-compose dialog (title stays; the paragraphs become Chinese)."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PRECOMP_CHINESE_V1"

OLD_DESC = '''            ui.label(
                egui::RichText::new(format!(
                    "Use this option to create a new intermediate composition with only \\"{}\\" in it. The new composition will become the source to the current layer.",
                    d.layer_name
                ))
                .color(t.text_dim)
                .size(11.0),
            );'''
NEW_DESC = '''            ui.label(
                egui::RichText::new(format!(
                    "此选项会创建一个新的中间合成，里面只包含“{}”。新合成会成为当前图层的源。",
                    d.layer_name
                ))
                .color(t.text_dim)
                .size(11.0),
            );'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/precomp.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("Pre-compose Chinese is already installed.")
        return
    if src.count(OLD_DESC) != 1:
        raise SystemExit(f"pre-compose description: expected 1 match, found {src.count(OLD_DESC)}")
    src = src.replace(OLD_DESC, NEW_DESC, 1)
    old_move = 'ui.radio_value(&mut d.leave, false, "Move all attributes into the new composition")'
    if src.count(old_move) != 1:
        raise SystemExit(f"move-attributes label: expected 1 match, found {src.count(old_move)}")
    src = src.replace(old_move, 'ui.radio_value(&mut d.leave, false, "将所有属性移入新合成")', 1)
    path.write_text(f"// {MARKER}\n{src}", encoding="utf-8")
    print("Pre-compose dialog is Chinese now.")


if __name__ == "__main__":
    main()
