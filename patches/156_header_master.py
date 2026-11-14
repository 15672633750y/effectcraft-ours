#!/usr/bin/env python3
"""The Timeline's column-header eye and speaker become master switches for every layer.

The header icons were painted labels with no click handling at all. They now toggle video (eye) and
audio (speaker) on every layer at once — what the header of the A/V column looks like it should do,
and what After Effects' layer switches column implies.

This is additive: no existing row widget, id or handler changes (the row switches keep their
behaviour, which is what crashed when it was touched).
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_HEADER_MASTER_V1"

ANCHOR = '''    let hresp = ui.interact(hdr_rect, egui::Id::unique("tl-colhdr"), Sense::click());
    app.auto.add("timeline.header", hdr_rect, "Columns (right-click)");
'''

ADD = '''
    // EFFECTCRAFT_OURS_HEADER_MASTER_V1 — 表头的眼睛/喇叭：全部图层的视频/音频总开关
    if vis.av {
        let cid = g.cid;
        let comp = app.session.project.comp_arc(cid);
        let (video_on, audio_on) = comp
            .as_ref()
            .map(|c| (c.layers.iter().all(|l| l.switches.video), c.layers.iter().all(|l| l.switches.audio)))
            .unwrap_or((false, false));
        let targets: Vec<u64> = comp.as_ref().map(|c| c.layers.iter().map(|l| l.id.0).collect()).unwrap_or_default();
        for (name, x, all_on) in [("video", cw.av + 10.0, video_on), ("audio", cw.av + 28.0, audio_on)] {
            let r = Rect::from_center_size(pos2(x, ch.center().y), vec2(18.0, 18.0));
            let tip = if name == "video" { "全部图层：显示 / 隐藏" } else { "全部图层：音频开 / 关" };
            let resp = ui.interact(r, egui::Id::unique(("tl-hdr-master", name)), Sense::click()).on_hover_text(tip);
            app.auto.add(&format!("timeline.header.master.{name}"), r, name);
            if resp.clicked() && !targets.is_empty() {
                actions.push(("layer.setSwitch".into(), json!({"layers": targets.clone(), "switch": name, "value": !all_on})));
            }
        }
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("header master switches already installed")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, ANCHOR + ADD, 1), encoding="utf-8")
    print("header eye/speaker toggle every layer")


if __name__ == "__main__":
    main()
