#!/usr/bin/env python3
"""删除成功后再拉一次列表：确认服务端真的没了，也顺便修"刷新后又出现"的观感。

之前只在本地把那条从列表里移除，若服务端仍存在（旧版 DELETE 根本没发出去），
下次刷新/重进面板又会冒出来。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLOUD_DELETE_RESYNC_V1"

OLD = '''            Event::Deleted(id) => {
                let mut list = get::<Vec<cloud::RemoteProject>>(ui, PROJECTS).unwrap_or_default();
                list.retain(|item| item.id != id);
                set(ui, PROJECTS, list);
                app.ui.status = "已删除".to_string();
            }'''

NEW = '''            Event::Deleted(id) => {
                let mut list = get::<Vec<cloud::RemoteProject>>(ui, PROJECTS).unwrap_or_default();
                list.retain(|item| item.id != id);
                set(ui, PROJECTS, list);
                app.ui.status = "已删除".to_string();
                // EFFECTCRAFT_OURS_CLOUD_DELETE_RESYNC_V1 — 再拉一次，确认服务端也没有了
                let token = token(ui);
                if !token.is_empty() {
                    set(ui, CLOUD_LOADING, true);
                    cloud::list_projects(token);
                }
            }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/account_ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("delete resync already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("delete now re-lists projects after success")


if __name__ == "__main__":
    main()
