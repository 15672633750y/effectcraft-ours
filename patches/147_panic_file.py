#!/usr/bin/env python3
"""Write a panic to a file the phone's file manager can show.

The session log lives under `Android/data/<package>/files/config/Logs`, which scoped storage hides
from most file managers, so a crash report was hard to hand over. The hook keeps logging (that is
what Help ▸ Enable Logging reads) and also drops a short text file in `DCIM/EffectCraft`, next to
the renders. Writing there can fail without broad storage access; that is ignored — the log line
still exists.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PANIC_FILE_V1"

OLD = """        log::error!("panic: {info}");
        previous(info);
"""
NEW = """        log::error!("panic: {info}");
        // EFFECTCRAFT_OURS_PANIC_FILE_V1 — 手机文件管理里能直接看到、能发出去的崩溃记录
        {
            let stamp = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_secs())
                .unwrap_or(0);
            let text = format!("EffectCraft 崩溃\\n\\n{info}\\n");
            for dir in ["/storage/emulated/0/DCIM/EffectCraft", "/storage/emulated/0/Download"] {
                let dir = std::path::Path::new(dir);
                if dir.is_dir() && std::fs::write(dir.join(format!("effectcraft-crash-{stamp}.txt")), &text).is_ok() {
                    break;
                }
            }
        }
        previous(info);
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/system/logging.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("panic file already installed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: expected 1, found {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("panics also land in DCIM/EffectCraft")


if __name__ == "__main__":
    main()
