#!/usr/bin/env python3
"""别裁切、别居中：把整张图原样铺满自适应前景。

`_foreground()` 原来会裁到内容边界再缩放到 62% 居中，所以无论怎么改源图的白边/位置，
桌面图标看起来都一样。这里改成整张画布等比铺满，源图的构图（留白、底部贴边）才会真正生效。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ICON_NO_TRIM_V1"

OLD = '''def _foreground(Image, stripped) -> "Image":
    """The artwork trimmed to its bounds and centred on a transparent CANVAS_PX canvas."""
    box = stripped.split()[3].getbbox()
    art = stripped.crop(box) if box else stripped
    scale = min(ARTWORK_PX / art.width, ARTWORK_PX / art.height)
    art = art.resize(
        (max(1, round(art.width * scale)), max(1, round(art.height * scale))),
        Image.LANCZOS,
    )
    canvas = Image.new("RGBA", (CANVAS_PX, CANVAS_PX), (0, 0, 0, 0))
    canvas.paste(art, ((CANVAS_PX - art.width) // 2, (CANVAS_PX - art.height) // 2), art)
    return canvas
'''

NEW = '''def _foreground(Image, stripped) -> "Image":
    """EFFECTCRAFT_OURS_ICON_NO_TRIM_V1 — 整张画布等比铺满，保留源图构图（不裁切、不居中）。"""
    art = stripped.resize((CANVAS_PX, CANVAS_PX), Image.LANCZOS)
    return art
'''


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "lib/app_icons.py"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("icon foreground already un-trimmed")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("adaptive icon keeps the source composition")


if __name__ == "__main__":
    main()
