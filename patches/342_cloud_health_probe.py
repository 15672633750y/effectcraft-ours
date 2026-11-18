#!/usr/bin/env python3
"""账号 · 调试入口：长按「关于」里的版本号 0.8 秒 → GET /health → 一行状态。

用户要亲眼确认网络层通没通：成功显示「云服务连接成功（存储 ok）」，失败显示
「云服务连接失败: <错误>」。结果走 `cloud` 自己的 status 槽，不进 events 队列
（events 留给登录/资料，将来 account_ui 消费，两者不抢）。

不改任何可见布局：版本号那行照旧画，只是多了一个不可见的交互矩形。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLOUD_HEALTH_PROBE_V1"

CLOUD_ANCHOR = '''fn json_or_null(text: &str) -> serde_json::Value {
'''
CLOUD_INSERT = '''/// health 探测的结果只走这一条状态槽：UI 每帧取一次，显示成一行。
fn status_slot() -> &'static Mutex<Option<String>> {
    static STATUS: OnceLock<Mutex<Option<String>>> = OnceLock::new();
    STATUS.get_or_init(|| Mutex::new(None))
}

/// 取走 health 探测留下的一行状态（没有就返回 None）。
pub fn take_status() -> Option<String> {
    status_slot().lock().ok().and_then(|mut slot| slot.take())
}

/// GET /health：只用来验证网络与 TLS 通不通，不做任何业务。
pub fn health() {
    spawn(move || {
        let message = match request("GET", "/health", None, None) {
            Ok((code, text)) if (200..300).contains(&code) => {
                let value = json_or_null(&text);
                // 200 不等于健康：后端 db 挂了也会回 200，得看 ok / db_error。
                let healthy = value["ok"].as_bool().unwrap_or(false);
                let db_error = value["db_error"].as_str().unwrap_or_default();
                let storage = value["storage"].as_str().unwrap_or("?");
                let version = value["version"].as_str().unwrap_or_default();
                if !healthy || !db_error.is_empty() {
                    let why = if db_error.is_empty() { "后端报告 not ok".to_string() } else { db_error.to_string() };
                    format!("云服务连接失败: {why}")
                } else if version.is_empty() {
                    format!("云服务连接成功（存储 {storage}）")
                } else {
                    format!("云服务连接成功（存储 {storage}，后端 v{version}）")
                }
            }
            Ok((code, _)) => format!("云服务连接失败: HTTP {code}"),
            Err(err) => format!("云服务连接失败: {err}"),
        };
        if let Ok(mut slot) = status_slot().lock() {
            *slot = Some(message);
        }
    });
}

fn json_or_null(text: &str) -> serde_json::Value {
'''

DIALOG_OLD = '''        Tokens::ui(12.0),
        t.text_dim,
    );
    ui.add_space(12.0);
'''
DIALOG_NEW = '''        Tokens::ui(12.0),
        t.text_dim,
    );
    // EFFECTCRAFT_OURS_CLOUD_HEALTH_PROBE_V1 — 长按版本号 0.8 秒：调一次 GET /health，
    // 把结果打成一行状态，用来亲眼确认网络层通了（不弹窗、不改布局）。
    {
        let version_rect = Rect::from_min_size(r.min + vec2(90.0, 50.0), vec2(300.0, 22.0));
        let resp = ui.interact(version_rect, egui::Id::new("ours-about-version"), Sense::click());
        let hold = egui::Id::new("ours-about-version-hold");
        let now = ui.input(|i| i.time);
        if resp.is_pointer_button_down_on() {
            // 长按时指针不动，egui 不会自己重绘 —— 不主动 request_repaint 的话，
            // 记录起点之后就再也没有下一帧去判断「超过 0.8 秒」，长按永远不触发。
            ui.ctx().request_repaint();
            match ui.data(|d| d.get_temp::<f64>(hold)) {
                // 注意：`insert_temp` 返回 RawKey，这里必须用块丢掉它，
                // 否则这个 match 的 arm 类型不一致（E0308: expected RawKey, found ()）。
                None => {
                    ui.data_mut(|d| d.insert_temp(hold, now));
                }
                Some(start) if now - start > 0.8 => {
                    ui.data_mut(|d| d.remove::<f64>(hold));
                    crate::cloud::health();
                    app.ui.status = "正在连接云服务…".to_string();
                }
                Some(_) => {}
            }
        } else {
            ui.data_mut(|d| d.remove::<f64>(hold));
        }
    }
    ui.add_space(12.0);
'''

FRAME_OLD = "        curves_editor(self, ui, full);\n"
FRAME_NEW = (
    "        curves_editor(self, ui, full);\n"
    "        // EFFECTCRAFT_OURS_CLOUD_HEALTH_PROBE_V1 — health 探测的结果落到底部状态行。\n"
    "        if let Some(message) = crate::cloud::take_status() {\n"
    "            self.ui.status = message;\n"
    "        }\n"
)


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    cloud = root / "crates/ui-egui/src/cloud.rs"
    src = cloud.read_text(encoding="utf-8")
    if "pub fn health(" not in src:
        if src.count(CLOUD_ANCHOR) != 1:
            raise SystemExit(f"cloud anchor: {src.count(CLOUD_ANCHOR)}")
        cloud.write_text(src.replace(CLOUD_ANCHOR, CLOUD_INSERT, 1), encoding="utf-8")
        print("cloud.rs: health probe + status slot")

    dialogs = root / "crates/ui-egui/src/panels/dialogs.rs"
    src = dialogs.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(DIALOG_OLD) != 1:
            raise SystemExit(f"dialogs anchor: {src.count(DIALOG_OLD)}")
        dialogs.write_text(src.replace(DIALOG_OLD, DIALOG_NEW, 1), encoding="utf-8")
        print("dialogs.rs: long-press the version line")

    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if "cloud::take_status" not in src:
        if src.count(FRAME_OLD) != 1:
            raise SystemExit(f"frame anchor: {src.count(FRAME_OLD)}")
        frame.write_text(src.replace(FRAME_OLD, FRAME_NEW, 1), encoding="utf-8")
        print("frame.rs: health status line")


if __name__ == "__main__":
    main()
