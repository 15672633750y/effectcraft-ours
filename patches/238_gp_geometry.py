#!/usr/bin/env python3
"""`.gp` 的几何参数与 AE 一致：center 是归一化偏移、opacity/edge_softness 可以超出 0–1。

From the vignette presets: `center` is normalised ((0.0025, -0.439) ≈ centre + offsets), `opacity` goes
to 2.7, `rel_width` to 5.9. Our params used pixels for the centre and clamped opacity to 1, so a preset's
numbers landed wrong.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_GP_GEOMETRY_V1"

# 1) .gp 导入时把 center 由归一化换成像素
ADD_OLD = """    s.execute("effect.apply", json!({ "effect": id }))?;
    let mut set = 0usize;
"""
ADD_NEW = """    s.execute("effect.apply", json!({ "effect": id }))?;
    let (cw, chh) = s.active_comp().map(|c| (c.width as f64, c.height as f64)).unwrap_or((1920.0, 1080.0));
    let mut set = 0usize;
"""

CENTER_OLD = """        let Some(param) = gp_param_name(&name) else { continue };
"""
CENTER_NEW = """        // center 在 Sapphire 里是相对画面中心的归一化偏移，我们存像素
        if name == "center" {
            if let Some(a) = value.as_array()
                && a.len() >= 2
                && let (Some(x), Some(y)) = (a[0].as_f64(), a[1].as_f64())
            {
                let px = (0.5 + x) * cw;
                let py = (0.5 + y) * chh;
                let _ = s.execute(
                    "prop.set",
                    json!({"path": format!("effects/{id}/centerXY"), "value": json!([px, py])}),
                );
            }
            continue;
        }
        let Some(param) = gp_param_name(&name) else { continue };
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/import_ext.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print(".gp geometry already handled")
        return
    for old, new in ((ADD_OLD, ADD_NEW), (CENTER_OLD, CENTER_NEW)):
        if src.count(old) < 1:
            raise SystemExit(f"anchor {old[:40]!r}: {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("centre converted to pixels, geometry passed through")


if __name__ == "__main__":
    main()
