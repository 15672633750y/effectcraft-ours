#!/usr/bin/env python3
"""账号与资料 · 第二包：工具栏最左的账号槽 + 登录/注册面板 + 资料卡（APP-交接新需求）。

第一包（`340_cloud_http.py`）已经有 HTTP 客户端；这一包只做界面：
- 工具栏最左槽位（原品牌 logo 的位置，`brand_and_home` 的开头）：
  未登录 = 44×26 的「登录」文字按钮；已登录 = 26×26 圆形头像（昵称首字 + 主题色底）。
  它就在 `header::show` 的横向流里，所以跟随工具栏走，不是固定悬浮。About 仍在「帮助」菜单。
- 点「登录」→ 登录/注册面板：用户名、密码（眼睛切换明文）、登录、注册、稍后再说。
- 点头像 → 资料卡：圆形头像、昵称、性别、生日、个性签名，保存 / 退出登录 / 关闭。
- 未登录不影响任何本地功能：面板只是盖一层，关掉就没了。

头像第一版是「昵称首字 + 主题色」占位（用户已同意头像先本地）；上传后端留到下一期。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ACCOUNT_UI_V1"

LIB_ANCHOR = "pub mod cloud;\n"
LIB_INSERT = "pub mod cloud;\nmod account_ui;\n"

# 链上 `brand_and_home` 的品牌 logo 已被 NO_BRAND_LOGO 补丁去掉，最左边现在是 Home；
# 账号槽插在它前面，才是真正的「最左槽位」。
HEADER_OLD = (
    "    let t = app.tokens;\n"
    "    // EFFECTCRAFT_OURS_NO_BRAND_LOGO_V1 — 去掉左边的品牌图标（关于仍在 帮助 ▸ 关于）\n"
)
HEADER_NEW = (
    "    let t = app.tokens;\n"
    "    // EFFECTCRAFT_OURS_ACCOUNT_UI_V1 — 最左槽位是账号入口：未登录是 44×26「登录」文字按钮，\n"
    "    // 已登录是 26×26 圆形头像（昵称首字 + 主题色）。它就在 header 的横向流里，\n"
    "    // 所以跟随工具栏滚动，不是固定悬浮。\n"
    "    x += crate::account_ui::slot(app, ui, p, x, cy);\n"
    "    // EFFECTCRAFT_OURS_NO_BRAND_LOGO_V1 — 去掉左边的品牌图标（关于仍在 帮助 ▸ 关于）\n"
)

# 必须画在布局面板**之后**：egui 同一个 layer 里后画的在上层，而「布局」入口是
# 每帧都画的，账号面板要是先画就会被它压住（用户实测：登录面板上还能点到「布局」）。
FRAME_ANCHOR = (
    "            self.ours_layout_error(\"switcher\", \"panic inside draw_layout_switcher\");\n"
    "        }\n"
)
FRAME_INSERT = (
    "            self.ours_layout_error(\"switcher\", \"panic inside draw_layout_switcher\");\n"
    "        }\n"
    "        // EFFECTCRAFT_OURS_ACCOUNT_TOP_V1 — 账号面板永远最后画，保证在布局面板之上\n"
    "        crate::account_ui::panel(self, ui, full);\n"
)

ACCOUNT_UI = r'''//! EFFECTCRAFT_OURS_ACCOUNT_UI_V1 — 账号槽、登录/注册面板、资料卡。
//!
//! 只做界面：所有网络都走 [`crate::cloud`] 的后台线程，这里每帧 [`crate::cloud::poll`] 一次。
//! 未登录时不做任何拦截，本地功能一点不受影响。

use crate::cloud::{self, Event, Profile};
use crate::theme::Tokens;
use crate::EffectcraftApp;
use egui::{Align2, Color32, Id, Pos2, Rect, Sense, Stroke, StrokeKind, Vec2};

const PANEL: &str = "ours-account-panel"; // 0 关 / 1 登录注册 / 2 资料
const TOKEN: &str = "ours-account-token";
const PROFILE: &str = "ours-account-profile";
const MESSAGE: &str = "ours-account-message";
const USER: &str = "ours-account-user";
const PASS: &str = "ours-account-pass";
const SHOW_PASS: &str = "ours-account-show-pass";
const NICK: &str = "ours-account-nick";
const GENDER: &str = "ours-account-gender";
const BIRTH: &str = "ours-account-birth";
const SIGN: &str = "ours-account-sign";
const FETCHED: &str = "ours-account-fetched";
const USERNAME: &str = "ours-account-username";
const EDITING: &str = "ours-account-editing";
const CROP_SRC: &str = "ours-account-crop-src";
const CROP_TEX: &str = "ours-account-crop-tex";
const CROP_POS: &str = "ours-account-crop-pos";
const CROP_RATIO: &str = "ours-account-crop-ratio";

/// 文件对话框是异步的，回调可能从任意线程来：只把路径丢进这里，UI 线程下一帧再处理。
fn pending_avatar() -> &'static std::sync::Mutex<Option<String>> {
    static PENDING: std::sync::OnceLock<std::sync::Mutex<Option<String>>> = std::sync::OnceLock::new();
    PENDING.get_or_init(|| std::sync::Mutex::new(None))
}

fn take_pending_avatar() -> Option<String> {
    pending_avatar().lock().ok().and_then(|mut slot| slot.take())
}

fn get<T: 'static + Clone>(ui: &egui::Ui, key: &str) -> Option<T> {
    ui.data(|d| d.get_temp::<T>(Id::new(key)))
}

fn temp<T: 'static + Clone + Default>(ui: &egui::Ui, key: &str) -> T {
    get(ui, key).unwrap_or_default()
}

/// `IdTypeMap::insert_temp` 要求 `T: Send + Sync`（它存在 egui 的全局内存里），
/// 少了这两个 bound 就是 E0277 —— 这是 900 构建失败的原因。
fn set<T: 'static + Clone + Send + Sync>(ui: &egui::Ui, key: &str, value: T) {
    ui.data_mut(|d| d.insert_temp(Id::new(key), value));
}

/// 已登录的 token（空串 = 未登录）。
fn token(ui: &egui::Ui) -> String {
    temp::<String>(ui, TOKEN)
}

fn logged_in(ui: &egui::Ui) -> bool {
    !token(ui).is_empty()
}

/// 本地头像 texture（`<config>/avatar.png`），解码失败就 None → 退回昵称首字。
fn avatar_texture(ui: &egui::Ui) -> Option<egui::TextureHandle> {
    if let Some(handle) = get::<egui::TextureHandle>(ui, "ours-account-avatar-tex") {
        return Some(handle);
    }
    // 按当前登录用户名取头像；换账号会清缓存，所以不会串图。
    let username = temp::<String>(ui, USERNAME);
    let path = if username.is_empty() { cloud::avatar_path() } else { cloud::avatar_file(&username) };
    let bytes = std::fs::read(path).ok()?;
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

/// 贴一张 texture：`Painter::image(texture_id, rect, uv, tint)`（签名对着 egui 源码核对过）。
fn paint_texture(ui: &egui::Ui, texture: &egui::TextureHandle, rect: Rect) {
    let uv = Rect::from_min_max(egui::pos2(0.0, 0.0), egui::pos2(1.0, 1.0));
    ui.painter().image(texture.id(), rect, uv, Color32::WHITE);
}

/// 圆形头像：有本地图就用圆形 mesh 贴图（真圆形裁切），否则昵称首字 + 主题色底。
/// 两种情况都画一圈 1px 主题色描边；返回圆心和半径，供调用方判断「点在圆内」。
fn paint_avatar(ui: &egui::Ui, r: Rect, t: &Tokens, profile: &Profile) -> (Pos2, f32) {
    let center = r.center();
    let radius = r.width().min(r.height()) * 0.5;
    ui.painter().circle_filled(center, radius, t.accent);
    match avatar_texture(ui) {
        Some(texture) => paint_circle_texture(ui, &texture, center, radius),
        None => {
            ui.painter().text(
                center,
                Align2::CENTER_CENTER,
                initial(profile),
                Tokens::ui((radius * 0.95).max(10.0)),
                Color32::from_rgb(16, 18, 22),
            );
        }
    }
    ui.painter().circle_stroke(center, radius - 0.5, Stroke::new(1.0, t.accent));
    (center, radius)
}

/// 用三角扇把 texture 圆形裁切地贴到圆里（uv 也跟着走圆），这是「真圆形头像」的做法。
fn paint_circle_texture(ui: &egui::Ui, texture: &egui::TextureHandle, center: Pos2, radius: f32) {
    const SEGMENTS: usize = 48;
    let mut mesh = egui::epaint::Mesh::default();
    mesh.texture_id = texture.id();
    mesh.vertices.push(egui::epaint::Vertex {
        pos: center,
        uv: Pos2::new(0.5, 0.5),
        color: Color32::WHITE,
    });
    for i in 0..=SEGMENTS {
        let angle = i as f32 / SEGMENTS as f32 * std::f32::consts::TAU;
        let (sin, cos) = angle.sin_cos();
        mesh.vertices.push(egui::epaint::Vertex {
            pos: center + Vec2::new(cos, sin) * radius,
            uv: Pos2::new(0.5 + 0.5 * cos, 0.5 + 0.5 * sin),
            color: Color32::WHITE,
        });
    }
    for i in 0..SEGMENTS as u32 {
        mesh.add_triangle(0, i + 1, i + 2);
    }
    ui.painter().add(egui::Shape::mesh(mesh));
}

/// 读一张图：按**字节**嗅探格式，不依赖文件名后缀（SAF 的 staged 副本经常没有扩展名，
/// 而且 image 只开了 png/jpeg 两个 decoder，所以 webp 之类本来就读不了）。
fn load_picture(path: &str) -> Option<image::DynamicImage> {
    let bytes = std::fs::read(path).ok()?;
    image::load_from_memory(&bytes).ok()
}

/// 选好的图 → 中心裁正方形（不拉伸）→ 缩到 256×256 → 存成 `<config>/avatar/<username>.png`。
#[allow(dead_code)]
fn save_avatar(source: &str, username: &str) -> bool {
    let Some(image) = load_picture(source) else {
        return false;
    };
    // resize_to_fill 就是「中心裁正方形再缩放」，不会拉伸变形。
    store_avatar(image, username)
}

/// 裁好的图直接落盘。
fn store_avatar(image: image::DynamicImage, username: &str) -> bool {
    let square = image.resize_to_fill(256, 256, image::imageops::FilterType::Lanczos3);
    if std::fs::create_dir_all(cloud::avatar_dir()).is_err() {
        return false;
    }
    square.save(cloud::avatar_file(username)).is_ok()
}

/// 打开系统的图片选择（走 App 现成的非阻塞文件对话框钩子，不会卡住 UI 帧）。
fn pick_avatar(app: &EffectcraftApp, ui: &egui::Ui) {
    let Some(spawn) = app.hooks.file_dialog_async.as_ref() else {
        return;
    };
    let dialog = crate::FileDialog::Open {
        exts: vec!["png".to_string(), "jpg".to_string(), "jpeg".to_string(), "webp".to_string()],
        many: false,
    };
    let done: crate::DialogDone = Box::new(|paths| {
        if let Some(path) = paths.into_iter().next() {
            if let Ok(mut slot) = pending_avatar().lock() {
                *slot = Some(path);
            }
        }
    });
    spawn(dialog, done);
    ui.ctx().request_repaint();
}

/// "1990-01-02" → (1990, 1, 2)；坏数据给一个安全默认值。
fn parse_birthday(text: &str) -> (i32, i32, i32) {
    let parts: Vec<i32> = text.split('-').filter_map(|p| p.trim().parse().ok()).collect();
    match parts.as_slice() {
        [y, m, d] => ((*y).clamp(1900, 2030), (*m).clamp(1, 12), (*d).clamp(1, 31)),
        _ => (1990, 1, 1),
    }
}

/// 一个 +/- 调节器（用作年/月/日）。
fn stepper(ui: &mut egui::Ui, t: &Tokens, r: Rect, value: &mut i32, min: i32, max: i32) -> bool {
    let btn = 22.0;
    let minus = Rect::from_min_size(r.min, Vec2::new(btn, r.height()));
    let plus = Rect::from_min_size(Pos2::new(r.max.x - btn, r.min.y), Vec2::new(btn, r.height()));
    let mid = Rect::from_min_max(Pos2::new(r.min.x + btn, r.min.y), Pos2::new(r.max.x - btn, r.max.y));
    let mut changed = false;
    if button(ui, t, minus, "-", false) {
        *value = (*value - 1).max(min);
        changed = true;
    }
    if button(ui, t, plus, "+", false) {
        *value = (*value + 1).min(max);
        changed = true;
    }
    ui.painter().rect_filled(mid, 4.0, t.field_bg);
    ui.painter().text(mid.center(), Align2::CENTER_CENTER, format!("{value}"), Tokens::ui(12.5), t.text);
    changed
}

fn initial(profile: &Profile) -> String {
    profile
        .nickname
        .chars()
        .next()
        .map(|c| c.to_string())
        .unwrap_or_else(|| "我".to_string())
}

/// 工具栏最左槽位：未登录是「登录」文字按钮，已登录是圆形头像。返回它占的宽度。
///
/// 包一层 `catch_unwind`：账号槽在工具栏里，它要是 panic 会连累整个 header 乃至主循环。
/// 坏一次就永久不画（返回 0 宽度），界面照旧，只是没有账号入口。
pub fn slot(app: &mut EffectcraftApp, ui: &mut egui::Ui, p: &egui::Painter, x: f32, cy: f32) -> f32 {
    let crashed = ui.data(|d| d.get_temp::<bool>(Id::new("ours-account-crashed")).unwrap_or(false));
    if crashed {
        return 0.0;
    }
    match std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| slot_inner(app, ui, p, x, cy))) {
        Ok(width) => width,
        Err(_) => {
            ui.data_mut(|d| d.insert_temp(Id::new("ours-account-crashed"), true));
            0.0
        }
    }
}

fn slot_inner(app: &mut EffectcraftApp, ui: &mut egui::Ui, p: &egui::Painter, x: f32, cy: f32) -> f32 {
    let t = app.tokens;
    let (resp, inside_circle) = if logged_in(ui) {
        let profile = temp::<Profile>(ui, PROFILE);
        let r = Rect::from_center_size(Pos2::new(x + 13.0, cy), Vec2::splat(26.0));
        let resp = ui.interact(r, Id::unique("ours-account-slot"), Sense::click());
        // 有本账号头像就圆形贴图，否则昵称首字 + 主题色底。
        let (center, radius) = paint_avatar(ui, r, &t, &profile);
        app.auto.add("account.slot", r, "账号");
        // 点击区域是**圆**，不是方形外接框：只有点在圆内才算点中。
        let inside = ui
            .input(|i| i.pointer.interact_pos())
            .map(|p| p.distance(center) <= radius)
            .unwrap_or(false);
        (resp, inside)
    } else {
        let r = Rect::from_min_size(Pos2::new(x, cy - 13.0), Vec2::new(44.0, 26.0));
        let resp = ui.interact(r, Id::unique("ours-account-slot"), Sense::click());
        p.rect_filled(r, 4.0, if resp.hovered() { t.hover } else { t.switch_well });
        p.text(r.center(), Align2::CENTER_CENTER, "登录", Tokens::ui(12.0), t.text);
        app.auto.add("account.slot", r, "登录");
        (resp, true)
    };
    let width = if logged_in(ui) { 28.0 } else { 48.0 };
    if resp.clicked() && inside_circle {
        set(ui, PANEL, if logged_in(ui) { 2_u8 } else { 1 });
        // 打开资料卡时先把输入框填成当前资料。
        if logged_in(ui) {
            let profile = temp::<Profile>(ui, PROFILE);
            fill_fields(ui, &profile);
            // 打开资料卡时拉一次 GET /me 刷新显示（失败只提示，不动本地编辑）。
            let token = token(ui);
            if !token.is_empty() {
                cloud::fetch_me(token);
            }
        }
        set(ui, MESSAGE, String::new());
    }
    width
}

fn fill_fields(ui: &egui::Ui, profile: &Profile) {
    set(ui, NICK, profile.nickname.clone());
    set(ui, GENDER, profile.gender.clone());
    set(ui, BIRTH, profile.birthday.clone());
    set(ui, SIGN, profile.signature.clone());
}

/// 每帧在 frame.rs 的末尾调用一次：收后台结果、画正在打开的面板。
/// 同样包一层 `catch_unwind`：面板出错最多是「点了没反应」，绝不让主循环崩。
pub fn panel(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: Rect) {
    let crashed = get::<bool>(ui, "ours-account-panel-crashed").unwrap_or(false);
    if crashed {
        return;
    }
    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| panel_inner(app, ui, full))).is_err() {
        set(ui, "ours-account-panel-crashed", true);
        set(ui, PANEL, 0_u8);
    }
}

fn panel_inner(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: Rect) {
    // 有面板打开时，先铺一层全屏交互：它在这帧里最后注册，所以吃掉下面所有面板的点击，
    // 再配合下面清掉滚轮，做到「整屏不可穿透」。
    let open = temp::<u8>(ui, PANEL) != 0;
    if open {
        let screen = ui.interact(full, egui::Id::unique("ours-account-modal"), Sense::click_and_drag());
        if screen.hovered() {
            ui.ctx().input_mut(|i| {
                i.smooth_scroll_delta = egui::Vec2::ZERO;
            });
        }
    }
    // 后台结果只在 UI 线程落地。
    for event in cloud::poll() {
        match event {
            Event::LoggedIn { token: fresh, username, profile } => {
                set(ui, TOKEN, fresh);
                set(ui, USERNAME, username);
                set(ui, PROFILE, profile.clone());
                fill_fields(ui, &profile);
                set(ui, PANEL, 0_u8);
                set(ui, MESSAGE, String::new());
                // 换了账号，头像缓存必须清掉，否则会显示上一个账号的图。
                ui.data_mut(|d| d.remove::<egui::TextureHandle>(Id::new("ours-account-avatar-tex")));
                app.ui.status = "已登录".to_string();
            }
            Event::LoginFailed(message) => set(ui, MESSAGE, message),
            Event::Profile(profile) => {
                set(ui, PROFILE, profile.clone());
                fill_fields(ui, &profile);
            }
            Event::SaveOk => {
                set(ui, MESSAGE, String::new());
                app.ui.status = "资料已保存".to_string();
            }
            Event::SaveFailed(message) | Event::Failed(message) => set(ui, MESSAGE, message),
            Event::SessionExpired => {
                set(ui, TOKEN, String::new());
                set(ui, USERNAME, String::new());
                set(ui, PROFILE, Profile::default());
                ui.data_mut(|d| d.remove::<egui::TextureHandle>(Id::new("ours-account-avatar-tex")));
                set(ui, PANEL, 0_u8);
                set(ui, MESSAGE, String::new());
                app.ui.status = "登录已过期，请重新登录".to_string();
            }
        }
    }
    // 启动后第一次：有 token 就静默拉一次资料（失败也只是回到未登录）。
    if !get::<bool>(ui, FETCHED).unwrap_or(false) {
        set(ui, FETCHED, true);
        if let Some((stored, username)) = cloud::load_account() {
            set(ui, TOKEN, stored.clone());
            set(ui, USERNAME, username);
            // 启动就用 token 验一次；401 会走 SessionExpired 静默登出。
            cloud::fetch_me(stored);
        }
    }
    // 上一帧文件对话框选好了图：裁成 256×256 存到 <config>/avatar/<username>.png，
    // 再清掉 texture 缓存让界面立刻换图（不用重启）。
    if let Some(path) = take_pending_avatar() {
        if temp::<String>(ui, USERNAME).is_empty() {
            set(ui, MESSAGE, "请先登录再换头像".to_string());
        } else if load_picture(&path).is_some() {
            // 先别裁：进裁剪页让用户自己调取景，确认后才落盘。
            ui.data_mut(|d| d.remove::<egui::TextureHandle>(Id::new(CROP_TEX)));
            set(ui, CROP_SRC, path);
            set(ui, CROP_POS, Vec2::new(0.5, 0.5));
            set(ui, CROP_RATIO, 0.85_f32);
            set(ui, PANEL, 3_u8);
        } else {
            set(ui, MESSAGE, "这个图片读不了，换一张试试".to_string());
        }
    }
    match temp::<u8>(ui, PANEL) {
        1 => auth_panel(app, ui, full),
        2 => profile_panel(app, ui, full),
        3 => crop_panel(app, ui, full),
        _ => {}
    }
}

fn scrim(ui: &egui::Ui, full: Rect) {
    ui.painter().rect_filled(full, 0.0, Color32::from_black_alpha(170));
}

fn card(t: &Tokens, ui: &egui::Ui, full: Rect, width: f32, height: f32, title: &str) -> Rect {
    let w = width.min(full.width() - 24.0);
    let card = Rect::from_center_size(full.center(), Vec2::new(w, height));
    ui.painter().rect_filled(card, 12.0, t.panel_bg);
    ui.painter().rect_stroke(card, 12.0, Stroke::new(1.0, t.field_border), StrokeKind::Inside);
    ui.painter().text(
        Pos2::new(card.center().x, card.min.y + 24.0),
        Align2::CENTER_CENTER,
        title,
        Tokens::semibold(15.0),
        t.text,
    );
    card
}

/// 一个输入框；返回是否被改过。
fn field(ui: &mut egui::Ui, t: &Tokens, r: Rect, key: &str, hint: &str, password: bool) -> bool {
    let mut value = temp::<String>(ui, key);
    let mut edit = egui::TextEdit::singleline(&mut value)
        .hint_text(hint)
        .text_color(t.text)
        .font(Tokens::ui(12.5))
        // 框高 30px，默认 margin 让文字偏上；给上下各 6px 就是垂直居中。
        .margin(egui::Margin::symmetric(8, 6));
    if password {
        edit = edit.password(true);
    }
    let changed = ui.put(r, edit).changed();
    if changed {
        set(ui, key, value);
    }
    changed
}

/// 密码框右边的小眼睛：睁眼 = 外圈 + 瞳孔，闭眼 = 再压一条斜线。
fn paint_eye(p: &egui::Painter, center: Pos2, open: bool, color: Color32) {
    p.circle_stroke(center, 6.5, Stroke::new(1.0, color));
    if open {
        p.circle_filled(center, 2.6, color);
    } else {
        // 闭眼：一条从左上到右下的斜线，盖住瞳孔
        p.line_segment(
            [center + Vec2::new(-7.0, 7.0), center + Vec2::new(7.0, -7.0)],
            Stroke::new(1.3, color),
        );
    }
}

fn button(ui: &mut egui::Ui, t: &Tokens, r: Rect, label: &str, primary: bool) -> bool {
    // Id 里必须带上位置：三个生日 stepper 的 "-"/"+" 文字相同，只用 label 会撞成同一个
    // widget，表现就是「只有第一个能点，日期改不了」。
    let id = egui::Id::new(("ours-account-btn", label, r.min.x as i32, r.min.y as i32));
    let resp = ui.interact(r, id, Sense::click());
    let fill = if primary {
        if resp.hovered() { t.accent_hover } else { t.accent }
    } else if resp.hovered() {
        t.hover
    } else {
        t.switch_well
    };
    ui.painter().rect_filled(r, 6.0, fill);
    let color = if primary { Color32::from_rgb(16, 18, 22) } else { t.text };
    ui.painter().text(r.center(), Align2::CENTER_CENTER, label, Tokens::ui(12.5), color);
    resp.clicked()
}

fn auth_panel(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: Rect) {
    let t = app.tokens;
    scrim(ui, full);
    let card = card(&t, ui, full, 320.0, 268.0, "登录 ShimoveAex");
    let left = card.min.x + 18.0;
    let width = card.width() - 36.0;
    let row = |y: f32, w: f32| Rect::from_min_size(Pos2::new(left, card.min.y + y), Vec2::new(w, 30.0));

    field(ui, &t, row(48.0, width), USER, "用户名（3~20 位字母数字下划线）", false);

    let pass_row = row(88.0, width);
    let field_rect = Rect::from_min_size(pass_row.min, Vec2::new(width - 36.0, 30.0));
    field(ui, &t, field_rect, PASS, "密码（至少 8 位）", !get::<bool>(ui, SHOW_PASS).unwrap_or(false));
    let eye = Rect::from_min_size(Pos2::new(pass_row.max.x - 32.0, pass_row.min.y), Vec2::new(32.0, 30.0));
    let eye_resp = ui.interact(eye, Id::unique("ours-account-eye"), Sense::click());
    let shown = get::<bool>(ui, SHOW_PASS).unwrap_or(false);
    // 眼睛图标自绘：外圈 + 瞳孔，闭眼时加一条斜线。不用 emoji（系统字体常常没有），
    // 也不用「显/隐」两个字（用户要的是眼睛）。
    let eye_color = if eye_resp.hovered() { t.text } else { t.text_dim };
    paint_eye(ui.painter(), eye.center(), shown, eye_color);
    if eye_resp.clicked() {
        set(ui, SHOW_PASS, !shown);
    }

    let user_value = temp::<String>(ui, USER);
    let pass_value = temp::<String>(ui, PASS);
    let mut submit = None;
    if button(ui, &t, row(130.0, 132.0), "登录", true) {
        submit = Some(true);
    }
    if button(ui, &t, Rect::from_min_size(Pos2::new(left + 140.0, card.min.y + 130.0), Vec2::new(132.0, 30.0)), "注册", false) {
        submit = Some(false);
    }
    if let Some(as_login) = submit {
        let name = user_value.trim().to_string();
        if name.chars().count() < 3 {
            set(ui, MESSAGE, "用户名至少 3 位".to_string());
        } else if pass_value.chars().count() < 8 {
            set(ui, MESSAGE, "密码至少 8 位".to_string());
        } else {
            set(ui, MESSAGE, if as_login { "正在登录…" } else { "正在注册…" }.to_string());
            if as_login {
                cloud::login(name, pass_value.clone());
            } else {
                cloud::register(name, pass_value.clone());
            }
        }
    }

    let message = temp::<String>(ui, MESSAGE);
    if !message.is_empty() {
        ui.painter().text(
            Pos2::new(card.center().x, card.min.y + 178.0),
            Align2::CENTER_CENTER,
            message,
            Tokens::ui(11.5),
            t.warning,
        );
    }

    let later = Rect::from_min_size(Pos2::new(left, card.min.y + 196.0), Vec2::new(width, 28.0));
    let later_resp = ui.interact(later, Id::unique("ours-account-later"), Sense::click());
    ui.painter().text(
        later.center(),
        Align2::CENTER_CENTER,
        "稍后再说（不影响本地功能）",
        Tokens::ui(11.5),
        t.text_dim,
    );
    let esc = ui.input(|i| i.key_pressed(egui::Key::Escape));
    if later_resp.clicked() || esc {
        set(ui, PANEL, 0_u8);
        set(ui, MESSAGE, String::new());
    }
    app.auto.add("account.auth", later, "稍后再说");
}

/// 从字节加载一张 texture（按内容嗅探格式），用于裁剪页显示原图。
fn picture_texture(ui: &egui::Ui, path: &str, key: &str) -> Option<egui::TextureHandle> {
    if let Some(handle) = get::<egui::TextureHandle>(ui, key) {
        return Some(handle);
    }
    let image = load_picture(path)?;
    let rgba = image.to_rgba8();
    let (w, h) = rgba.dimensions();
    if w == 0 || h == 0 {
        return None;
    }
    let color = egui::ColorImage::from_rgba_unmultiplied([w as usize, h as usize], rgba.as_raw());
    let handle = ui.ctx().load_texture(key, color, egui::TextureOptions::LINEAR);
    set(ui, key, handle.clone());
    Some(handle)
}

/// 裁剪页：显示原图，用户可以拖方框、改大小，确认后按方框逐像素裁切再缩到 256×256。
fn crop_panel(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: Rect) {
    let t = app.tokens;
    let src = temp::<String>(ui, CROP_SRC);
    if src.is_empty() {
        set(ui, PANEL, 2_u8);
        return;
    }
    scrim(ui, full);
    let card = card(&t, ui, full, 380.0, 520.0, "调整头像");
    let left = card.min.x + 16.0;
    let width = card.width() - 32.0;
    let Some(texture) = picture_texture(ui, &src, CROP_TEX) else {
        set(ui, MESSAGE, "这个图片读不了，换一张试试".to_string());
        set(ui, PANEL, 2_u8);
        return;
    };
    let size = texture.size_vec2();
    // 原图等比放进卡片上部
    let stage = Rect::from_min_size(Pos2::new(left, card.min.y + 44.0), Vec2::new(width, 330.0));
    let scale = (stage.width() / size.x).min(stage.height() / size.y);
    let shown = Vec2::new(size.x * scale, size.y * scale);
    let image_rect = Rect::from_center_size(stage.center(), shown);
    ui.painter().rect_filled(image_rect.expand(1.0), 4.0, t.field_bg);
    paint_texture(ui, &texture, image_rect);

    // 方框：位置用相对原图的比例，大小是短边的比例
    let mut ratio = get::<f32>(ui, CROP_RATIO).unwrap_or(0.85).clamp(0.2, 1.0);
    let mut pos = get::<Vec2>(ui, CROP_POS).unwrap_or(Vec2::new(0.5, 0.5));
    let short = shown.x.min(shown.y);
    let side = short * ratio;
    let centre = image_rect.min + Vec2::new(pos.x * shown.x, pos.y * shown.y);
    let frame = Rect::from_center_size(centre, Vec2::splat(side));

    // 拖动方框
    let drag = ui.interact(image_rect, Id::unique("ours-account-crop-drag"), Sense::drag());
    if drag.dragged() {
        let d = drag.drag_delta();
        pos.x = (pos.x + d.x / shown.x.max(1.0)).clamp(0.0, 1.0);
        pos.y = (pos.y + d.y / shown.y.max(1.0)).clamp(0.0, 1.0);
        set(ui, CROP_POS, pos);
    }
    // 方框外的四块压暗，中心留亮，直观看出裁的是什么
    let shade = Color32::from_black_alpha(150);
    let p = ui.painter();
    p.rect_filled(Rect::from_min_max(image_rect.min, Pos2::new(image_rect.max.x, frame.min.y)), 0.0, shade);
    p.rect_filled(Rect::from_min_max(Pos2::new(image_rect.min.x, frame.max.y), image_rect.max), 0.0, shade);
    p.rect_filled(Rect::from_min_max(Pos2::new(image_rect.min.x, frame.min.y), Pos2::new(frame.min.x, frame.max.y)), 0.0, shade);
    p.rect_filled(Rect::from_min_max(Pos2::new(frame.max.x, frame.min.y), Pos2::new(image_rect.max.x, frame.max.y)), 0.0, shade);
    p.rect_stroke(frame, 0.0, Stroke::new(1.5, Color32::WHITE), StrokeKind::Inside);
    p.rect_stroke(frame.shrink(1.0), 0.0, Stroke::new(1.0, t.accent), StrokeKind::Inside);

    // 大小滑块
    let slider_rect = Rect::from_min_size(Pos2::new(left, card.min.y + 392.0), Vec2::new(width, 24.0));
    {
        let mut value = ratio;
        let changed = ui
            .put(slider_rect, egui::Slider::new(&mut value, 0.2..=1.0).show_value(false))
            .changed();
        if changed {
            ratio = value;
            set(ui, CROP_RATIO, ratio);
        }
    }
    ui.painter().text(
        Pos2::new(card.center().x, card.min.y + 420.0),
        Align2::CENTER_CENTER,
        "拖动图片移动位置，下面的滑杆调整取景范围",
        Tokens::ui(10.5),
        t.text_faint,
    );

    // 确定 / 取消
    let btn_y = card.min.y + 444.0;
    let bw = (width - 8.0) / 2.0;
    if button(ui, &t, Rect::from_min_size(Pos2::new(left, btn_y), Vec2::new(bw, 30.0)), "确定", true) {
        let username = temp::<String>(ui, USERNAME);
        // 闭包返回 Option<bool>：里面用 `?` 提前退出，外面 unwrap_or(false) 收口。
        let done = (|| -> Option<bool> {
            let image = load_picture(&src)?;
            let (w, h) = (image.width() as f32, image.height() as f32);
            let short_px = w.min(h);
            let side_px = (short_px * ratio).max(8.0);
            let cx = pos.x * w;
            let cy = pos.y * h;
            let x = (cx - side_px * 0.5).clamp(0.0, (w - side_px).max(0.0));
            let y = (cy - side_px * 0.5).clamp(0.0, (h - side_px).max(0.0));
            let cropped = image.crop_imm(x as u32, y as u32, side_px as u32, side_px as u32);
            Some(store_avatar(cropped, &username))
        })()
        .unwrap_or(false);
        if done {
            ui.data_mut(|d| d.remove::<egui::TextureHandle>(Id::new("ours-account-avatar-tex")));
            ui.data_mut(|d| d.remove::<egui::TextureHandle>(Id::new(CROP_TEX)));
            set(ui, CROP_SRC, String::new());
            set(ui, MESSAGE, "头像已更新".to_string());
        } else {
            set(ui, MESSAGE, "这个图片读不了，换一张试试".to_string());
        }
        set(ui, PANEL, 2_u8);
    }
    if button(ui, &t, Rect::from_min_size(Pos2::new(left + bw + 8.0, btn_y), Vec2::new(bw, 30.0)), "取消", false) {
        ui.data_mut(|d| d.remove::<egui::TextureHandle>(Id::new(CROP_TEX)));
        set(ui, CROP_SRC, String::new());
        set(ui, PANEL, 2_u8);
    }
}

/// 只读的一行：左边小标签，右边值。
fn plain_row(ui: &egui::Ui, t: &Tokens, left: f32, y: f32, label: &str, value: &str) {
    ui.painter().text(Pos2::new(left, y), Align2::LEFT_CENTER, label, Tokens::ui(11.5), t.text_dim);
    let shown = if value.trim().is_empty() { "—" } else { value };
    ui.painter().text(Pos2::new(left + 62.0, y), Align2::LEFT_CENTER, shown, Tokens::ui(12.5), t.text);
}

fn profile_panel(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: Rect) {
    let t = app.tokens;
    let editing = get::<bool>(ui, EDITING).unwrap_or(false);
    scrim(ui, full);
    let card = card(&t, ui, full, 340.0, 452.0, if editing { "编辑资料" } else { "我的资料" });
    let left = card.min.x + 18.0;
    let width = card.width() - 36.0;
    let row = |y: f32| Rect::from_min_size(Pos2::new(left, card.min.y + y), Vec2::new(width, 30.0));

    // 头像：点圆形区域 → 换图（点击判定在圆内，不是方形外接框）。只读时也能点。
    let profile = temp::<Profile>(ui, PROFILE);
    let avatar_rect = Rect::from_center_size(Pos2::new(card.center().x, card.min.y + 72.0), Vec2::splat(48.0));
    let (avatar_center, avatar_radius) = paint_avatar(ui, avatar_rect, &t, &profile);
    let avatar_resp = ui.interact(avatar_rect, Id::unique("ours-account-avatar-hit"), Sense::click());
    let hits_circle = |ui: &egui::Ui| {
        ui.input(|i| i.pointer.interact_pos())
            .map(|p| p.distance(avatar_center) <= avatar_radius)
            .unwrap_or(false)
    };
    if avatar_resp.hovered() && hits_circle(ui) {
        ui.ctx().set_cursor_icon(egui::CursorIcon::PointingHand);
    }
    if avatar_resp.clicked() && hits_circle(ui) {
        pick_avatar(app, ui);
    }
    ui.painter().text(
        Pos2::new(card.center().x, card.min.y + 104.0),
        Align2::CENTER_CENTER,
        "点头像更换",
        Tokens::ui(10.5),
        t.text_faint,
    );

    let gap = 6.0;
    if editing {
        // 昵称
        field(ui, &t, row(122.0), NICK, "昵称", false);
        // 性别：男 / 女 / 保密
        let gender = temp::<String>(ui, GENDER);
        let gy = card.min.y + 162.0;
        let gw = (width - gap * 2.0) / 3.0;
        for (i, label) in ["男", "女", "保密"].iter().enumerate() {
            let r = Rect::from_min_size(Pos2::new(left + i as f32 * (gw + gap), gy), Vec2::new(gw, 28.0));
            if button(ui, &t, r, label, gender == *label) {
                set(ui, GENDER, label.to_string());
            }
        }
        // 生日：年 / 月 / 日
        let (mut year, mut month, mut day) = parse_birthday(&temp::<String>(ui, BIRTH));
        let by = card.min.y + 200.0;
        let unit_w = (width - gap * 2.0) / 3.0;
        let mut birth_changed = false;
        birth_changed |= stepper(ui, &t, Rect::from_min_size(Pos2::new(left, by), Vec2::new(unit_w, 28.0)), &mut year, 1900, 2030);
        birth_changed |= stepper(ui, &t, Rect::from_min_size(Pos2::new(left + unit_w + gap, by), Vec2::new(unit_w, 28.0)), &mut month, 1, 12);
        birth_changed |= stepper(ui, &t, Rect::from_min_size(Pos2::new(left + (unit_w + gap) * 2.0, by), Vec2::new(unit_w, 28.0)), &mut day, 1, 31);
        if birth_changed {
            set(ui, BIRTH, format!("{year:04}-{month:02}-{day:02}"));
        }
        // 个性签名：多行
        let mut sign = temp::<String>(ui, SIGN);
        let rect = Rect::from_min_size(Pos2::new(left, card.min.y + 238.0), Vec2::new(width, 76.0));
        let edit = egui::TextEdit::multiline(&mut sign)
            .hint_text("个性签名")
            .text_color(t.text)
            .font(Tokens::ui(12.5))
            .margin(egui::Margin::symmetric(8, 6))
            .desired_rows(3);
        if ui.put(rect, edit).changed() {
            set(ui, SIGN, sign);
        }
    } else {
        // 只读：一眼看完，不出现输入框
        let nick = temp::<String>(ui, NICK);
        let gender = temp::<String>(ui, GENDER);
        let birth = temp::<String>(ui, BIRTH);
        let sign = temp::<String>(ui, SIGN);
        let rows = [
            ("昵称", nick.as_str()),
            ("性别", gender.as_str()),
            ("生日", birth.as_str()),
            ("签名", sign.as_str()),
        ];
        for (i, (label, value)) in rows.iter().enumerate() {
            let y = card.min.y + 130.0 + i as f32 * 34.0;
            ui.painter().rect_filled(
                Rect::from_min_size(Pos2::new(left, y - 14.0), Vec2::new(width, 28.0)),
                4.0,
                t.field_bg,
            );
            let clipped: String = value.chars().take(28).collect();
            plain_row(ui, &t, left + 8.0, y, label, &clipped);
        }
    }

    // 按钮：只读时「编辑 / 关闭 / 退出登录」，编辑时「保存 / 取消 / 退出登录」
    let btn_y = card.min.y + 326.0;
    let bw = (width - gap * 2.0) / 3.0;
    if editing {
        if button(ui, &t, Rect::from_min_size(Pos2::new(left, btn_y), Vec2::new(bw, 30.0)), "保存", true) {
            let edited = Profile {
                nickname: temp::<String>(ui, NICK).trim().to_string(),
                gender: temp::<String>(ui, GENDER).trim().to_string(),
                birthday: temp::<String>(ui, BIRTH).trim().to_string(),
                signature: temp::<String>(ui, SIGN).trim().to_string(),
            };
            let token = token(ui);
            if token.is_empty() {
                set(ui, MESSAGE, "登录已失效，请重新登录".to_string());
            } else {
                set(ui, PROFILE, edited.clone());
                set(ui, MESSAGE, "正在保存…".to_string());
                cloud::save_profile(token, edited);
            }
            set(ui, EDITING, false);
        }
        if button(ui, &t, Rect::from_min_size(Pos2::new(left + bw + gap, btn_y), Vec2::new(bw, 30.0)), "取消", false) {
            // 丢弃这次编辑：把输入框恢复成已保存的资料
            let profile = temp::<Profile>(ui, PROFILE);
            fill_fields(ui, &profile);
            set(ui, EDITING, false);
            set(ui, MESSAGE, String::new());
        }
    } else {
        if button(ui, &t, Rect::from_min_size(Pos2::new(left, btn_y), Vec2::new(bw, 30.0)), "编辑", true) {
            let profile = temp::<Profile>(ui, PROFILE);
            fill_fields(ui, &profile);
            set(ui, EDITING, true);
            set(ui, MESSAGE, String::new());
        }
        if button(ui, &t, Rect::from_min_size(Pos2::new(left + bw + gap, btn_y), Vec2::new(bw, 30.0)), "关闭", false) {
            set(ui, PANEL, 0_u8);
            set(ui, MESSAGE, String::new());
        }
    }
    if button(ui, &t, Rect::from_min_size(Pos2::new(left + (bw + gap) * 2.0, btn_y), Vec2::new(bw, 30.0)), "退出登录", false) {
        cloud::logout();
        set(ui, TOKEN, String::new());
        set(ui, USERNAME, String::new());
        set(ui, PROFILE, Profile::default());
        set(ui, EDITING, false);
        set(ui, PANEL, 0_u8);
        ui.data_mut(|d| d.remove::<egui::TextureHandle>(Id::new("ours-account-avatar-tex")));
        app.ui.status = "已退出登录".to_string();
    }

    let message = temp::<String>(ui, MESSAGE);
    if !message.is_empty() {
        ui.painter().text(
            Pos2::new(card.center().x, card.min.y + 400.0),
            Align2::CENTER_CENTER,
            message,
            Tokens::ui(11.0),
            t.warning,
        );
    }
    if ui.input(|i| i.key_pressed(egui::Key::Escape)) {
        set(ui, PANEL, 0_u8);
        set(ui, EDITING, false);
        set(ui, MESSAGE, String::new());
    }
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    lib = root / "crates/ui-egui/src/lib.rs"
    src = lib.read_text(encoding="utf-8")
    if "mod account_ui;" not in src:
        if src.count(LIB_ANCHOR) != 1:
            raise SystemExit(f"lib anchor: {src.count(LIB_ANCHOR)}")
        lib.write_text(src.replace(LIB_ANCHOR, LIB_INSERT, 1), encoding="utf-8")
        print("lib.rs: account_ui registered")

    module = root / "crates/ui-egui/src/account_ui.rs"
    if not module.exists():
        module.write_text(ACCOUNT_UI, encoding="utf-8")
        print("account_ui.rs: written")

    header = root / "crates/ui-egui/src/header.rs"
    src = header.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(HEADER_OLD) != 1:
            raise SystemExit(f"header anchor: {src.count(HEADER_OLD)}")
        header.write_text(src.replace(HEADER_OLD, HEADER_NEW, 1), encoding="utf-8")
        print("header.rs: account slot in the left-most toolbar slot")

    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if "crate::account_ui::panel" not in src:
        if src.count(FRAME_ANCHOR) != 1:
            raise SystemExit(f"frame anchor: {src.count(FRAME_ANCHOR)}")
        frame.write_text(src.replace(FRAME_ANCHOR, FRAME_INSERT, 1), encoding="utf-8")
        print("frame.rs: account panel drawn at the end of the frame")


if __name__ == "__main__":
    main()
