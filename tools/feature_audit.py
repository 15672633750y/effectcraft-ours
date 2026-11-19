#!/usr/bin/env python3
"""全盘扫描：每个补丁的产物是否真的出现在最终代码里。

原理：每个补丁都用 `MARKER = "EFFECTCRAFT_..."` 做幂等标记。把全部补丁应用到纯净树后，
在产物里搜这个标记——搜不到，说明这个补丁**实际没改到任何东西**（锚点失配被吞、或被后来的补丁覆盖）。
再叠加一份"关键功能清单"，逐项确认关键命令/字符串仍在。
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOWN_NOOP = {"175_plugin_path_install.py", "350_preset_save_no_saf.py"}

# 关键功能：名字 → 在产物里必须出现的字面量（任一命中即算在）
FEATURES = {
    "文件关联/ImportShim": ["ImportShim"],
    "aep 导入分发": ['"file.importAep"'],
    "ffx 预设套用": ['"ours.applyPreset"'],
    "gp 预设": ['"gp"'],
    "文字预设兜底(314 蒸发)": ["Evaporate Animator"],
    "字体注册": ['"ours.addFont"'],
    "字体目录扫描": ["EffectCraft/Fonts"],
    "Import 目录扫描": ["EffectCraft/Import"],
    "zip 分流": ["ZIP_DISPATCH"],
    "aep 自动重连": ['"file.relinkFootage"'],
    "导入结果常驻面板": ["ours-import-report"],
    "预设库搜索": ["ours-preset-search"],
    "预设库芯片": ["ours-preset-chip"],
    "保存预设弹窗": ["preset_save_panel"],
    "布局按钮(浮层之前)": ["EFFECTCRAFT_OURS_LAYOUT_BTN_AREA_V1"],
    "账号槽位": ["ours-account-slot"],
    "云端工程": ["云端工程"],
    "崩溃自动恢复": ["自动恢复失败"],
    "崩溃日志": ["crash.log"],
    "导入面板 340": [".max_width(340.0)"],
    "NV 骨架记录(186)": [".nv-skeleton.txt"],
    "share 桥(210)": ["shareFile"],
}


def fresh_tree() -> Path:
    out = ROOT / "tmp" / "audit"
    subprocess.run(["rm", "-rf", str(out)], check=True)
    out.mkdir(parents=True)
    subprocess.run(["cp", "-a", str(ROOT / "repo"), str(out / "src")], check=True)
    r = subprocess.run([sys.executable, str(ROOT / "tmp/apply_all.py"), str(out / "src")],
                       capture_output=True, text=True)
    if "fails 0" not in r.stdout:
        print(r.stdout[-2000:])
        raise SystemExit("patch application failed")
    return out / "src"


def markers(patch: Path) -> set[str]:
    src = patch.read_text(encoding="utf-8", errors="ignore")
    found = set()
    for m in re.finditer(r'^(?:[A-Z_]*MARKER[A-Z_]*)\s*=\s*"([A-Z0-9_]+)"', src, re.M):
        found.add(m.group(1))
    return found


def main() -> int:
    src = fresh_tree()
    blob = []
    for p in src.rglob("*"):
        if p.is_file() and p.suffix in {".rs", ".json", ".toml", ".java", ".xml", ".py", ".yml"}:
            try:
                blob.append(p.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                pass
    text = "\n".join(blob)
    print(f"产物文件 {len(blob)} 个，共 {len(text)//1024} KB\n")

    print("=== 补丁产物检查 ===")
    missing = []
    total = 0
    for patch in sorted((ROOT / "ours-patches").glob("*.py")):
        for mk in markers(patch):
            total += 1
            if mk in text:
                continue
            if patch.name in KNOWN_NOOP:
                continue
            missing.append((patch.name, mk))
    print(f"  检查 {total} 个标记，缺失 {len(missing)}")
    for name, mk in missing:
        print(f"  MISSING {name}  ({mk})")

    print("\n=== 关键功能清单 ===")
    bad = 0
    for name, needles in FEATURES.items():
        ok = any(n in text for n in needles)
        print(("  OK   " if ok else "  FAIL ") + name)
        bad += 0 if ok else 1

    print(f"\n补丁标记缺失 {len(missing)} 项，关键功能失败 {bad} 项")
    return 1 if bad or missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
