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
    let resp = if logged_in(ui) {
        let profile = temp::<Profile>(ui, PROFILE);
        let r = Rect::from_center_size(Pos2::new(x + 13.0, cy), Vec2::splat(26.0));
        let resp = ui.interact(r, Id::unique("ours-account-slot"), Sense::click());
        // 没有头像图片时用昵称首字 + 主题色底（用户定的占位方案）。
        p.circle_filled(r.center(), 13.0, if resp.hovered() { t.accent_hover } else { t.accent });
        p.text(r.center(), Align2::CENTER_CENTER, initial(&profile), Tokens::ui(13.0), Color32::from_rgb(16, 18, 22));
        app.auto.add("account.slot", r, "账号");
        resp
    } else {
        let r = Rect::from_min_size(Pos2::new(x, cy - 13.0), Vec2::new(44.0, 26.0));
        let resp = ui.interact(r, Id::unique("ours-account-slot"), Sense::click());
        p.rect_filled(r, 4.0, if resp.hovered() { t.hover } else { t.switch_well });
        p.text(r.center(), Align2::CENTER_CENTER, "登录", Tokens::ui(12.0), t.text);
        app.auto.add("account.slot", r, "登录");
        resp
    };
    let width = if logged_in(ui) { 28.0 } else { 48.0 };
    if resp.clicked() {
        set(ui, PANEL, if logged_in(ui) { 2_u8 } else { 1 });
        // 打开资料卡时先把输入框填成当前资料。
        if logged_in(ui) {
            let profile = temp::<Profile>(ui, PROFILE);
            fill_fields(ui, &profile);
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
            Event::LoggedIn { token: fresh, profile } => {
                set(ui, TOKEN, fresh);
                set(ui, PROFILE, profile.clone());
                fill_fields(ui, &profile);
                set(ui, PANEL, 0_u8);
                set(ui, MESSAGE, String::new());
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
                set(ui, PROFILE, Profile::default());
                set(ui, PANEL, 0_u8);
                set(ui, MESSAGE, String::new());
                app.ui.status = "登录已过期，请重新登录".to_string();
            }
        }
    }
    // 启动后第一次：有 token 就静默拉一次资料（失败也只是回到未登录）。
    if !get::<bool>(ui, FETCHED).unwrap_or(false) {
        set(ui, FETCHED, true);
        let stored = cloud::load_token().unwrap_or_default();
        if !stored.is_empty() {
            set(ui, TOKEN, stored.clone());
            cloud::fetch_me(stored);
        }
    }
    match temp::<u8>(ui, PANEL) {
        1 => auth_panel(app, ui, full),
        2 => profile_panel(app, ui, full),
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
    let resp = ui.interact(r, egui::Id::new(("ours-account-btn", label)), Sense::click());
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

fn profile_panel(app: &mut EffectcraftApp, ui: &mut egui::Ui, full: Rect) {
    let t = app.tokens;
    scrim(ui, full);
    let card = card(&t, ui, full, 320.0, 336.0, "我的资料");
    let left = card.min.x + 18.0;
    let width = card.width() - 36.0;
    let row = |y: f32| Rect::from_min_size(Pos2::new(left, card.min.y + y), Vec2::new(width, 30.0));

    // 头像：昵称首字 + 主题色（有本地图片的版本留到下一期）。
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

    field(ui, &t, row(122.0), NICK, "昵称", false);
    field(ui, &t, row(160.0), GENDER, "性别", false);
    field(ui, &t, row(198.0), BIRTH, "生日（1990-01-02）", false);
    field(ui, &t, row(236.0), SIGN, "个性签名", false);

    if button(ui, &t, Rect::from_min_size(Pos2::new(left, card.min.y + 278.0), Vec2::new(132.0, 30.0)), "保存", true) {
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
    }
    if button(ui, &t, Rect::from_min_size(Pos2::new(left + 140.0, card.min.y + 278.0), Vec2::new(132.0, 30.0)), "退出登录", false) {
        cloud::logout();
        set(ui, TOKEN, String::new());
        set(ui, PROFILE, Profile::default());
        set(ui, PANEL, 0_u8);
        app.ui.status = "已退出登录".to_string();
    }

    let message = temp::<String>(ui, MESSAGE);
    if !message.is_empty() {
        ui.painter().text(
            Pos2::new(card.center().x, card.min.y + 316.0),
            Align2::CENTER_CENTER,
            message,
            Tokens::ui(11.0),
            t.warning,
        );
    }
    let esc = ui.input(|i| i.key_pressed(egui::Key::Escape));
    if esc {
        set(ui, PANEL, 0_u8);
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
