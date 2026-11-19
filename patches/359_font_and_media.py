#!/usr/bin/env python3
"""两条导入路径的补全：

1. `ours.addFont {path}` —— 运行时注册一个字体文件（`.ttf` / `.otf` / `.ttc`）。引擎的
   `text::fonts::add_font_data` 早就有这个能力，只是一直没暴露成命令，所以 app 里没法加字体。
2. 媒体文件走 `file.import` 的 `newComp`（引擎自带）：导入素材并**顺手建一个和素材同尺寸、
   同帧率、同时长的合成**，不用先导素材再手动建合成。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FONT_AND_MEDIA_V1"

SPEC_OLD = '''    ), cmd!(
        "ours.presets",'''
SPEC_NEW = '''    ), cmd!(
        "ours.addFont",
        "导入字体",
        [],
        None,
        "{path: .ttf/.otf/.ttc 路径}",
        always,
        add_font
    ), cmd!(
        "ours.presets",'''

FN = r'''

/// EFFECTCRAFT_OURS_FONT_AND_MEDIA_V1 — 运行时注册字体文件，返回注册到的 face 数。
fn add_font(_s: &mut Session, p: &Value) -> Result<Value> {
    let path = str_p(p, "path").ok_or_else(|| bad("ours.addFont", "no path"))?.to_string();
    let bytes = std::fs::read(&path)
        .map_err(|e| crate::EngineError::Other(format!("cannot read {path}: {e}")))?;
    let faces = crate::text::fonts::add_font_data(bytes).len();
    Ok(json!({ "path": path, "faces": faces }))
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/ours_export.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("font command already present")
        return
    if src.count(SPEC_OLD) != 1:
        raise SystemExit(f"spec anchor: {src.count(SPEC_OLD)}")
    src = src.replace(SPEC_OLD, SPEC_NEW, 1)
    if not src.endswith("\n"):
        src += "\n"
    src += FN
    path.write_text(src, encoding="utf-8")
    print("ours.addFont registered")


if __name__ == "__main__":
    main()
