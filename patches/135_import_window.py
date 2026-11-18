#!/usr/bin/env python3
"""导入面板（最终版）：只讲工程与素材，插件走它自己的入口。

面板上五个可点条目，每个都按扩展名分发到对应命令：

| 条目 | 扩展名 | 命令 |
|---|---|---|
| After Effects 工程 | `.aep` / `.aepx` | `file.importAep` |
| EffectCraft 工程 | `.ecproj` / `.ecprojx` | `file.importProject` |
| Premiere / AM / FCP XML | `.xml .fcpxml .otio .edl .aaf .omf` | `file.importTimeline` |
| 媒体文件 | mp4/mov/png/jpg/wav/mp3 … | `file.import` |
| AE 效果预设 | `.ffx` | 自己的解析器（见下） |

`.ffx` 不走命令：读 XML 里每个效果节点的 `name` / `matchName`，用
`effectcraft_effects::lookup`（id → 显示名大小写不敏感 → 别名表）去匹配，匹配上的用
`effect.apply` 套到当前选中图层，最后用玻璃弹窗汇总「已应用 X 个 / 缺少哪些」。
参数不设置：`.ffx` 只给参数显示名，拿不到效果内部的参数 id 路径，保持默认值。

灰字（不可点）：剪映 / CapCut 工程、NodeVideo 工程 —— 这两种上游确实没有解析器。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_IMPORT_WINDOW_V1"

MENU_OLD = '''            [("newComp", "New Composition…", "comp.new"), ("newFolder", "New Folder", "project.newFolder"), ("import", "Import File…", "file.import")]
'''
MENU_NEW = '''            [
                ("newComp", "New Composition…", "comp.new"),
                ("newFolder", "New Folder", "project.newFolder"),
                ("import", "Import File…", "file.import"),
                // EFFECTCRAFT_OURS_IMPORT_WINDOW_V1 — 插件与工程格式都从这里进
                ("importAll", "导入工程与素材…", "ours.import"),
            ]
'''

LOOP_OLD = '''    for (id, params) in actions {
        if let Err(e) = crate::menus::invoke(app, &ctx, &id, params) {
            app.ui.status = e;
        }
'''
LOOP_NEW = '''    for (id, params) in actions {
        if id == "ours.import" {
            ctx.data_mut(|d| d.insert_temp(egui::Id::new("ours-import-open"), true));
            continue;
        }
        if let Err(e) = crate::menus::invoke(app, &ctx, &id, params) {
            app.ui.status = e;
        }
'''

CALL = '''    import_window(app, ui.ctx());
'''

WINDOW = r'''

/// 文件对话框选好的路径（回调可能来自任意线程）→ 下一帧再分发。
fn pending_import() -> &'static std::sync::Mutex<Option<String>> {
    static PENDING: std::sync::OnceLock<std::sync::Mutex<Option<String>>> = std::sync::OnceLock::new();
    PENDING.get_or_init(|| std::sync::Mutex::new(None))
}

/// 面板上可点的五个条目。
#[derive(Clone, Copy, PartialEq)]
enum ImportKind {
    Aep,
    Ecproj,
    Timeline,
    Media,
    Ffx,
    /// Sapphire .gp 预设（237 的 apply_gp 解析它）
    Gp,
    /// NodeVideo 工程包：.nv 或 zip
    Nv,
}

impl ImportKind {
    fn exts(self) -> Vec<&'static str> {
        match self {
            ImportKind::Aep => vec!["aep", "aepx"],
            ImportKind::Ecproj => vec!["ecproj", "ecprojx"],
            ImportKind::Timeline => vec!["xml", "fcpxml", "otio", "edl", "aaf", "omf"],
            ImportKind::Ffx => vec!["ffx"],
            ImportKind::Gp => vec!["gp"],
            ImportKind::Nv => vec!["nv", "zip"],
            ImportKind::Media => vec![
                "mp4", "mov", "mxf", "mkv", "webm", "png", "jpg", "jpeg", "webp", "tif", "tiff", "wav", "mp3", "flac",
            ],
        }
    }

    fn command(self) -> &'static str {
        match self {
            ImportKind::Aep => "file.importAep",
            ImportKind::Ecproj => "file.importProject",
            ImportKind::Timeline => "file.importTimeline",
            ImportKind::Ffx => "",
            ImportKind::Gp => "",
            ImportKind::Nv => "file.import",
            ImportKind::Media => "file.import",
        }
    }
}

/// 看扩展名推断属于哪一类（底部「导入文件…」不预设类别时用）。
fn kind_for_ext(ext: &str) -> ImportKind {
    let lower = ext.to_ascii_lowercase();
    if ["aep", "aepx"].contains(&lower.as_str()) {
        ImportKind::Aep
    } else if ["ecproj", "ecprojx"].contains(&lower.as_str()) {
        ImportKind::Ecproj
    } else if ["xml", "fcpxml", "otio", "edl", "aaf", "omf"].contains(&lower.as_str()) {
        ImportKind::Timeline
    } else if lower == "ffx" {
        ImportKind::Ffx
    } else if lower == "gp" {
        ImportKind::Gp
    } else if lower == "nv" || lower == "zip" {
        ImportKind::Nv
    } else {
        ImportKind::Media
    }
}

/// 记下这次点的是哪个条目（`.ffx` 不走命令，要自己解析）。
fn pending_kind() -> &'static std::sync::Mutex<Option<ImportKind>> {
    static KIND: std::sync::OnceLock<std::sync::Mutex<Option<ImportKind>>> = std::sync::OnceLock::new();
    KIND.get_or_init(|| std::sync::Mutex::new(None))
}

fn pick_for(app: &mut EffectcraftApp, kind: ImportKind) {
    let Some(spawn) = app.hooks.file_dialog_async.as_ref() else {
        app.ui.status = "这个平台没有文件选择器".to_string();
        return;
    };
    let dialog = crate::FileDialog::Open {
        exts: kind.exts().iter().map(|e| e.to_string()).collect(),
        many: false,
    };
    let done: crate::DialogDone = Box::new(|paths| {
        if let Some(path) = paths.into_iter().next() {
            if let Ok(mut slot) = pending_import().lock() {
                *slot = Some(path);
            }
        }
    });
    if let Ok(mut slot) = pending_kind().lock() {
        *slot = Some(kind);
    }
    spawn(dialog, done);
}

/// 底部主按钮：所有扩展名都列出来，选完再按扩展名推断类别。
fn pick_any(app: &mut EffectcraftApp) {
    let Some(spawn) = app.hooks.file_dialog_async.as_ref() else {
        app.ui.status = "这个平台没有文件选择器".to_string();
        return;
    };
    let all = [
        ImportKind::Aep,
        ImportKind::Ecproj,
        ImportKind::Timeline,
        ImportKind::Media,
        ImportKind::Ffx,
        ImportKind::Gp,
        ImportKind::Nv,
    ];
    let mut exts: Vec<String> = Vec::new();
    for kind in all {
        for ext in kind.exts() {
            let ext = ext.to_string();
            if !exts.contains(&ext) {
                exts.push(ext);
            }
        }
    }
    let dialog = crate::FileDialog::Open { exts, many: false };
    let done: crate::DialogDone = Box::new(|paths| {
        if let Some(path) = paths.into_iter().next() {
            if let Ok(mut slot) = pending_import().lock() {
                *slot = Some(path);
            }
        }
    });
    if let Ok(mut slot) = pending_kind().lock() {
        *slot = None;
    }
    spawn(dialog, done);
}

/// 从标签里取一个属性值（大小写不敏感找 `key="`）。
fn ffx_attr(head: &str, key: &str) -> String {
    let lower = head.to_ascii_lowercase();
    let needle = format!("{}=\"", key.to_ascii_lowercase());
    let Some(at) = lower.find(&needle) else {
        return String::new();
    };
    head[at + needle.len()..].chars().take_while(|c| *c != '"').collect()
}

/// `.ffx` 里每个效果节点：`<Effect name="Glow" matchName="ADBE Glo2">`（也见过 `<Filter …>`）。
fn parse_ffx_effects(xml: &str) -> Vec<(String, String)> {
    let mut out: Vec<(String, String)> = Vec::new();
    for raw in xml.split('<').skip(1) {
        let head: String = raw.chars().take_while(|c| *c != '>').collect();
        let lower = head.to_ascii_lowercase();
        if !(lower.starts_with("effect") || lower.starts_with("filter")) {
            continue;
        }
        let mut name = ffx_attr(&head, "name");
        if name.is_empty() {
            name = ffx_attr(&head, "displayname");
        }
        let mut match_name = ffx_attr(&head, "matchname");
        if match_name.is_empty() {
            match_name = ffx_attr(&head, "match_name");
        }
        if name.is_empty() && match_name.is_empty() {
            continue;
        }
        out.push((name, match_name));
    }
    out
}

/// 由效果名 / matchName 生成候选名：原名 → matchName → 去掉 `ADBE ` 前缀 → 去掉尾部数字。
fn effect_candidates(name: &str, match_name: &str) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    fn push(out: &mut Vec<String>, value: &str) {
        let trimmed = value.trim();
        if !trimmed.is_empty() && !out.iter().any(|x| x == trimmed) {
            out.push(trimmed.to_string());
        }
    }
    push(&mut out, name);
    push(&mut out, match_name);
    for candidate in [name, match_name] {
        if candidate.is_empty() {
            continue;
        }
        let tail = candidate
            .strip_prefix("ADBE ")
            .or_else(|| candidate.strip_prefix("ADBE"))
            .map(str::trim)
            .unwrap_or(candidate);
        if tail != candidate {
            push(&mut out, tail);
        }
        let letters: String = tail.chars().take_while(|c| !c.is_ascii_digit()).collect();
        if letters.len() >= 4 && letters.len() < tail.len() {
            push(&mut out, &letters);
        }
    }
    out
}

/// 依次拿候选名调 `effect.apply`。
/// 返回 `Ok(())` 表示套上了；`Err(true)` 表示这些名字都不是已知效果；`Err(false)` 是别的错
/// （多半是没选中图层）—— 后者要如实告诉用户，不能算成「缺少效果」。
fn try_apply_effect(
    app: &mut EffectcraftApp,
    ctx: &egui::Context,
    name: &str,
    match_name: &str,
) -> Result<(), bool> {
    let candidates = effect_candidates(name, match_name);
    let mut unknown = true;
    for candidate in candidates {
        let params = serde_json::json!({ "effect": candidate });
        match crate::menus::invoke(app, ctx, "effect.apply", params) {
            Ok(_) => return Ok(()),
            Err(e) => {
                // engine 对不认识的名字报 `unknown effect`；其它错误（没有图层）不是缺效果。
                if !e.contains("unknown effect") {
                    app.ui.status = format!("应用效果失败：{e}");
                    unknown = false;
                    break;
                }
            }
        }
    }
    Err(unknown)
}

fn apply_ffx(app: &mut EffectcraftApp, ctx: &egui::Context, path: &str) {
    let Some(xml) = std::fs::read(path)
        .ok()
        .map(|bytes| String::from_utf8_lossy(&bytes).trim_start_matches('\u{feff}').to_string())
        .filter(|text| text.trim_start().starts_with('<'))
    else {
        app.ui.status = "这个 .ffx 读不了".to_string();
        return;
    };
    let effects = parse_ffx_effects(&xml);
    if effects.is_empty() {
        app.ui.status = "这个 .ffx 里没有效果".to_string();
        return;
    }
    let mut applied = 0usize;
    let mut missing: Vec<String> = Vec::new();
    for (name, match_name) in &effects {
        match try_apply_effect(app, ctx, name, match_name) {
            Ok(()) => applied += 1,
            Err(true) => missing.push(if name.is_empty() { match_name.clone() } else { name.clone() }),
            // Err(false)：已经写过状态行（比如没选中图层），不重复计数。
            Err(false) => {}
        }
    }
    let body = if applied == 0 && !missing.is_empty() {
        "此预设用到的效果本软件都没有".to_string()
    } else if missing.is_empty() {
        format!("已应用 {applied} 个效果（参数为默认值，可在效果面板里调）")
    } else {
        let list: Vec<String> = missing.iter().take(6).cloned().collect();
        let more = missing.len().saturating_sub(list.len());
        let tail = if more > 0 { format!(" 等 {more} 个") } else { String::new() };
        format!(
            "已应用 {applied} 个效果，缺少 {} 个：{}{}",
            missing.len(),
            list.join("、"),
            tail
        )
    };
    crate::account_ui::show_notice_ctx(ctx, "AE 效果预设", &body);
}

fn dispatch_import(app: &mut EffectcraftApp, ctx: &egui::Context) {
    let path = pending_import().lock().ok().and_then(|mut slot| slot.take());
    let kind = pending_kind().lock().ok().and_then(|mut slot| slot.take());
    let Some(path) = path else { return };
    let kind = kind.unwrap_or_else(|| {
        let ext = std::path::Path::new(&path)
            .extension()
            .map(|e| e.to_string_lossy().to_string())
            .unwrap_or_default();
        kind_for_ext(&ext)
    });
    if kind == ImportKind::Ffx {
        apply_ffx(app, ctx, &path);
        return;
    }
    // .gp 走 237 的 apply_gp（参数名/数值都能还原）
    if kind == ImportKind::Gp {
        match crate::menus::invoke(app, ctx, "ours.applyPreset", serde_json::json!({ "path": path })) {
            Ok(_) => app.ui.status = "已套用 .gp 预设".to_string(),
            Err(e) => app.ui.status = format!("套用失败：{e}"),
        }
        return;
    }
    let params = if matches!(kind, ImportKind::Media | ImportKind::Nv) {
        serde_json::json!({ "paths": [path] })
    } else {
        serde_json::json!({ "path": path })
    };
    if let Err(e) = crate::menus::invoke(app, ctx, kind.command(), params) {
        app.ui.status = format!("导入失败：{e}");
    }
}

/// 分组小标题：12px、灰 60%、字距 +0.5，上方留 14px。
fn import_section(ui: &mut egui::Ui, t: &Tokens, title: &str) {
    ui.add_space(6.0);
    let spaced: String = title.chars().flat_map(|c| [c, '\u{2009}']).collect();
    ui.label(egui::RichText::new(spaced.trim_end()).size(10.0).color(t.text_dim));
    ui.add_space(6.0);
}

fn import_tint(color: Color32, alpha: u8) -> Color32 {
    Color32::from_rgba_unmultiplied(color.r(), color.g(), color.b(), alpha)
}

/// 一行「像按钮」的条目：高 52、圆角 10、surface 底；hover 主题色 8%、按下 14%。
#[allow(clippy::too_many_arguments)]
fn import_row(
    ui: &mut egui::Ui,
    app: &mut EffectcraftApp,
    t: &Tokens,
    kind: ImportKind,
    icon: &str,
    title: &str,
    sub: &str,
) {
    let width = ui.available_width();
    let (rect, resp) = ui.allocate_exact_size(vec2(width, 40.0), egui::Sense::click());
    let accent = t.accent;
    let fill = if resp.is_pointer_button_down_on() {
        import_tint(accent, 52)
    } else if resp.hovered() {
        import_tint(accent, 34)
    } else {
        t.field_bg
    };
    let p = ui.painter();
    p.rect_filled(rect, 10.0, fill);
    if resp.hovered() {
        ui.ctx().set_cursor_icon(egui::CursorIcon::PointingHand);
    }
    // 18×18 图标方块（随 196 宽等比缩小），主题色 25% 底
    let icon_rect = egui::Rect::from_center_size(egui::pos2(rect.min.x + 18.0, rect.center().y), vec2(20.0, 20.0));
    // 图标块压暗，字母本身用荧光主题色（原来是暗绿/灰，和主题色不一致）
    p.rect_filled(icon_rect, 8.0, import_tint(accent, 26));
    p.text(icon_rect.center(), egui::Align2::CENTER_CENTER, icon, Tokens::ui(10.0), accent);
    p.text(
        egui::pos2(icon_rect.max.x + 6.0, rect.center().y - 7.0),
        egui::Align2::LEFT_CENTER,
        title,
        Tokens::ui(11.0),
        t.text,
    );
    p.text(
        egui::pos2(icon_rect.max.x + 8.0, rect.center().y + 7.0),
        egui::Align2::LEFT_CENTER,
        sub,
        Tokens::ui(8.5),
        t.text_dim,
    );
    if resp.clicked() {
        pick_for(app, kind);
    }
}

/// 暂不支持的行：尺寸、底色、图标底**和上面的行完全一样**，
/// 只有末尾的「敬请期待」用灰字（不再整行压成 40% 透明）。
fn import_disabled_row(ui: &mut egui::Ui, t: &Tokens, title: &str) {
    let width = ui.available_width();
    let (rect, _) = ui.allocate_exact_size(vec2(width, 40.0), egui::Sense::hover());
    let p = ui.painter();
    p.rect_filled(rect, 10.0, t.field_bg);
    let icon_rect = egui::Rect::from_center_size(egui::pos2(rect.min.x + 18.0, rect.center().y), vec2(20.0, 20.0));
    p.rect_filled(icon_rect, 8.0, import_tint(t.accent, 26));
    p.text(
        egui::pos2(icon_rect.max.x + 8.0, rect.center().y),
        egui::Align2::LEFT_CENTER,
        title,
        Tokens::ui(11.0),
        t.text,
    );
    // 只有末尾这三个字是灰的
    p.text(
        egui::pos2(rect.max.x - 14.0, rect.center().y),
        egui::Align2::RIGHT_CENTER,
        "敬请期待",
        Tokens::ui(9.5),
        t.text_faint,
    );
}

/// 导入面板：工程三类 + 素材两类；插件不在这里。
fn import_window(app: &mut EffectcraftApp, ctx: &egui::Context) {
    let open_id = egui::Id::new("ours-import-open");
    let mut open = ctx.data(|d| d.get_temp::<bool>(open_id).unwrap_or(false));
    if !open {
        return;
    }
    dispatch_import(app, ctx);
    let t = app.tokens;
    let style = ctx.style_of(ctx.theme());
    // 和「快捷键」面板**完全相同**的材质：rgba(12,12,14,130) 半透明底 + 白色 90 细边 + 圆角 14。
    // 统一走「快捷键」面板的基准（panel_style.rs），不在各处写死。
    let frame = crate::panel_style::frame(&style);
    egui::Window::new("导入")
        // 不要 egui 自带的标题栏：它的高度由 style 决定、压不下去，用户圈出来的那条空白就是它。
        .title_bar(false)
        .open(&mut open)
        .frame(frame)
        .collapsible(false)
        .resizable(false)
        .default_width(340.0)
        // default_width 只是初始值：副标题太长会把窗口撑开，这里给硬上下限。
        .max_width(340.0)
        .min_width(340.0)
        .show(ctx, |ui| {
            ui.spacing_mut().item_spacing.y = 4.0;
            // 自绘紧凑标题栏：高 28，标题居中，右侧 ✕ 关闭。
            let (bar, _) = ui.allocate_exact_size(
                egui::vec2(ui.available_width(), 28.0),
                egui::Sense::hover(),
            );
            ui.painter().text(
                bar.center(),
                egui::Align2::CENTER_CENTER,
                "导入",
                Tokens::ui(12.5),
                t.text,
            );
            let close = egui::Rect::from_center_size(
                egui::pos2(bar.max.x - 18.0, bar.center().y),
                egui::vec2(24.0, 24.0),
            );
            let close_resp = ui.interact(close, egui::Id::unique("ours-import-close"), egui::Sense::click());
            ui.painter().text(
                close.center(),
                egui::Align2::CENTER_CENTER,
                "\u{00d7}",
                Tokens::ui(14.0),
                t.text_dim,
            );
            if close_resp.clicked() {
                ui.ctx().data_mut(|d| d.insert_temp(open_id, false));
            }
            import_section(ui, &t, "工程");
            import_row(ui, app, &t, ImportKind::Aep, "A", "After Effects 工程", ".aep / .aepx · 合成、图层、关键帧可还原，效果缺失会先提示");
            import_row(ui, app, &t, ImportKind::Ecproj, "E", "EffectCraft 工程", ".ecproj / .ecprojx · 整个工程原样打开");
            import_row(ui, app, &t, ImportKind::Timeline, "T", "Premiere / AM / FCP XML", ".xml .fcpxml .otio .edl .aaf .omf · 重建时间线");
            // NodeVideo 已经能导入，所以放在**工程**组里；剪映暂不支持，也留在同一组，只标灰。
            import_row(ui, app, &t, ImportKind::Nv, "N", "NodeVideo 工程", ".nv / .zip · 重建时间线");
            import_disabled_row(ui, &t, "剪映 / CapCut 工程");
            import_section(ui, &t, "素材");
            import_row(ui, app, &t, ImportKind::Media, "M", "媒体文件", "mp4 / mov / png / jpg / wav / mp3 · 作为素材导入");
            import_row(ui, app, &t, ImportKind::Ffx, "F", "AE 效果预设", ".ffx · 效果套到选中图层，参数用默认值");
            ui.add_space(8.0);
            // 主按钮：固定 44 高，居中的胶囊（宽度 = 文字 + 48），圆角 12
            let accent = t.accent;
            let button = egui::Button::new(
                egui::RichText::new("导入文件…")
                    .size(14.0)
                    .color(Color32::from_rgb(8, 10, 12)),
            )
            .fill(accent)
            .corner_radius(crate::panel_style::RADIUS);
            let row = ui.available_width();
            // 「导入文件…」5 个字 @14px ≈ 70px，再 +48 的内边距 = 118；上限不超过行宽。
            let mask = 110.0_f32;
            let (slot, _) = ui.allocate_exact_size(vec2(row, crate::panel_style::BUTTON_H), egui::Sense::hover());
            let target = egui::Rect::from_center_size(slot.center(), vec2(row, 36.0));
            if ui.put(target, button).clicked() {
                pick_any(app);
            }
            ui.add_space(4.0);
            ui.label(
                egui::RichText::new("支持以上全部格式")
                    .size(8.0)
                    .color(t.text_faint),
            );
            ui.label(
                egui::RichText::new(".ffx 只应用效果名，参数用默认值")
                    .size(8.0)
                    .color(t.text_faint),
            );
        });
    ctx.data_mut(|d| d.insert_temp(open_id, open));
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/project.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("import window already installed")
        return
    for old, new in ((MENU_OLD, MENU_NEW), (LOOP_OLD, LOOP_NEW)):
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old[:50]!r}: expected 1, found {src.count(old)}")
        src = src.replace(old, new, 1)
    # Draw the window once per frame from the panel.
    anchor = "    marquee_select(app, &ctx, &lp, list, &empty, &rows);\n"
    if src.count(anchor) != 1:
        raise SystemExit(f"call anchor: {src.count(anchor)}")
    src = src.replace(anchor, CALL + anchor, 1)
    src += WINDOW
    path.write_text(src, encoding="utf-8")
    print("import window (projects + media, real .ffx) installed")


if __name__ == "__main__":
    main()
