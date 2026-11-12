#!/usr/bin/env python3
"""While rendering, the viewer follows the frames as they are produced."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PREVIEW_FOLLOW_V1"
ANCHOR = "pub fn show(app: &mut EffectcraftApp, ui: &mut egui::Ui, rect: Rect) {\n"
CODE = '''// EFFECTCRAFT_OURS_PREVIEW_FOLLOW_V1
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/header.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("preview follow already installed")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"header show anchor: {src.count(ANCHOR)}")
    body = '''    // Rendering happens on a worker thread; moving the playhead along the finished frames lets
    // the viewer show progress instead of a frozen image.
    if app.session.is_rendering() {
        let follow = ui.ctx().data(|d| d.get_temp::<bool>(egui::Id::new("ours-preview-follow")).unwrap_or(true));
        if follow
            && let Some(st) = app.session.render_progress()
        {
            let fps = app.session.active_comp().map(|c| c.frame_rate.as_f64()).unwrap_or(30.0).max(1.0);
            app.session.set_time(effectcraft_engine::time::Tick::from_seconds_f64(st.done as f64 / fps));
        }
    }
'''
    src = src.replace(ANCHOR, ANCHOR + body, 1)
    path.write_text(src, encoding="utf-8")
    print("viewer follows the render")


if __name__ == "__main__":
    main()
