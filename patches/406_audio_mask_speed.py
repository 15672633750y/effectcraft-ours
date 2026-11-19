#!/usr/bin/env python3
"""底部工具条再加三个**真功能**：音频 / 蒙版 / 变速。

* 音频：新增 `ImportKind::Audio`（mp3/wav/m4a/aac/flac/ogg），走现有文件选择器，
        选完交给 `file.import`；就是"跳到音乐文件"的那个界面。
* 蒙版：`mask.new`，按当前合成尺寸给一个矩形蒙版（四角顶点）。
* 变速：`layer.enableTimeRemap`，给选中图层打开时间重映射（=变速的前提）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_AUDIO_MASK_SPEED_V1"

# ---- project.rs：新增 Audio 类别
EXTS_OLD = '''            ImportKind::Font => vec!["ttf", "otf", "ttc"],'''
EXTS_NEW = '''            ImportKind::Font => vec!["ttf", "otf", "ttc"],
            // EFFECTCRAFT_OURS_AUDIO_MASK_SPEED_V1 — 音频专用选择
            ImportKind::Audio => vec!["mp3", "wav", "m4a", "aac", "flac", "ogg", "opus"],'''

CMD_OLD = '''            ImportKind::Font => "",
            ImportKind::Media => "file.import",'''
CMD_NEW = '''            ImportKind::Font => "",
            ImportKind::Audio => "file.import",
            ImportKind::Media => "file.import",'''

VARIANT_OLD = '''    /// 字体文件：注册后文字图层能选到
    Font,
}'''
VARIANT_NEW = '''    /// 字体文件：注册后文字图层能选到
    Font,
    /// 音频文件：底部「音频」按钮专用
    Audio,
}'''

FN_OLD = '''fn pick_for(app: &mut EffectcraftApp, kind: ImportKind) {'''
FN_NEW = '''/// 底部工具条的「音频」按钮：只列音频扩展名。
pub(crate) fn pick_audio(app: &mut EffectcraftApp) {
    pick_for(app, ImportKind::Audio);
}

fn pick_for(app: &mut EffectcraftApp, kind: ImportKind) {'''

# ---- frame.rs：三个新按钮
ITEMS_OLD = '''                        _ => vec![
                            ("\\u{ff0b}", "导入", 0),
                            ("T", "文字", 1),
                            ("\\u{25c7}", "形状", 2),
                            ("\\u{2605}", "预设", 3),
                            ("\\u{25b6}", "播放", 4),
                            ("\\u{2191}", "导出", 8),
                        ],'''
ITEMS_NEW = '''                        _ => vec![
                            ("\\u{ff0b}", "导入", 0),
                            ("T", "文字", 1),
                            ("\\u{25c7}", "形状", 2),
                            ("\\u{2605}", "预设", 3),
                            ("\\u{25b6}", "播放", 4),
                            ("\\u{2191}", "导出", 8),
                            ("\\u{266b}", "音频", 9),
                            ("\\u{25d1}", "蒙版", 15),
                            ("\\u{23e9}", "变速", 16),
                        ],'''

CAPCUT_OLD = '''                        "capcut" => vec![
                            ("\\u{ff0b}", "视频", 0),
                            ("T", "文字", 1),
                            ("\\u{25c7}", "形状", 2),
                            ("\\u{2605}", "效果", 3),
                            ("\\u{25b6}", "播放", 4),
                            ("\\u{2191}", "导出", 8),
                        ],'''
CAPCUT_NEW = '''                        "capcut" => vec![
                            ("\\u{ff0b}", "视频", 0),
                            ("T", "文字", 1),
                            ("\\u{25c7}", "形状", 2),
                            ("\\u{2605}", "效果", 3),
                            ("\\u{25b6}", "播放", 4),
                            ("\\u{2191}", "导出", 8),
                            ("\\u{266b}", "音频", 9),
                            ("\\u{25d1}", "蒙版", 15),
                            ("\\u{23e9}", "变速", 16),
                        ],'''

KS_OLD = '''                        "kuaishou" => vec![
                            ("\\u{ff0b}", "导入", 0),
                            ("T", "字幕", 1),
                            ("\\u{25c7}", "形状", 2),
                            ("\\u{2605}", "特效", 3),
                            ("\\u{25b6}", "播放", 4),
                            ("\\u{2191}", "导出", 8),
                        ],'''
KS_NEW = '''                        "kuaishou" => vec![
                            ("\\u{ff0b}", "导入", 0),
                            ("T", "字幕", 1),
                            ("\\u{25c7}", "形状", 2),
                            ("\\u{2605}", "特效", 3),
                            ("\\u{25b6}", "播放", 4),
                            ("\\u{2191}", "导出", 8),
                            ("\\u{266b}", "音频", 9),
                            ("\\u{25d1}", "蒙版", 15),
                            ("\\u{23e9}", "变速", 16),
                        ],'''

MATCH_OLD = '''                Some(13) => {
                    let id = egui::Id::new("ours-export-open");
                    ui.ctx().data_mut(|d| d.insert_temp(id, true));
                }
                _ => {}'''

MATCH_NEW = '''                Some(13) => {
                    let id = egui::Id::new("ours-export-open");
                    ui.ctx().data_mut(|d| d.insert_temp(id, true));
                }
                Some(9) => {
                    crate::panels::project::pick_audio(self);
                }
                Some(15) => {
                    let size = self
                        .session
                        .active_comp()
                        .map(|c| (c.width as f64, c.height as f64));
                    if let Some((w, h)) = size {
                        let verts = vec![
                            vec![0.0, 0.0],
                            vec![w, 0.0],
                            vec![w, h],
                            vec![0.0, h],
                        ];
                        let r = crate::menus::invoke(
                            self,
                            ui.ctx(),
                            "mask.new",
                            serde_json::json!({ "vertices": verts, "closed": true }),
                        );
                        self.ui.status = if r.is_ok() {
                            "已新建矩形蒙版".into()
                        } else {
                            "新建蒙版需要先选中图层".into()
                        };
                    } else {
                        self.ui.status = "先打开一个合成".into();
                    }
                }
                Some(16) => {
                    let r = crate::menus::invoke(
                        self,
                        ui.ctx(),
                        "layer.enableTimeRemap",
                        serde_json::json!({ "value": true }),
                    );
                    self.ui.status = if r.is_ok() {
                        "已为选中图层打开时间重映射（可做变速）".into()
                    } else {
                        "先选中一个图层".into()
                    };
                }
                _ => {}'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    proj = root / "crates/ui-egui/src/panels/project.rs"
    src = proj.read_text(encoding="utf-8")
    if MARKER not in src:
        for name, old, new in (
            ("variant", VARIANT_OLD, VARIANT_NEW),
            ("exts", EXTS_OLD, EXTS_NEW),
            ("cmd", CMD_OLD, CMD_NEW),
            ("fn", FN_OLD, FN_NEW),
        ):
            if src.count(old) != 1:
                raise SystemExit(f"project {name} anchor: {src.count(old)}")
            src = src.replace(old, new, 1)
        proj.write_text(src, encoding="utf-8")
        print("project.rs: Audio import kind + pick_audio()")

    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER in src:
        print("tray buttons already present")
        return
    for name, old, new in (
        ("capcut", CAPCUT_OLD, CAPCUT_NEW),
        ("kuaishou", KS_OLD, KS_NEW),
        ("default", ITEMS_OLD, ITEMS_NEW),
        ("match", MATCH_OLD, MATCH_NEW),
    ):
        if src.count(old) != 1:
            raise SystemExit(f"frame {name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    frame.write_text(src, encoding="utf-8")
    print("frame.rs: 音频 / 蒙版 / 变速 buttons wired")


if __name__ == "__main__":
    main()
