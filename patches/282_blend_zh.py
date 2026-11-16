#!/usr/bin/env python3
"""混合模式下拉框显示中文（之前直接显示英文 label）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_BLEND_ZH_V1"

EDITS = [('let mresp = widgets::dropdown(ui, mr, layer.blend_mode.label(), &t, egui::Id::unique(("mode", layer.id.0)));', 'let mresp = widgets::dropdown(ui, mr, &crate::i18n::tr(layer.blend_mode.label()), &t, egui::Id::unique(("mode", layer.id.0)));'), ('BlendMode::ALL.iter().flat_map(|m| if m.ends_group() { vec![m.label().to_string(), "-".to_string()] } else { vec![m.label().to_string()] }).collect();', 'BlendMode::ALL.iter().flat_map(|m| if m.ends_group() { vec![crate::i18n::tr(m.label()).to_string(), "-".to_string()] } else { vec![crate::i18n::tr(m.label()).to_string()] }).collect();'), ('widgets::popup_menu(ui, pop, mr.left_bottom(), &opts, opts.iter().position(|o| o == layer.blend_mode.label()))', 'widgets::popup_menu(ui, pop, mr.left_bottom(), &opts, opts.iter().position(|o| o == crate::i18n::tr(layer.blend_mode.label())))')]

def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("blend labels already translated")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("blend mode labels go through tr()")


if __name__ == "__main__":
    main()
