#!/usr/bin/env python3
"""Timeline tree labels and the snapping menu in Chinese.

The Timeline draws its own tree: group rows ("Transform", "Audio", "Waveform") and property rows
("Audio Levels") went straight to the painter, so they stayed English no matter what the i18n
table said. Both now pass through the property-name table, and the Snapping menu's two After
Effects option names are translated too.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TREE_ZH_V1"

EDITS = [
    # Group rows that are not effects (Transform, Audio, Waveform …).
    (
        "        Some(effect) => crate::i18n::effects::group(effect, name),\n        None => name.clone(),\n",
        "        Some(effect) => crate::i18n::effects::group(effect, name),\n"
        "        // A plain property group: 变换 / 音频 / 波形 …\n"
        "        None => crate::i18n::prop::name(name, \"\").to_string(),\n",
    ),
    # The property rows themselves.
    (
        "    lp.text(pos2(indent + 82.0, cy), Align2::LEFT_CENTER, &prop.name, Tokens::ui(11.5), t.text);",
        "    lp.text(pos2(indent + 82.0, cy), Align2::LEFT_CENTER, crate::i18n::prop::name(&prop.name, \"\"), Tokens::ui(11.5), t.text);",
    ),
    (
        'egui::PopupAnchor::Pointer).show(|ui| ui.label(&prop.name));',
        'egui::PopupAnchor::Pointer).show(|ui| ui.label(crate::i18n::prop::name(&prop.name, "")));',
    ),
    # Snapping options menu.
    (
        "let items: Vec<String> = vw::SnapFeatures::OPTIONS.iter().map(|(k, label)| widgets::check_label(f.option(k), label)).collect();",
        "let items: Vec<String> = vw::SnapFeatures::OPTIONS.iter().map(|(k, label)| widgets::check_label(f.option(k), tr(label))).collect();",
    ),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    timeline = root / "crates/ui-egui/src/panels/timeline.rs"
    src = timeline.read_text(encoding="utf-8")
    if MARKER not in src:
        changed = False
        for old, new in EDITS[:3]:
            if new in src:
                continue
            if src.count(old) != 1:
                raise SystemExit(f"timeline anchor {old[:60]!r}: expected 1, found {src.count(old)}")
            src = src.replace(old, new, 1)
            changed = True
        if changed:
            timeline.write_text(src, encoding="utf-8")
            print("timeline tree labels go through the table")

    header = root / "crates/ui-egui/src/header.rs"
    h = header.read_text(encoding="utf-8")
    old, new = EDITS[3]
    if new not in h:
        if h.count(old) != 1:
            raise SystemExit(f"snapping menu anchor: expected 1, found {h.count(old)}")
        header.write_text(h.replace(old, new, 1), encoding="utf-8")
        print("snapping menu labels go through the table")


if __name__ == "__main__":
    main()
