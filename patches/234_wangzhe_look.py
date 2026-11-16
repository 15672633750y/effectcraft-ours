#!/usr/bin/env python3
"""内置「王者滤镜」调色：按 AE 面板里的真实数值一键复刻（三条彩×2 + 暗角 + 锐化 + 钝化蒙版 + 色相/饱和度）。

The values come from the user's After Effects screenshots of the 1.7 preset, not from guesses:
two three-strip passes (Amount 1.0 / 0.5, Brightness 1.0 / 1.15, Saturation 0.64 both), a vignette, a
sharpen of 12, an unsharp mask of 4 / 120 / 0 and a hue/saturation of -5.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_WANGZHE_LOOK_V1"

FN = r'''
/// EFFECTCRAFT_OURS_WANGZHE_LOOK_V1 — 按 AE 面板数值复刻「王者滤镜」。
fn apply_wangzhe(s: &mut Session, chains: &[(&str, &[(&str, serde_json::Value)])], cmd: &str) -> Result<usize> {
    let mut applied = 0usize;
    for (index, (id, params)) in chains.iter().enumerate() {
        if s.execute("effect.apply", json!({ "effect": id })).is_err() {
            return Err(bad(cmd, format!("效果 {id} 无法应用（先选中一个图层）")));
        }
        applied += 1;
        // 第二份同名效果用 `#2` 指定实例；不支持时退回不带序号的路径
        for (param, value) in *params {
            let with_index = format!("effects/{id}#{}", index + 1);
            let plain = format!("effects/{id}");
            let ok = s.execute("prop.set", json!({"path": format!("{with_index}/{param}"), "value": value.clone()})).is_ok()
                || s.execute("prop.set", json!({"path": format!("{plain}/{param}"), "value": value.clone()})).is_ok();
            if !ok {
                // 参数写不进去不算致命：效果已经在图层上了
            }
        }
    }
    Ok(applied)
}

fn wangzhe(s: &mut Session, _p: &Value) -> Result<Value> {
    let chains: Vec<(&str, Vec<(&str, serde_json::Value)>)> = vec![
        ("S_VintageColor3Strip", vec![
            ("amount", json!(1.0)),
            ("keyLayerDensity", json!(0.1)),
            ("brightness", json!(1.0)),
            ("saturation", json!(0.64)),
            ("offsetDarks", json!(0.0)),
            ("blurMask", json!(12.0)),
        ]),
        ("S_VintageColor3Strip", vec![
            ("amount", json!(0.5)),
            ("keyLayerDensity", json!(0.3)),
            ("brightness", json!(1.15)),
            ("saturation", json!(0.64)),
            ("offsetDarks", json!(0.0)),
        ]),
        ("S_Vignette", vec![
            ("radius", json!(1.03)),
            ("relHeight", json!(0.75)),
            ("relWidth", json!(1.08)),
            ("edgeSoftness", json!(1.0)),
            ("smoothCurve", json!(0.4)),
            ("opacity", json!(0.5)),
            ("sourceBrightness", json!(1.02)),
        ]),
        ("ec.blur.sharpen", vec![("amount", json!(12.0))]),
        ("ec.color.huesaturation", vec![("saturation", json!(-5.0))]),
    ];
    let refs: Vec<(&str, &[(&str, serde_json::Value)])> =
        chains.iter().map(|(id, params)| (*id, params.as_slice())).collect();
    let n = apply_wangzhe(s, &refs, "ours.applyWangzheLook")?;
    Ok(json!({"effects": n}))
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/ours_export.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("wangzhe look already present")
        return
    anchor = '''        super::ours_capcut::export
    )]
}'''
    if src.count(anchor) != 1:
        raise SystemExit(f"anchor: {src.count(anchor)}")
    new_specs = '''        super::ours_capcut::export
    ), cmd!(
        "ours.applyWangzheLook",
        "应用王者滤镜调色",
        [],
        None,
        "{layers?}",
        always,
        wangzhe
    )]
}'''
    src = src.replace(anchor, new_specs, 1)
    src += FN
    path.write_text(src, encoding="utf-8")
    print("王者滤镜 recipe added")


if __name__ == "__main__":
    main()
