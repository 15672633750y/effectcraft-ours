#!/usr/bin/env python3
"""「保存预设」接上我们自己的导出链路（上游那个只会写空文件）。

两处：
1. `frontend.rs`：保存对话框的默认文件名 `Preset.ecpreset` → `Preset.ffx`（用户要的扩展名）。
2. `animation.rs::save_preset`：上游只保存**选中的属性/效果**，选中整个图层时直接报
   「select properties or effects to save」，落盘就是 0 字节。现在没有选中效果/属性时，
   改为调用 `ours_export::export_preset`：读选中图层的**整个效果栈**（id + 参数值）写成
   `{"format":"effectcraft.preset.v1", "effects":[{id, params}]}` 的 JSON。
   选中了具体效果的情况保持上游行为，不动。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SAVE_PRESET_JSON_V1"

FE_OLD = '"anim.savePreset" => ("path", Ask::Save("Preset.ecpreset".into())),'
FE_NEW = '"anim.savePreset" => ("path", Ask::Save("Preset.ffx".into())),'

ANIM_OLD = '''    if props.is_empty() && effects.is_empty() {
        return Err(bad("anim.savePreset", "select properties or effects to save"));
    }
'''
ANIM_NEW = '''    if props.is_empty() && effects.is_empty() {
        // EFFECTCRAFT_OURS_SAVE_PRESET_JSON_V1 — 没选中具体效果/属性时，导出选中图层的
        // 整个效果栈（我们自己的 JSON 预设）。上游这里直接报错，落盘就是 0 字节。
        return super::ours_export::export_preset(s, p);
    }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    fe = root / "crates/ui-egui/src/menus/frontend.rs"
    src = fe.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(FE_OLD) != 1:
            raise SystemExit(f"frontend anchor: {src.count(FE_OLD)}")
        fe.write_text(src.replace(FE_OLD, FE_NEW, 1), encoding="utf-8")
        print("save dialog default -> Preset.ffx")

    anim = root / "crates/engine/src/cmd/animation.rs"
    src = anim.read_text(encoding="utf-8")
    if MARKER in src:
        print("save_preset fallback already present")
        return
    if src.count(ANIM_OLD) != 1:
        raise SystemExit(f"animation anchor: {src.count(ANIM_OLD)}")
    src = src.replace(ANIM_OLD, ANIM_NEW, 1)
    anim.write_text(src, encoding="utf-8")
    print("save_preset falls back to our JSON export")


if __name__ == "__main__":
    main()
