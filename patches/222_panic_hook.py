#!/usr/bin/env python3
"""Rust panic 也写文件：闪退不再什么都没有。

The Java handler covers Java exceptions and the heartbeat covers native aborts, but a Rust `panic!`
unwinds (or aborts on Android) with its message going to a log nobody can read. A panic hook writes
`crash-rust-<time>.txt` into DCIM/EffectCraft — message, location and a backtrace — then calls the
previous hook, so behaviour is otherwise unchanged.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PANIC_HOOK_V1"

ANCHOR = "    pub fn new(session: Session) -> Self {\n"
NEW = ANCHOR + "        install_panic_hook();\n"

FUNC = '''

/// EFFECTCRAFT_OURS_PANIC_HOOK_V1 — 把 panic 的消息、位置和回溯写到 DCIM/EffectCraft。
fn install_panic_hook() {
    use std::sync::Once;
    static ONCE: Once = Once::new();
    ONCE.call_once(|| {
        let previous = std::panic::take_hook();
        std::panic::set_hook(Box::new(move |info| {
            let dir = std::path::Path::new("/storage/emulated/0/DCIM/EffectCraft");
            let _ = std::fs::create_dir_all(dir);
            let path = dir.join(format!(
                "crash-rust-{}.txt",
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .map(|d| d.as_millis())
                    .unwrap_or(0)
            ));
            let text = format!(
                "{info}\\n\\nBacktrace:\\n{:?}\\n",
                std::backtrace::Backtrace::force_capture()
            );
            if let Ok(mut f) = std::fs::File::create(&path) {
                use std::io::Write;
                let _ = f.write_all(text.as_bytes());
                let _ = f.sync_all();
            }
            previous(info);
        }));
    });
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("panic hook already installed")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, NEW, 1)
    src += FUNC
    path.write_text(src, encoding="utf-8")
    print("panic hook writes crash-rust-*.txt")


if __name__ == "__main__":
    main()
