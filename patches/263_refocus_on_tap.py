#!/usr/bin/env python3
"""手机上同一个输入框「第一次点能弹出键盘，之后再点就不弹」——每次点击都强制重取焦点。

On Android the soft keyboard only appears when a text field *gains* focus. Once a field is focused and the
keyboard is dismissed (the back gesture, or the keyboard covering what you wanted to tap), tapping the
same field again changes nothing, so the keyboard never comes back. Every click on a numeric field now
drops and re-requests focus, which makes the platform show the keyboard again.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_REFOCUS_ON_TAP_V1"

OLD = """    let r = ui.add(egui::TextEdit::singleline(&mut text).desired_width(96.0).font(Tokens::mono(12.0)));
"""

NEW = """    let r = ui.add(egui::TextEdit::singleline(&mut text).desired_width(96.0).font(Tokens::mono(12.0)));
    // EFFECTCRAFT_OURS_REFOCUS_ON_TAP_V1 — 每次点击都重新取焦点，手机才会再次弹出键盘
    if r.clicked() {
        let id = r.id;
        ui.memory_mut(|m| m.surrender_focus(id));
        ui.memory_mut(|m| m.request_focus(id));
    }
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/panels/comp_settings.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("re-focus on tap already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("numeric fields re-request focus on every tap")


if __name__ == "__main__":
    main()
