#!/usr/bin/env python3
"""Effect/layer headers fall back to the property-name table when the effect lookup misses."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_HEADER_FALLBACK_V1"
OLD = "        let shown = crate::i18n::effects::group(effect, &g.name);\n"
NEW = (
    "        // " + MARKER + "\n"
    "        // If the effect table did not know the name, the structural group table gets a turn:\n"
    "        // that is what turns \"Layer Transform\" into 图层变换.\n"
    "        let shown = {\n"
    "            let first = crate::i18n::effects::group(effect, &g.name);\n"
    "            if first == g.name { crate::i18n::prop::name(&g.name, \"\").to_string() } else { first }\n"
    "        };\n"
)


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/effect_controls/panel.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("header fallback already installed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("headers fall back to the property-name table")


if __name__ == "__main__":
    main()
