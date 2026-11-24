#!/usr/bin/env python3
"""底部工具条加「保存」：竖屏布局原来根本无法保存工程文件。

`文件 ▸ 保存` 在桌面菜单栏里，竖屏品牌布局把菜单栏隐藏了 —— 手机上除了自动保存快照，
**没有手动保存真实工程文件的入口**。

现在工具条最后一格是「保存」：
* 已有真实路径（不在自动保存目录）→ 直接 `file.save`
* 还没有 → 弹「另存为」，选好路径后 `file.saveAs`
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_TRAY_SAVE_V1"

LINE = '                            ("2", "2×", 20),'
ADD = '\n                            ("\\u{1f4be}", "保存", 21),'

MATCH_OLD = '''                Some(20) => {'''

MATCH_NEW = '''                Some(21) => {
                    // EFFECTCRAFT_OURS_TRAY_SAVE_V1 — 保存真实工程文件；没有路径就先另存为
                    let real = self
                        .session
                        .path
                        .clone()
                        .filter(|p| !p.is_empty() && !p.contains("EffectCraft Auto-Save"));
                    match real {
                        Some(p) => {
                            let r = crate::menus::invoke(
                                self,
                                ui.ctx(),
                                "file.save",
                                serde_json::json!({ "path": p }),
                            );
                            self.ui.status = if r.is_ok() {
                                "已保存".to_string()
                            } else {
                                "保存失败".to_string()
                            };
                        }
                        None => {
                            if let Some(spawn) = self.hooks.file_dialog_async.as_ref() {
                                let dialog = crate::FileDialog::Save {
                                    default: "我的工程.ecproj".to_string(),
                                    ext: "ecproj".to_string(),
                                    project: true,
                                };
                                let done: crate::DialogDone = Box::new(|paths| {
                                    if let Some(p) = paths.into_iter().next() {
                                        if let Ok(mut slot) = ours_save_target().lock() {
                                            *slot = Some(p);
                                        }
                                    }
                                });
                                spawn(dialog, done);
                                self.ui.status = "选择保存位置…".to_string();
                            } else {
                                self.ui.status = "这个平台没有文件选择器".to_string();
                            }
                        }
                    }
                }
                Some(20) => {'''

HANDLE_ANCHOR = '''                _ => {}
            }
        }
        // EFFECTCRAFT_OURS_CAPCUT_TRANSPORT_V1'''

HANDLE_INSERT = '''                _ => {}
            }
            // EFFECTCRAFT_OURS_TRAY_SAVE_V1 — 另存为选好路径后立刻保存
            if let Ok(mut slot) = ours_save_target().lock() {
                if let Some(path) = slot.take() {
                    let r = crate::menus::invoke(
                        self,
                        ui.ctx(),
                        "file.saveAs",
                        serde_json::json!({ "path": path }),
                    );
                    self.ui.status = if r.is_ok() {
                        format!("已保存到 {path}")
                    } else {
                        "保存失败".to_string()
                    };
                }
            }
        }
        // EFFECTCRAFT_OURS_CAPCUT_TRANSPORT_V1'''

HELPER_ANCHOR = '''/// EFFECTCRAFT_OURS_SPEED_PANEL_V1 — 时间伸缩面板'''

HELPER_INSERT = '''/// 「另存为」回调把选好的路径放这里，下一帧被取走并执行 `file.saveAs`。
fn ours_save_target() -> &'static std::sync::Mutex<Option<String>> {
    static SLOT: std::sync::OnceLock<std::sync::Mutex<Option<String>>> = std::sync::OnceLock::new();
    SLOT.get_or_init(|| std::sync::Mutex::new(None))
}

/// EFFECTCRAFT_OURS_SPEED_PANEL_V1 — 时间伸缩面板'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("tray save already present")
        return
    n = src.count(LINE)
    if n < 1:
        raise SystemExit(f"tray line anchor: {n}")
    src = src.replace(LINE, LINE + ADD)
    for name, old, new in (
        ("match", MATCH_OLD, MATCH_NEW),
        ("handle", HANDLE_ANCHOR, HANDLE_INSERT),
        ("helper", HELPER_ANCHOR, HELPER_INSERT),
    ):
        if src.count(old) != 1:
            raise SystemExit(f"{name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("tray gained a real 保存 button")


if __name__ == "__main__":
    main()
