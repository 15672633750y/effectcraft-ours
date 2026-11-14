#!/usr/bin/env python3
"""Status messages in Chinese: an engine error says "layer.rename: the layer is locked".

The message is painted straight from `app.ui.status`, so however complete the table was, command
failures stayed English. The toast now goes through `i18n::status`, which translates the message
after a `command: ` prefix and leaves the command id alone (it is what a bug report needs).
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_STATUS_ZH_V1"

OLD = '''        let msg = if !self.ui.status.is_empty() {
            Some(self.ui.status.clone())
        } else {
'''
NEW = '''        let msg = if !self.ui.status.is_empty() {
            // EFFECTCRAFT_OURS_STATUS_ZH_V1 — 失败提示里的英文句子也翻
            Some(crate::i18n::status(&self.ui.status))
        } else {
'''

HELPER = '''
/// A status line in the interface language: `command.id: message` keeps the command and translates
/// the message when the table has it.
pub fn status(text: &str) -> String {
    if let Some((cmd, rest)) = text.split_once(": ") {
        let shown = tr(rest);
        if shown != rest {
            return format!("{cmd}: {shown}");
        }
    }
    tr(text).to_string()
}
'''

ANCHOR = "pub(crate) use ui::{set_current, tr, tr_args};\n"


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    frame = root / "crates/ui-egui/src/app/frame.rs"
    src = frame.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(OLD) != 1:
            raise SystemExit(f"frame anchor: {src.count(OLD)}")
        frame.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
        print("status toast goes through the table")

    i18n = root / "crates/ui-egui/src/i18n.rs"
    src = i18n.read_text(encoding="utf-8")
    if "pub fn status(" not in src:
        if src.count(ANCHOR) != 1:
            raise SystemExit(f"i18n anchor: {src.count(ANCHOR)}")
        i18n.write_text(src.replace(ANCHOR, ANCHOR + HELPER, 1), encoding="utf-8")
        print("i18n::status added")


if __name__ == "__main__":
    main()
