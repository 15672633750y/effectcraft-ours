#!/usr/bin/env python3
"""The Audio panel's levels are draggable: drag 左/右 sideways to set that channel's dB.

The panel only showed the selected layer's Audio Levels, so there was nowhere obvious to change
the volume. Now the two rows are a slider: 0.25 dB per pixel, clamped to -60…+12 dB, written
through `prop.set` on `audio/levels` (so it is undoable like any other property change).
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_AUDIO_DRAG_V1"

OLD = '''        Some((name, [a, b])) => {
            p.text(pos2(lx, top - 9.0), Align2::LEFT_CENTER, &name, Tokens::ui(11.0), t.text_dim);
            for (i, (k, v)) in [("Left", a), ("Right", b)].into_iter().enumerate() {
                let y = top + 12.0 + i as f32 * 20.0;
                p.text(pos2(lx, y), Align2::LEFT_CENTER, k, Tokens::ui(12.0), t.text_dim);
                p.text(pos2(lx + 44.0, y), Align2::LEFT_CENTER, format!("{v:+.1} dB"), Tokens::ui(12.0), t.hot_text);
            }
        }
'''

NEW = '''        Some((name, [a, b])) => {
            p.text(pos2(lx, top - 9.0), Align2::LEFT_CENTER, &name, Tokens::ui(11.0), t.text_dim);
            for (i, (k, v)) in [("左", a), ("右", b)].into_iter().enumerate() {
                let y = top + 12.0 + i as f32 * 20.0;
                p.text(pos2(lx, y), Align2::LEFT_CENTER, k, Tokens::ui(12.0), t.text_dim);
                p.text(pos2(lx + 44.0, y), Align2::LEFT_CENTER, format!("{v:+.1} dB"), Tokens::ui(12.0), t.hot_text);
            }
            // EFFECTCRAFT_OURS_AUDIO_DRAG_V1
            // Drag a channel sideways to change it: this is where people look for the volume, so
            // the panel sets the Audio Levels instead of only showing them.
            for (i, ch) in [0usize, 1usize].into_iter().enumerate() {
                let y = top + 12.0 + i as f32 * 20.0;
                let row = Rect::from_min_size(pos2(lx - 4.0, y - 10.0), vec2(104.0, 20.0));
                let resp = ui.interact(row, egui::Id::unique(("audio-level", i)), Sense::drag());
                if resp.hovered() {
                    ui.ctx().set_cursor_icon(egui::CursorIcon::ResizeHorizontal);
                }
                if resp.dragged() {
                    let step = resp.drag_delta().x * 0.25;
                    if step != 0.0 {
                        let mut lv = [a, b];
                        lv[ch] = (lv[ch] + step).clamp(-60.0, 12.0);
                        if let Some(id) = sel {
                            let _ = crate::menus::invoke(
                                app,
                                ui.ctx(),
                                "prop.set",
                                json!({"layer": id.0, "path": "audio/levels", "value": [lv[0], lv[1]]}),
                            );
                        }
                    }
                }
            }
        }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/misc.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("audio drag already installed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"audio levels anchor: expected 1, found {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("the Audio panel's levels drag sideways")


if __name__ == "__main__":
    main()
