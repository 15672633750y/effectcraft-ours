#!/usr/bin/env python3
"""Let Android re-create the activity on a rotation instead of handling it in place.

`configChanges` listed every rotation-related change, so Android hands the resize to the running
app: the native window changes size under the graphics surface, and that is where the app dies.
Declaring nothing makes Android do what it does for every ordinary app — finish the activity and
start it again at the new size — which is the path the framework handles properly. The app reopens
the same project; nothing else changes.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ROTATE_RECREATE_V1"
OLD = 'config_changes = "{config_changes}"\n'
NEW = '# EFFECTCRAFT_OURS_ROTATE_RECREATE_V1 — 不声明 configChanges：转屏交给系统重建 Activity\n'


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "lib/build-common.sh"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("rotation already left to the system")
        return
    n = src.count(OLD)
    if n < 1:
        raise SystemExit(f"config_changes anchor: {n}")
    src = src.replace(OLD, NEW)
    path.write_text(src, encoding="utf-8")
    print(f"removed configChanges from {n} activity blocks")


if __name__ == "__main__":
    main()
