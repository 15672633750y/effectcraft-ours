#!/usr/bin/env python3
"""导出对话框里「导出 CapCut 桌面工程包（.zip）」接上真正的导出器。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CAPCUT_BUTTON_V1"

OLD = '''            if ui.button("导出 CapCut 桌面工程包（.zip）").clicked() {
                app.ui.status = "暂不支持：需要 CapCut 草稿样本才能写出可打开的 draft_content.json".into();
            }
'''
NEW = '''            if ui.button("导出 CapCut 桌面工程包（.zip）").clicked() {
                match crate::menus::invoke(app, ui.ctx(), "ours.exportCapCut", serde_json::json!({})) {
                    Ok(r) => {
                        let zip = r.get("zip").and_then(|v| v.as_str()).unwrap_or("").to_string();
                        app.ui.status = format!("已导出 CapCut 工程包：{zip}");
                    }
                    Err(e) => app.ui.status = format!("CapCut 导出失败：{e}"),
                }
            }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    hits = [p for p in (root / "crates/ui-egui/src").rglob("*.rs")
            if '导出 CapCut 桌面工程包' in p.read_text(encoding="utf-8", errors="ignore")]
    if not hits:
        raise SystemExit("capcut button not found")
    path = hits[0]
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("capcut button already wired")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("capcut button wired to the exporter")


if __name__ == "__main__":
    main()
