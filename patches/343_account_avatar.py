#!/usr/bin/env python3
"""账号 · 头像本地文件：`<config>/avatar.png` 存在就显示，没有才用昵称首字。

用户要求：「头像先本地存储 + 上传后端（base64 或后续 R2/KV，先本地也行）」。

- 文件位置：`XDG_CONFIG_HOME/avatar.png`（Android 上是
  `/storage/emulated/0/Android/data/com.shimoveaex.effects/files/config/avatar.png`）
- 只读本地，不上传；后端 `prefs_json` 只有 8 KB，塞不下图片
- 解码/读盘任何一步失败都退回昵称首字占位，不报错、不 panic
- texture 缓存进 `ui.data`，不会每帧重新解码（否则 60fps 会烧 CPU）

这一包只加文件支持和绘制，不碰 341 已经做好的槽位/面板布局。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ACCOUNT_AVATAR_V1"

CLOUD_ANCHOR = '''fn account_path() -> std::path::PathBuf {
    config_dir().join("account.json")
}
'''
CLOUD_INSERT = '''fn account_path() -> std::path::PathBuf {
    config_dir().join("account.json")
}

/// 本地头像文件。后端 `prefs_json` 上限 8 KB，图片只能放本地。
pub fn avatar_path() -> std::path::PathBuf {
    config_dir().join("avatar.png")
}
'''

UI_ANCHOR = '''fn initial(profile: &Profile) -> String {
'''
UI_INSERT = '''/// 本地头像的 texture（读 `avatar.png` 并缓存；失败就是 None，退回首字占位）。
fn avatar_texture(ui: &egui::Ui) -> Option<egui::TextureHandle> {
    if let Some(handle) = get::<egui::TextureHandle>(ui, "ours-account-avatar-tex") {
        return Some(handle);
    }
    let bytes = std::fs::read(cloud::avatar_path()).ok()?;
    let image = image::load_from_memory(&bytes).ok()?.to_rgba8();
    let (w, h) = image.dimensions();
    if w == 0 || h == 0 {
        return None;
    }
    let color = egui::ColorImage::from_rgba_unmultiplied([w as usize, h as usize], image.as_raw());
    let handle = ui.ctx().load_texture("ours-account-avatar", color, egui::TextureOptions::LINEAR);
    set(ui, "ours-account-avatar-tex", handle.clone());
    Some(handle)
}

/// 贴一张 texture：用 `Painter::image(texture_id, rect, uv, tint)`（签名已对着 egui 源码核对）。
fn paint_texture(ui: &egui::Ui, texture: &egui::TextureHandle, rect: Rect) {
    let uv = Rect::from_min_max(egui::pos2(0.0, 0.0), egui::pos2(1.0, 1.0));
    ui.painter().image(texture.id(), rect, uv, Color32::WHITE);
}

/// 画头像：有本地图片就贴图（圆内接正方形 + 主题色外圈），否则昵称首字。
fn paint_avatar(ui: &egui::Ui, r: Rect, t: &Tokens, profile: &Profile) {
    let radius = r.width().min(r.height()) * 0.5;
    ui.painter().circle_filled(r.center(), radius, t.accent);
    let texture = avatar_texture(ui);
    match texture {
        Some(texture) => {
            let side = radius * std::f32::consts::SQRT_2;
            let inner = Rect::from_center_size(r.center(), Vec2::splat(side));
            paint_texture(ui, &texture, inner);
        }
        None => {
            ui.painter().text(
                r.center(),
                Align2::CENTER_CENTER,
                initial(profile),
                Tokens::ui((radius * 0.9).max(10.0)),
                Color32::from_rgb(16, 18, 22),
            );
        }
    }
}

fn initial(profile: &Profile) -> String {
'''

SLOT_OLD = '''        let r = Rect::from_center_size(Pos2::new(x + 13.0, cy), Vec2::splat(26.0));
        let resp = ui.interact(r, Id::unique("ours-account-slot"), Sense::click());
        // 没有头像图片时用昵称首字 + 主题色底（用户定的占位方案）。
        p.circle_filled(r.center(), 13.0, if resp.hovered() { t.accent_hover } else { t.accent });
        p.text(r.center(), Align2::CENTER_CENTER, initial(&profile), Tokens::ui(13.0), Color32::from_rgb(16, 18, 22));
        app.auto.add("account.slot", r, "账号");
        resp
'''
SLOT_NEW = '''        let r = Rect::from_center_size(Pos2::new(x + 13.0, cy), Vec2::splat(26.0));
        let resp = ui.interact(r, Id::unique("ours-account-slot"), Sense::click());
        // 有 `avatar.png` 就贴图，没有才用昵称首字 + 主题色（用户定的占位方案）。
        let hover = if resp.hovered() { t.accent_hover } else { t.accent };
        ui.painter().circle_filled(r.center(), 13.0, hover);
        match avatar_texture(ui) {
            Some(texture) => {
                let inner = Rect::from_center_size(r.center(), Vec2::splat(13.0 * std::f32::consts::SQRT_2));
                paint_texture(ui, &texture, inner);
            }
            None => {
                ui.painter().text(r.center(), Align2::CENTER_CENTER, initial(&profile), Tokens::ui(13.0), Color32::from_rgb(16, 18, 22));
            }
        }
        app.auto.add("account.slot", r, "账号");
        resp
'''

PROFILE_OLD = '''    // 头像：昵称首字 + 主题色（有本地图片的版本留到下一期）。
    let avatar = Pos2::new(card.center().x, card.min.y + 74.0);
    ui.painter().circle_filled(avatar, 22.0, t.accent);
    let profile = temp::<Profile>(ui, PROFILE);
    ui.painter().text(avatar, Align2::CENTER_CENTER, initial(&profile), Tokens::semibold(18.0), Color32::from_rgb(16, 18, 22));
    ui.painter().text(
        Pos2::new(card.center().x, card.min.y + 104.0),
        Align2::CENTER_CENTER,
        "头像：先用昵称首字，上传稍后支持",
        Tokens::ui(10.5),
        t.text_faint,
    );
'''
PROFILE_NEW = '''    // 头像：有本地 avatar.png 就贴图，否则昵称首字。
    let avatar = Pos2::new(card.center().x, card.min.y + 74.0);
    let profile = temp::<Profile>(ui, PROFILE);
    paint_avatar(ui, Rect::from_center_size(avatar, Vec2::splat(44.0)), &t, &profile);
    ui.painter().text(
        Pos2::new(card.center().x, card.min.y + 104.0),
        Align2::CENTER_CENTER,
        if avatar_texture(ui).is_some() { "头像：本地 avatar.png" } else { "头像：昵称首字（放 avatar.png 可换图）" },
        Tokens::ui(10.5),
        t.text_faint,
    );
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    cloud = root / "crates/ui-egui/src/cloud.rs"
    src = cloud.read_text(encoding="utf-8")
    if "pub fn avatar_path(" not in src:
        if src.count(CLOUD_ANCHOR) != 1:
            raise SystemExit(f"cloud anchor: {src.count(CLOUD_ANCHOR)}")
        cloud.write_text(src.replace(CLOUD_ANCHOR, CLOUD_INSERT, 1), encoding="utf-8")
        print("cloud.rs: avatar_path")

    ui_path = root / "crates/ui-egui/src/account_ui.rs"
    src = ui_path.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(UI_ANCHOR) != 1:
            raise SystemExit(f"account_ui anchor: {src.count(UI_ANCHOR)}")
        src = src.replace(UI_ANCHOR, UI_INSERT, 1)
        if src.count(SLOT_OLD) != 1:
            raise SystemExit(f"slot anchor: {src.count(SLOT_OLD)}")
        src = src.replace(SLOT_OLD, SLOT_NEW, 1)
        if src.count(PROFILE_OLD) != 1:
            raise SystemExit(f"profile anchor: {src.count(PROFILE_OLD)}")
        src = src.replace(PROFILE_OLD, PROFILE_NEW, 1)
        ui_path.write_text(src, encoding="utf-8")
        print("account_ui.rs: local avatar file in the slot and the profile card")


if __name__ == "__main__":
    main()
