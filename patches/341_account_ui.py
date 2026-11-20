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
# 337 现在只留 `curves_editor(self, ui, full);`（布局按钮搬到 357 的 Middle 层 Area 里），
# 所以账号面板改为紧跟曲线编辑器插入。
FRAME_ANCHOR = "        curves_editor(self, ui, full);\n"
FRAME_INSERT = (
    "        curves_editor(self, ui, full);\n"
    "        // EFFECTCRAFT_OURS_ACCOUNT_TOP_V1 — 账号面板在所有浮层之后画\n"
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
const BANNED: &str = "ours-account-banned";
const PROJECTS: &str = "ours-cloud-projects";
const UPLOADING: &str = "ours-cloud-uploading";
const CONFIRM_DELETE: &str = "ours-cloud-confirm-delete";
const LAST_STATE: &str = "ours-account-last-state";
const WAS_FOCUSED: &str = "ours-account-was-focused";
const CLOUD_LOADING: &str = "ours-cloud-loading";
const LAST_PANEL: &str = "ours-account-last-panel";
const NOTICE_TITLE: &str = "ours-notice-title";
const NOTICE_BODY: &str = "ours-notice-body";
const NOTICE_AT: &str = "ours-notice-at";

/// 「另存为」对话框的回调（任意线程）→ 下一帧再拿路径去保存并上传。
fn pending_save() -> &'static std::sync::Mutex<Option<String>> {
    static SAVE: std::sync::OnceLock<std::sync::Mutex<Option<String>>> = std::sync::OnceLock::new();
    SAVE.get_or_init(|| std::sync::Mutex::new(None))
}

fn take_pending_save() -> Option<String> {
    pending_save().lock().ok().and_then(|mut slot| slot.take())
}

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
    // 有头像图就不要再铺主题色圆底：椭圆边缘会透出一圈蓝/青，用户看到的就是「头像上有一层蓝」。
    let texture = avatar_texture(ui);
    if texture.is_none() {
        ui.painter().circle_filled(center, radius, t.accent);
    }
    match texture {
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
    // 用户要求去掉头像外面那圈蓝边：只画圆形贴图/首字，不再描边。
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
    // 循环：12 月往后是 1 月，1 月往前是 12 月；日也是 31 ↔ 1。
    if button(ui, t, minus, "-", false) {
        *value = if *value <= min { max } else { *value - 1 };
        changed = true;
    }
    if button(ui, t, plus, "+", false) {
        *value = if *value >= max { min } else { *value + 1 };
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
        let resp = ui.interact(r, Id::unique("ours-account-slot"), egui::Sense::click());
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
        let resp = ui.interact(r, Id::unique("ours-account-slot"), egui::Sense::click());
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

/// 账号类的错误统一走这里：标题 + 正文，居中玻璃弹窗（不再是按钮下面那行橙色小字）。
/// `pub`：`.ffx` 预设导入的汇总弹窗也复用它。
pub fn show_notice(ui: &egui::Ui, title: &str, body: &str) {
    set(ui, NOTICE_TITLE, title.to_string());
    set(ui, NOTICE_BODY, body.to_string());
    set(ui, NOTICE_AT, ui.input(|i| i.time));
    ui.ctx().request_repaint();
}

/// 只拿得到 `Context` 的地方（比如导入面板里的 `.ffx` 汇总）用这个。
pub fn show_notice_ctx(ctx: &egui::Context, title: &str, body: &str) {
    let (title, body) = (title.to_string(), body.to_string());
    ctx.data_mut(|d| {
        d.insert_temp(Id::new(NOTICE_TITLE), title);
        d.insert_temp(Id::new(NOTICE_BODY), body);
    });
    let now = ctx.input(|i| i.time);
    ctx.data_mut(|d| d.insert_temp(Id::new(NOTICE_AT), now));
    ctx.request_repaint();
}

fn close_notice(ui: &egui::Ui) {
    set(ui, NOTICE_TITLE, String::new());
    set(ui, NOTICE_BODY, String::new());
}

/// 居中玻璃弹窗：0.35 的遮罩 + rgba(20,22,26,0.82) 圆角 18 + 150ms 淡入。
fn notice_panel(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: Rect) {
    let t = app.tokens;
    let title = temp::<String>(ui, NOTICE_TITLE);
    if title.is_empty() {
        return;
    }
    let body = temp::<String>(ui, NOTICE_BODY);
    let at = get::<f64>(ui, NOTICE_AT).unwrap_or(0.0);
    let now = ui.input(|i| i.time);
    // 150ms 淡入
    let fade = if at <= 0.0 { 1.0 } else { ((now - at) / 0.15).clamp(0.0, 1.0) as f32 };
    if fade < 1.0 {
        ui.ctx().request_repaint();
    }
    // 遮罩（alpha 0.35）；点它关闭
    ui.painter().rect_filled(full, 0.0, Color32::from_black_alpha((89.0 * fade) as u8));
    let backdrop = ui.interact(full, Id::unique("ours-notice-backdrop"), egui::Sense::click());
    if backdrop.clicked() {
        close_notice(ui);
        return;
    }
    let width = 320.0_f32.min(full.width() - 32.0);
    let card = Rect::from_center_size(full.center(), Vec2::new(width, 176.0));
    // 背景 rgba(20,22,26,0.82) + 圆角 18 + 白色细边
    ui.painter().rect_filled(card, 18.0, Color32::from_rgba_unmultiplied(20, 22, 26, (209.0 * fade) as u8));
    ui.painter().rect_stroke(
        card,
        18.0,
        Stroke::new(1.0, Color32::from_rgba_unmultiplied(255, 255, 255, (70.0 * fade) as u8)),
        StrokeKind::Inside,
    );
    // 标题
    ui.painter().text(
        Pos2::new(card.min.x + 20.0, card.min.y + 30.0),
        Align2::LEFT_CENTER,
        title,
        Tokens::semibold(15.0),
        Color32::from_rgba_unmultiplied(245, 247, 250, (255.0 * fade) as u8),
    );
    // 正文（自动换行）
    let body_rect = Rect::from_min_size(Pos2::new(card.min.x + 20.0, card.min.y + 52.0), Vec2::new(width - 40.0, 70.0));
    ui.put(
        body_rect,
        egui::Label::new(egui::RichText::new(body).size(12.5).color(Color32::from_rgba_unmultiplied(196, 202, 212, (255.0 * fade) as u8))),
    );
    // 「知道了」
    let btn = Rect::from_min_size(Pos2::new(card.min.x + 20.0, card.max.y - 48.0), Vec2::new(width - 40.0, 32.0));
    if button(ui, &t, btn, "知道了", true) {
        close_notice(ui);
    }
    if ui.input(|i| i.key_pressed(egui::Key::Escape)) {
        close_notice(ui);
    }
}

fn panel_inner(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: Rect) {
    // 每次**重新打开**云端面板都拉一次列表（切进来就算），不依赖上一次的缓存：
    // 否则杀后台重进后列表是空的，用户得手动点「刷新」。
    {
        let now_panel = temp::<u8>(ui, PANEL);
        let prev_panel = get::<u8>(ui, LAST_PANEL).unwrap_or(0);
        if now_panel != prev_panel {
            set(ui, LAST_PANEL, now_panel);
            if now_panel == 4 {
                let token_now = token(ui);
                if !token_now.is_empty() {
                    set(ui, CLOUD_LOADING, true);
                    cloud::list_projects(token_now);
                }
            }
        }
    }
    // 有面板打开时，先铺一层全屏交互：它在这帧里最后注册，所以吃掉下面所有面板的点击，
    // 再配合下面清掉滚轮，做到「整屏不可穿透」。
    let open = temp::<u8>(ui, PANEL) != 0;
    if open {
        let screen = ui.interact(full, egui::Id::unique("ours-account-modal"), egui::Sense::click_and_drag());
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
                // 能登录进来就不再是封禁状态
                set(ui, BANNED, String::new());
                cloud::clear_banned();
                // 换了账号，头像缓存必须清掉，否则会显示上一个账号的图。
                ui.data_mut(|d| d.remove::<egui::TextureHandle>(Id::new("ours-account-avatar-tex")));
                app.ui.status = "已登录".to_string();
            }
            Event::LoginFailed(message) => {
                // 明确指出原因的错误一律弹窗，不再塞进按钮下面那行小字。
                show_notice(ui, "登录失败", &message);
                set(ui, MESSAGE, String::new());
            }
            Event::Profile(profile) => {
                set(ui, PROFILE, profile.clone());
                fill_fields(ui, &profile);
            }
            Event::SaveOk => {
                set(ui, MESSAGE, String::new());
                app.ui.status = "资料已保存".to_string();
            }
            Event::SaveFailed(message) | Event::Failed(message) => set(ui, MESSAGE, message),
            Event::Banned(reason) => {
                // 403 ACCOUNT_BANNED：清 token，把原因存起来（内存 + 文件），
                // 底部提示直接用 reason 原文，不再弹通用的那句。
                set(ui, TOKEN, String::new());
                set(ui, USERNAME, String::new());
                set(ui, PROFILE, Profile::default());
                set(ui, BANNED, reason.clone());
                set(ui, PANEL, 0_u8);
                set(ui, MESSAGE, String::new());
                set(ui, EDITING, false);
                cloud::save_banned(&reason);
                ui.data_mut(|d| d.remove::<egui::TextureHandle>(Id::new("ours-account-avatar-tex")));
                show_notice(ui, "账号已被停用", &reason);
            }
            Event::Projects(list) => {
                set(ui, PROJECTS, list);
                set(ui, CLOUD_LOADING, false);
            }
            Event::Uploading(busy) => set(ui, UPLOADING, busy),
            Event::Uploaded(name) => {
                app.ui.status = format!("已上传「{name}」");
                set(ui, MESSAGE, String::new());
                let token = token(ui);
                if !token.is_empty() {
                    cloud::list_projects(token);
                }
            }
            Event::Downloaded(path) => {
                app.ui.status = "已下载，正在打开…".to_string();
                if let Err(err) = app.session.execute("file.open", serde_json::json!({ "path": path })) {
                    app.ui.status = format!("打开失败: {err}");
                }
            }
            Event::Deleted(id) => {
                let mut list = get::<Vec<cloud::RemoteProject>>(ui, PROJECTS).unwrap_or_default();
                list.retain(|item| item.id != id);
                set(ui, PROJECTS, list);
                app.ui.status = "已删除".to_string();
            }
            Event::CloudFailed(message) => {
                set(ui, CLOUD_LOADING, false);
                set(ui, UPLOADING, false);
                set(ui, MESSAGE, message.clone());
                app.ui.status = message;
            }
            Event::SessionExpired => {
                set(ui, TOKEN, String::new());
                set(ui, USERNAME, String::new());
                set(ui, PROFILE, Profile::default());
                ui.data_mut(|d| d.remove::<egui::TextureHandle>(Id::new("ours-account-avatar-tex")));
                set(ui, PANEL, 0_u8);
                set(ui, MESSAGE, String::new());
                show_notice(ui, "账号异常", "登录已失效，请重新登录");
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
        // 上次被停用的原因也读回来：token 已经被清掉了，但登录页要能说明为什么。
        if let Some(reason) = cloud::load_banned() {
            set(ui, BANNED, reason);
        }
    }
    // 封禁要实时生效：登录状态下每 60 秒、以及每次切回前台，都拉一次 GET /me。
    // 被封（403 ACCOUNT_BANNED）或 token 失效（401）会清掉本地 token，
    // 界面立刻落回「登录」，不用杀 App 重进。
    {
        let token_now = token(ui);
        if !token_now.is_empty() {
            let now = ui.input(|i| i.time);
            let focused = ui.input(|i| i.viewport().focused.unwrap_or(false));
            let last = get::<f64>(ui, LAST_STATE).unwrap_or(0.0);
            let was = get::<bool>(ui, WAS_FOCUSED).unwrap_or(false);
            let due = now - last > 60.0 || (focused && !was) || last <= 0.0;
            if due {
                set(ui, LAST_STATE, now);
                cloud::check_state(token_now);
            }
            set(ui, WAS_FOCUSED, focused);
        } else {
            set(ui, WAS_FOCUSED, false);
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
        4 => cloud_panel(app, ui, full),
        _ => {}
    }
    // 弹窗必须最后画：登录面板、资料卡、云端面板都要被它压住。
    notice_panel(app, ui, full);
}

fn scrim(ui: &egui::Ui, full: Rect) {
    // 遮罩很淡（45）：玻璃卡片本身已经足够区分，太深会把后面的头像/控件压偏色。
    ui.painter().rect_filled(full, 0.0, Color32::from_black_alpha(45));
}

fn card(t: &Tokens, ui: &egui::Ui, full: Rect, width: f32, height: f32, title: &str) -> Rect {
    let w = width.min(full.width() - 24.0);
    let card = Rect::from_center_size(full.center(), Vec2::new(w, height));
    // 和「快捷」面板同一套材质：半透明深底 + 白色细边 + 14 圆角（不要不透明底板）。
    ui.painter().rect_filled(card, crate::panel_style::RADIUS, crate::panel_style::bg());
    ui.painter().rect_stroke(
        card,
        crate::panel_style::RADIUS,
        Stroke::new(1.0, crate::panel_style::border()),
        StrokeKind::Inside,
    );
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

/// 给别的面板（比如保存预设弹窗）复用同一套按钮样式。
pub fn button_pub(ui: &mut egui::Ui, t: &Tokens, r: Rect, label: &str, primary: bool) -> bool {
    button(ui, t, r, label, primary)
}

fn button(ui: &mut egui::Ui, t: &Tokens, r: Rect, label: &str, primary: bool) -> bool {
    // Id 里必须带上位置：三个生日 stepper 的 "-"/"+" 文字相同，只用 label 会撞成同一个
    // widget，表现就是「只有第一个能点，日期改不了」。
    let id = egui::Id::new(("ours-account-btn", label, r.min.x as i32, r.min.y as i32));
    let resp = ui.interact(r, id, egui::Sense::click());
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
    let eye_resp = ui.interact(eye, Id::unique("ours-account-eye"), egui::Sense::click());
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
    // 被封禁时不显示「注册」：这个账号状态只能由后台处理，注册也没用，
    // 而且原因直接显示出来（后端 reason 原文）。
    let banned = temp::<String>(ui, BANNED);
    let mut submit = None;
    if banned.is_empty() {
        if button(ui, &t, row(130.0, 132.0), "登录", true) {
            submit = Some(true);
        }
        if button(ui, &t, Rect::from_min_size(Pos2::new(left + 140.0, card.min.y + 130.0), Vec2::new(132.0, 30.0)), "注册", false) {
            submit = Some(false);
        }
    } else if button(ui, &t, row(130.0, width), "登录", true) {
        submit = Some(true);
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

    // 这里不再画橙色小字：错误统一由 notice_panel 弹窗呈现。
    let message = temp::<String>(ui, MESSAGE);
    if !message.is_empty() {
        ui.painter().text(
            Pos2::new(card.center().x, card.min.y + 178.0),
            Align2::CENTER_CENTER,
            message,
            Tokens::ui(11.5),
            t.text_dim,
        );
    }

    let later = Rect::from_min_size(Pos2::new(left, card.min.y + 196.0), Vec2::new(width, 28.0));
    let later_resp = ui.interact(later, Id::unique("ours-account-later"), egui::Sense::click());
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

/// `updated_at`（毫秒）→ `2026-11-18 20:31`。
fn fmt_cloud_time(ms: u64) -> String {
    chrono::DateTime::from_timestamp_millis(ms as i64)
        .map(|dt| dt.format("%Y-%m-%d %H:%M").to_string())
        .unwrap_or_else(|| "—".to_string())
}

/// 上传当前工程：先 `file.save` 确保磁盘是最新的，再读字节上传；没有路径就先「另存为」。
fn start_upload(app: &mut EffectcraftApp, ui: &mut egui::Ui) {
    let token = token(ui);
    if token.is_empty() {
        set(ui, PANEL, 1_u8);
        return;
    }
    let Some(path) = app.session.path.clone().filter(|p| !p.is_empty()) else {
        // 新工程还没落盘：先让用户选个保存位置，回调下一帧再上传。
        if let Some(spawn) = app.hooks.file_dialog_async.as_ref() {
            let dialog = crate::FileDialog::Save { default: "我的工程.ecproj".to_string(), ext: "ecproj".to_string(), project: true };
            let done: crate::DialogDone = Box::new(|paths| {
                if let Some(path) = paths.into_iter().next() {
                    if let Ok(mut slot) = pending_save().lock() {
                        *slot = Some(path);
                    }
                }
            });
            spawn(dialog, done);
            ui.ctx().request_repaint();
        } else {
            set(ui, MESSAGE, "先把工程保存一次再上传".to_string());
        }
        return;
    };
    // 存盘，保证上传的是最新的编辑。
    if let Err(err) = app.session.execute("file.save", serde_json::json!({ "path": path })) {
        set(ui, MESSAGE, format!("保存失败: {err}"));
        return;
    }
    match std::fs::read(&path) {
        Ok(bytes) => {
            let name = std::path::Path::new(&path)
                .file_stem()
                .map(|s| s.to_string_lossy().to_string())
                .filter(|s| !s.is_empty())
                .unwrap_or_else(|| "我的工程".to_string());
            let name = cloud_clean_name(&name);
            set(ui, UPLOADING, true);
            cloud::upload_project(token, name, bytes);
        }
        Err(err) => set(ui, MESSAGE, format!("读工程文件失败: {err}")),
    }
}


/// 工程名：把自动保存叠出来的「auto-save N」全去掉，避免每次上传都变成新工程。
fn cloud_clean_name(stem: &str) -> String {
    let mut out = String::new();
    for part in stem.split(" auto-save") {
        let part = part.trim();
        if part.is_empty() { continue; }
        if !out.is_empty() { out.push(' '); }
        out.push_str(part);
    }
    let trimmed = out.trim().trim_end_matches(|c: char| c.is_ascii_digit()).trim();
    if trimmed.is_empty() { "我的工程".to_string() } else { trimmed.to_string() }
}

/// 云端工程面板：未登录显示「登录后可用」，登录后是列表 + 上传/刷新。
fn cloud_panel(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: Rect) {
    let t = app.tokens;
    scrim(ui, full);
    let card = card(&t, ui, full, 380.0, 480.0, "云端工程");
    let left = card.min.x + 16.0;
    let width = card.width() - 32.0;
    let token = token(ui);

    if token.is_empty() {
        ui.painter().text(
            Pos2::new(card.center().x, card.min.y + 150.0),
            Align2::CENTER_CENTER,
            "登录后可用",
            Tokens::ui(14.0),
            t.text_dim,
        );
        let btn = Rect::from_min_size(Pos2::new(left, card.min.y + 190.0), Vec2::new(width, 32.0));
        if button(ui, &t, btn, "去登录", true) {
            set(ui, PANEL, 1_u8);
        }
    } else {
        let busy = get::<bool>(ui, UPLOADING).unwrap_or(false);
        let list = get::<Vec<cloud::RemoteProject>>(ui, PROJECTS).unwrap_or_default();
        // 顶部：上传 + 刷新
        let half = (width - 8.0) / 2.0;
        if busy {
            let r = Rect::from_min_size(Pos2::new(left, card.min.y + 48.0), Vec2::new(width, 30.0));
            ui.painter().rect_filled(r, 6.0, t.switch_well);
            ui.put(r.shrink(12.0), egui::Spinner::new());
            ui.painter().text(r.center() + Vec2::new(0.0, 0.0), Align2::CENTER_CENTER, "上传中…", Tokens::ui(12.0), t.text_dim);
        } else if button(ui, &t, Rect::from_min_size(Pos2::new(left, card.min.y + 48.0), Vec2::new(half, 30.0)), "上传当前工程", true) {
            start_upload(app, ui);
        }
        if !busy
            && button(ui, &t, Rect::from_min_size(Pos2::new(left + half + 8.0, card.min.y + 48.0), Vec2::new(half, 30.0)), "刷新", false)
        {
            set(ui, MESSAGE, String::new());
            cloud::list_projects(token.clone());
        }

        // 列表
        let list_top = card.min.y + 88.0;
        let row_h = crate::panel_style::ROW_H + 6.0;
        let visible = ((card.max.y - 96.0 - list_top) / row_h).max(1.0) as usize;
        let loading = get::<bool>(ui, CLOUD_LOADING).unwrap_or(false);
        if list.is_empty() {
            let (text, color) = if loading {
                ("加载中…", t.text_dim)
            } else {
                ("还没有云端工程，点「上传当前工程」试试", t.text_dim)
            };
            ui.painter().text(
                Pos2::new(card.center().x, list_top + 40.0),
                Align2::CENTER_CENTER,
                text,
                Tokens::ui(11.5),
                color,
            );
        }
        if loading {
            ui.put(Rect::from_center_size(Pos2::new(card.center().x, list_top + 74.0), Vec2::splat(18.0)), egui::Spinner::new());
        }
        let mut confirm = temp::<String>(ui, CONFIRM_DELETE);
        for (i, item) in list.iter().take(visible).enumerate() {
            let y = list_top + i as f32 * row_h;
            let r = Rect::from_min_size(Pos2::new(left, y), Vec2::new(width, row_h - 4.0));
            ui.painter().rect_filled(r, 6.0, t.field_bg);
            ui.painter().text(
                Pos2::new(r.min.x + 8.0, r.min.y + 15.0),
                Align2::LEFT_CENTER,
                item.name.clone(),
                Tokens::ui(12.5),
                t.text,
            );
            let meta = format!(
                "{}  ·  {}",
                crate::panels::project::fmt_size(item.size_bytes),
                fmt_cloud_time(item.updated_at)
            );
            ui.painter().text(Pos2::new(r.min.x + 8.0, r.min.y + 32.0), Align2::LEFT_CENTER, meta, Tokens::ui(10.5), t.text_faint);
            // 下载 / 删除
            let bw = 62.0;
            let dl = Rect::from_min_size(Pos2::new(r.max.x - bw * 2.0 - 12.0, r.min.y + 8.0), Vec2::new(bw, 24.0));
            let del = Rect::from_min_size(Pos2::new(r.max.x - bw - 6.0, r.min.y + 8.0), Vec2::new(bw, 24.0));
            if button(ui, &t, dl, "下载", false) {
                cloud::download_project(token.clone(), item.id.clone(), item.name.clone());
                set(ui, MESSAGE, "正在下载…".to_string());
            }
            let asking = confirm == item.id;
            let label = if asking { "确认删除" } else { "删除" };
            if button(ui, &t, del, label, asking) {
                if asking {
                    cloud::delete_project(token.clone(), item.id.clone());
                    confirm.clear();
                } else {
                    confirm = item.id.clone();
                }
            }
        }
        set(ui, CONFIRM_DELETE, confirm);

        // 「另存为」选好了位置：保存后立刻上传
        if let Some(target) = take_pending_save() {
            if let Err(err) = app.session.execute("file.saveAs", serde_json::json!({ "path": target.clone() })) {
                set(ui, MESSAGE, format!("保存失败: {err}"));
            } else {
                match std::fs::read(&target) {
                    Ok(bytes) => {
                        let name = std::path::Path::new(&target)
                            .file_stem()
                            .map(|s| s.to_string_lossy().to_string())
                            .unwrap_or_else(|| "我的工程".to_string());
                        let name = cloud_clean_name(&name);
                        set(ui, UPLOADING, true);
                        cloud::upload_project(token.clone(), name, bytes);
                    }
                    Err(err) => set(ui, MESSAGE, format!("读工程文件失败: {err}")),
                }
            }
        }
    }

    // 底部：关闭
    let close = Rect::from_min_size(Pos2::new(left, card.max.y - 44.0), Vec2::new(width, 30.0));
    if button(ui, &t, close, "关闭", false) {
        set(ui, PANEL, 0_u8);
        set(ui, MESSAGE, String::new());
        set(ui, CONFIRM_DELETE, String::new());
    }
    let message = temp::<String>(ui, MESSAGE);
    if !message.is_empty() {
        ui.painter().text(
            Pos2::new(card.center().x, card.max.y - 58.0),
            Align2::CENTER_CENTER,
            message,
            Tokens::ui(11.0),
            t.warning,
        );
    }
    if ui.input(|i| i.key_pressed(egui::Key::Escape)) {
        set(ui, PANEL, 0_u8);
        set(ui, MESSAGE, String::new());
    }
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
    let drag = ui.interact(image_rect, Id::unique("ours-account-crop-drag"), egui::Sense::drag());
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
    let avatar_resp = ui.interact(avatar_rect, Id::unique("ours-account-avatar-hit"), egui::Sense::click());
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
        // 生日：直接一个输入框，点了就能用键盘敲（2004-12-31）。下面一行仍给
        // 年/月/日 步进器，且末尾会循环（12 → 1、31 → 1），两种方式都能用。
        field(ui, &t, row(200.0), BIRTH, "生日 2004-12-31", false);
        let (mut year, mut month, mut day) = parse_birthday(&temp::<String>(ui, BIRTH));
        let by = card.min.y + 236.0;
        let unit_w = (width - gap * 2.0) / 3.0;
        let mut birth_changed = false;
        birth_changed |= stepper(ui, &t, Rect::from_min_size(Pos2::new(left, by), Vec2::new(unit_w, 26.0)), &mut year, 1900, 2030);
        birth_changed |= stepper(ui, &t, Rect::from_min_size(Pos2::new(left + unit_w + gap, by), Vec2::new(unit_w, 26.0)), &mut month, 1, 12);
        birth_changed |= stepper(ui, &t, Rect::from_min_size(Pos2::new(left + (unit_w + gap) * 2.0, by), Vec2::new(unit_w, 26.0)), &mut day, 1, 31);
        if birth_changed {
            set(ui, BIRTH, format!("{year:04}-{month:02}-{day:02}"));
        }
        // 个性签名：多行
        let mut sign = temp::<String>(ui, SIGN);
        let rect = Rect::from_min_size(Pos2::new(left, card.min.y + 274.0), Vec2::new(width, 62.0));
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
            let y = card.min.y + 130.0 + i as f32 * 38.0;
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
    let btn_y = card.min.y + 350.0;
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
