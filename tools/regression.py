#!/usr/bin/env python3
"""推送前回归清单（静态检查版）。

清单里的 1-8 大多是设备上的真实行为，本地无法执行；这里把每一条能静态验证的部分固化下来，
任何一项从"过"变"不过"就直接失败，避免为了加新功能而把旧功能改坏。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = ROOT / "tmp"


def fresh_tree() -> Path:
    """在纯净源码树上应用全部补丁，返回产物根目录。"""
    out = TMP / "reg"
    if out.exists():
        subprocess.run(["rm", "-rf", str(out)], check=True)
    out.mkdir(parents=True)
    subprocess.run(["cp", "-a", str(ROOT / "repo"), str(out / "src")], check=True)
    r = subprocess.run(
        [sys.executable, str(TMP / "apply_all.py"), str(out / "src")],
        capture_output=True, text=True,
    )
    if "fails 0" not in r.stdout:
        print("补丁应用失败：")
        print(r.stdout[-3000:])
        raise SystemExit(1)
    return out / "src"


def read(root: Path, rel: str) -> str:
    p = root / rel
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""


def main() -> int:
    src = fresh_tree()
    frame = read(src, "crates/ui-egui/src/app/frame.rs")
    project = read(src, "crates/ui-egui/src/panels/project.rs")
    ours = read(src, "crates/engine/src/cmd/ours_export.rs")
    aep = read(src, "crates/engine/src/cmd/aep.rs")
    files = read(src, "crates/engine/src/cmd/file.rs")
    viewer = read(src, "crates/ui-egui/src/panels/viewer.rs")
    cloud = read(src, "crates/ui-egui/src/cloud.rs")

    checks = []

    # 1. .aep 导入仍然接到 file.importAep
    checks.append((
        "1 .aep -> file.importAep",
        '"file.importAep"' in frame and "aep" in frame,
    ))
    # 2. 文字预设不许静默
    checks.append((
        "2 文字预设给出明确结果（不静默）",
        "is_text_only_preset" in ours or "文字预设" in ours,
    ))
    # 3. .gp 走 applyPreset
    checks.append((
        "3 .gp -> ours.applyPreset",
        '"gp"' in frame and '"ours.applyPreset"' in frame,
    ))
    # 4. 保存预设对话框仍在
    checks.append((
        "4 保存预设弹窗仍在",
        "preset_save_panel" in frame or "savePreset" in frame,
    ))
    # 5. 导入面板尺寸
    row52 = "vec2(width, 40.0)" in project or "vec2(width, 52.0)" in project
    checks.append(("5 导入面板行高在 40/52", row52))
    checks.append(("5 面板宽度 340", ".max_width(340.0)" in project))
    # 6. 预设库搜索 + 芯片
    checks.append((
        "6 预设库搜索与芯片",
        "ours-preset-search" in frame and "ours-preset-chip" in frame,
    ))
    # 7. 布局按钮画在浮层之前
    i_layout = frame.find("EFFECTCRAFT_OURS_LAYOUT_BTN_AREA_V1")
    i_shortcut = frame.find("shortcut_panel(self, ui, full);")
    checks.append((
        "7 布局按钮在浮层之前绘制",
        i_layout > 0 and i_shortcut > 0 and i_layout < i_shortcut,
    ))
    # 8. 云端命令仍在
    checks.append((
        "8 云端上传/下载命令仍在",
        "upload_project" in cloud and "download_project" in cloud,
    ))
    # 附：字体与 zip 分流
    checks.append(("9 字体命令仍在", '"ours.addFont"' in ours))
    ext = read(src, "crates/engine/src/cmd/import_ext.rs")
    checks.append(("10 zip 分流仍在", "ZIP_DISPATCH" in ext))
    # 防止再出现"重写函数时漏掉别的补丁注入的集合"：这四个必须都在 import_nodevideo 里
    for var in ("fills", "adjustments", "all_nodes", "nodes"):
        checks.append((f"11 import_nodevideo 里 {var} 仍在", f"let mut {var}" in ext))
    checks.append(("12 .nv-skeleton 记录仍在", ".nv-skeleton.txt" in ext))
    # 布局：五套 id 都在，且竖屏布局结构彼此不同（不是同一棵树换比例）
    dock = read(src, "crates/ui-egui/src/dock.rs")
    for lid in ("ae", "capcut", "blurrr", "kuaishou", "am"):
        # am 与旧名 jianying 合并在一个 match 分支里：`"am" | "jianying" =>`
        present = f'"{lid}" =>' in dock or f'"{lid}" |' in dock or f'| "{lid}"' in dock
        checks.append((f"13 布局 {lid} 仍在", present))
    i = dock.find("pub fn ours_layout")
    seg = dock[i: dock.find("\n}", i)] if i > 0 else ""
    checks.append(("13 AM 有三栏（预览/时间线/工具）", '"am" | "jianying" => Layout {' in seg))
    checks.append(("13 亮色布局主题同步", 'ThemeKind::Light' in frame))
    checks.append(("13 品牌色板（拆包颜色）", ('BRAND_PALETTE_V1' in frame or 'BRAND_PALETTE_V2' in frame) and '0x00, 0xCA, 0xE0' in frame and '0xFF, 0x50, 0x00' in frame))
    theme_src = read(src, "crates/ui-egui/src/theme.rs")
    checks.append(("14 滚动条加宽到 12px", 'bar_width: 12.0' in theme_src))
    checks.append(("14 预设库滚动条可拖", 'ours-preset-scrollbar' in frame))
    checks.append(("14 竖屏自绘顶栏", 'fn ours_shell_header' in frame))
    checks.append(("15 底部工具条可横向滚动", 'EFFECTCRAFT_OURS_TRAY_SCROLL_V1' in frame and 'ours-tray-drag' in frame))
    checks.append(("15 AM 左侧竖栏 + 动作接线", 'EFFECTCRAFT_OURS_AM_LEFT_RAIL_V1' in frame and 'EFFECTCRAFT_OURS_RAIL_ACTIONS_V1' in frame))
    checks.append(("15 CapCut 播放条", 'EFFECTCRAFT_OURS_CAPCUT_TRANSPORT_V1' in frame))
    checks.append(("15 工具条导出按钮", 'EFFECTCRAFT_OURS_TRAY_EXPORT_V1' in frame and '"导出", 8' in frame))
    checks.append(("16 轨道标签色按品牌", 'EFFECTCRAFT_OURS_BRAND_TRACK_COLORS_V1' in frame and '0xA8, 0x55, 0xF7' in frame))
    checks.append(("16 Blurrr 顶部条 + 动作", 'EFFECTCRAFT_OURS_BLURRR_TOP_V1' in frame and 'EFFECTCRAFT_OURS_BLURRR_ACTIONS_V1' in frame))
    proj = read(src, "crates/ui-egui/src/panels/project.rs")
    checks.append(("17 音频/蒙版/变速 按钮", 'pick_audio' in proj and '"蒙版", 15' in frame and 'Some(15) =>' in frame and 'Some(16) =>' in frame))
    checks.append(("17 存帧按钮", '"存帧", 17' in frame and 'render.saveCurrentPreview' in frame))
    checks.append(("17 变速快捷档", '"0.5×", 18' in frame and 'layer.timeStretch' in frame and 'Some(20) =>' in frame))
    checks.append(("18 竖屏导出/插件窗口", 'pub(crate) fn export_window' in read(src, "crates/ui-egui/src/header.rs") and 'crate::header::export_window(self, ui.ctx());' in frame))
    checks.append(("18 小区块慢速扫光", 'EFFECTCRAFT_OURS_GRID_SCAN_V2' in frame and 'for dgx in -4..=4' in frame))
    checks.append(("18 时间伸缩面板 0.01–100", 'fn ours_speed_panel' in frame and '0.01..=100.0' in frame))
    checks.append(("18 dock 加高到 78", 'let h = 78.0;' in frame and 'let cell_w = 88.0_f32;' in frame))
    checks.append(("18 导入面板全局绘制", 'crate::panels::project::import_window(self, ui.ctx());' in frame))
    checks.append(("19 骨架色随品牌", 'EFFECTCRAFT_OURS_PALETTE_FIELDS_V1' in frame and 't.pasteboard = bg.lerp_to_gamma(text, 0.10);' in frame))
    checks.append(("19 竖屏设置入口", 'EFFECTCRAFT_OURS_SETTINGS_BUTTON_V1' in frame and 'crate::Dialog::Settings' in frame))
    cloud_src = read(src, "crates/ui-egui/src/cloud.rs")
    acct_src = read(src, "crates/ui-egui/src/account_ui.rs")
    checks.append(("20 云端 DELETE 真正发出", 'agent.delete(&url)' in cloud_src and 'CLOUD_REQUEST_ARMS_V2' in cloud_src))
    checks.append(("20 上传前校验落盘与 schema", 'pub fn upload_project_from_path' in cloud_src and 'v.get("schema").is_some()' in cloud_src))
    checks.append(("20 工程名稳定", 'fn cloud_project_name' in acct_src and 'fn cloud_clean_name' not in acct_src))
    checks.append(("21 自动保存名先剥离再判断", 'EFFECTCRAFT_OURS_CLOUD_NAME_TOAST_V1' in acct_src and 'lower.starts_with("untitled")' in acct_src))
    checks.append(("21 下载完成清提示", 'Event::Downloaded(path) => {' in acct_src and acct_src.count('set(ui, CLOUD_LOADING, false);') >= 2))
    checks.append(("21 连续崩溃进安全模式", 'EFFECTCRAFT_OURS_SAFE_MODE_V1' in read(src, "crates/ui-egui/src/panels/settings.rs") and '.recovery-count' in read(src, "crates/ui-egui/src/panels/settings.rs")))
    checks.append(("21 自动保存不再套娃", 'EFFECTCRAFT_OURS_AUTOSAVE_NO_NEST_V1' in read(src, "crates/engine/src/settings/autosave.rs")))
    checks.append(("21 上传要求真实工程文件", 'EFFECTCRAFT_OURS_UPLOAD_REAL_FILE_V1' in acct_src))
    checks.append(("21 cloud.log 超 512KB 截断", 'EFFECTCRAFT_OURS_CLOUD_LOG_ROTATE_V1' in cloud_src))
    checks.append(("20 删除后重新拉列表", 'CLOUD_DELETE_RESYNC_V1' in acct_src))
    checks.append(("14 时间线横向滚动条", 'EFFECTCRAFT_OURS_TIMELINE_SCROLLBAR_V1' in frame))
    checks.append(("14 时间线滚动条可点跳", 'EFFECTCRAFT_OURS_TIMELINE_SCROLLBAR_CLICK_V1' in frame))
    checks.append(("13 CapCut 底部是素材库", '"capcut" => Layout' in seg and 'vsplit(Ratio(0.52), tabs(&[Timeline], 0), tabs(&[Project], 0))' in seg))

    bad = 0
    for name, ok in checks:
        print(("  OK   " if ok else "  FAIL ") + name)
        bad += 0 if ok else 1
    print(f"\n{len(checks) - bad}/{len(checks)} 通过")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
