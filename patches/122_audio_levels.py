#!/usr/bin/env python3
"""Audio Levels read like After Effects: one dB number, and the two channels move together.

In After Effects the Audio Levels value is a single `+4.00 dB` until you unlink it. Here it was two
plain numbers with the link off by default, so "turn the whole thing down" meant dragging twice.
Now the pair is linked by default (the chain icon still unlinks it) and the numbers carry their dB.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_AUDIO_LEVELS_AE_V1"

EDITS = [
    (
        '    let linked = linkable && app.ui.timeline.is_linked(uid, !(size || levels));\n',
        '    // ' + MARKER + '\n'
        '    // Audio Levels start linked, as After Effects draws them: one dB for both channels.\n'
        '    let linked = linkable && app.ui.timeline.is_linked(uid, !size);\n',
    ),
    (
        '            app.ui.timeline.toggle_link(uid, !(size || levels));\n',
        '            app.ui.timeline.toggle_link(uid, !size);\n',
    ),
    (
        '        let suffix = if pct && d + 1 == n { "%" } else { "" };\n',
        '        let suffix = if pct && d + 1 == n { "%" } else if levels { " dB" } else { "" };\n',
    ),
]


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/timeline.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("audio levels already AE-shaped")
        return
    for old, new in EDITS:
        if src.count(old) != 1:
            raise SystemExit(f"anchor {old.strip()[:50]!r}: expected 1, found {src.count(old)}")
        src = src.replace(old, new, 1)
    path.write_text(src, encoding="utf-8")
    print("Audio Levels: dB suffix, linked by default")


if __name__ == "__main__":
    main()
