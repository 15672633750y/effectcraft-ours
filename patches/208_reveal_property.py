#!/usr/bin/env python3
"""AE 的属性键：P/位置、S/缩放、R/旋转、T/不透明度、A/锚点。

`anim.reveal` only reveals *animated* properties (U). These keys reveal one named property whether or
not it is animated, for the selected layers — or for every layer when nothing is selected, as in
After Effects. The reveal goes through the same frontend call the timeline already uses.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_REVEAL_PROPERTY_V1"

FN = '''

/// EFFECTCRAFT_OURS_REVEAL_PROPERTY_V1 — 展开指定属性（P/S/R/T/A）。
fn reveal_property(s: &mut Session, p: &Value) -> Result<Value> {
    let want = str_p(p, "prop").unwrap_or("position").to_string();
    let cid = super::comp_id(s, p)?;
    let comp = s.project.comp(cid).ok_or(EngineError::NoComp)?;
    let layers: Vec<LayerId> =
        if s.state.selected_layers.is_empty() { comp.layers.iter().map(|l| l.id).collect() } else { s.state.selected_layers.clone() };
    let mut out = vec![];
    for lid in &layers {
        let Some(l) = comp.layer(*lid) else { continue };
        for top in l.props.groups() {
            if top.match_id != "transform" {
                continue;
            }
            if let Some(pr) = top.get(&want) {
                out.push(json!({"layer": lid.0, "prop": pr.uid}));
            }
        }
    }
    if out.is_empty() {
        return Err(bad("layer.revealProperty", "the layer has no such property"));
    }
    let layer_ids: Vec<u64> = layers.iter().map(|l| l.0).collect();
    frontend(s, "timeline.revealProps", &json!({"props": out, "kind": "property", "layers": layer_ids}))?;
    Ok(json!({"props": out}))
}
'''

REG_OLD = '''        cmd!("anim.reveal", "Reveal Properties", [], None, "{kind: keyframes|animation|modified}", has_comp, reveal),
'''
REG_NEW = REG_OLD + '''        cmd!(
            "layer.revealProperty",
            "Reveal a Property",
            [],
            None,
            "{prop: position|scale|rotation|opacity|anchor, layers?} — no layers: every layer",
            has_comp,
            reveal_property
        ),
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/animation.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("reveal_property already installed")
        return
    if src.count(REG_OLD) != 1:
        raise SystemExit(f"registration anchor: {src.count(REG_OLD)}")
    src = src.replace(REG_OLD, REG_NEW, 1)
    src += FN
    path.write_text(src, encoding="utf-8")
    print("P/S/R/T/A reveal command added")


if __name__ == "__main__":
    main()
