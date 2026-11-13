#!/usr/bin/env python3
"""Group headings in Effect Controls (Layer Transform, Contents, ...) show in Chinese."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_GROUP_NAMES_V1"
OLD = "pub(crate) fn group(id: &str, stored: &str) -> String {\n    let Some(spec) = effectcraft_engine::effects::find(id) else { return stored.to_string() };"
NEW = "pub(crate) fn group(id: &str, stored: &str) -> String {\n    // " + MARKER + "\n    // Structural groups are not effect groups: name them directly.\n    match stored {\n        \"Layer Transform\" => return \"图层变换\".to_string(),\n        \"Transform\" => return \"变换\".to_string(),\n        \"Contents\" => return \"内容\".to_string(),\n        \"Text\" => return \"文本\".to_string(),\n        \"Shape\" => return \"形状\".to_string(),\n        \"Masks\" => return \"遮罩\".to_string(),\n        \"Material Options\" => return \"材质选项\".to_string(),\n        _ => {}\n    }\n    let Some(spec) = effectcraft_engine::effects::find(id) else { return stored.to_string() };"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/effects.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("group headings already translated")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("structural group headings are Chinese")


if __name__ == "__main__":
    main()
