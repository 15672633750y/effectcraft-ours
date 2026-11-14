#!/usr/bin/env python3
"""Drop repeated rows from the Simplified Chinese catalog.

Our patches add rows for enums and engine messages; a few of those strings were already in the
upstream table (Cancel, Show, Sort …). A repeated source is harmless at run time (the first row
wins) but `catalogs_are_unique_and_keep_the_english_shape` calls it a catalog bug, and a duplicate
with a *different* translation is a trap for whoever edits next. This keeps the first row of each
source string.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_I18N_DEDUPE_V1"

ROW = re.compile(r'^(\s*)\("((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"\s*\),\s*$')


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/i18n/ui.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("catalog already deduped")
        return
    start = src.index("const SIMPLIFIED_CHINESE: &[(&str, &str)] = &[")
    end = src.index("\n];", start)
    block = src[start:end]
    seen = set()
    out = []
    dropped = 0
    for line in block.splitlines(True):
        m = ROW.match(line.rstrip("\n"))
        if m:
            key = m.group(2)
            if key in seen:
                dropped += 1
                continue
            seen.add(key)
        out.append(line)
    src = src[:start] + "".join(out) + src[end:]
    src = src.replace("const SIMPLIFIED_CHINESE: &[(&str, &str)] = &[",
                      "// " + MARKER + "\nconst SIMPLIFIED_CHINESE: &[(&str, &str)] = &[", 1)
    path.write_text(src, encoding="utf-8")
    print(f"dropped {dropped} repeated rows")


if __name__ == "__main__":
    main()
