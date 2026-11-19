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
    checks.append(("13 品牌色板（拆包颜色）", 'EFFECTCRAFT_OURS_BRAND_PALETTE_V1' in frame and '0x00, 0xCA, 0xE0' in frame and '0xFF, 0x50, 0x00' in frame))
    theme_src = read(src, "crates/ui-egui/src/theme.rs")
    checks.append(("14 滚动条加宽到 12px", 'bar_width: 12.0' in theme_src))
    checks.append(("14 预设库滚动条可拖", 'ours-preset-scrollbar' in frame))
    checks.append(("14 竖屏自绘顶栏", 'fn ours_shell_header' in frame))
    checks.append(("14 时间线横向滚动条", 'EFFECTCRAFT_OURS_TIMELINE_SCROLLBAR_V1' in frame))
    checks.append(("14 时间线滚动条可点跳", 'EFFECTCRAFT_OURS_TIMELINE_SCROLLBAR_CLICK_V1' in frame))
    checks.append(("13 CapCut 底部是素材库", '"capcut" => Layout' in seg and 'vsplit(Ratio(0.55), tabs(&[Timeline], 0), tabs(&[Project], 0))' in seg))

    bad = 0
    for name, ok in checks:
        print(("  OK   " if ok else "  FAIL ") + name)
        bad += 0 if ok else 1
    print(f"\n{len(checks) - bad}/{len(checks)} 通过")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
