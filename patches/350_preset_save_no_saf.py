#!/usr/bin/env python3
"""已被 `352_preset_save_dialog.py` 取代（2026-11-19）。

350 当初是「直接写 DCIM/EffectCraft/Presets/<图层名>.ffx」，现在改成弹命名框：
`invoke("anim.savePreset")` 只打开弹窗，真正的写入由弹窗调 `ours.exportPreset`。
远端已经应用过这个文件名，所以保留并改成空操作。
"""
from __future__ import annotations


def main() -> None:
    print("superseded by 352_preset_save_dialog.py")


if __name__ == "__main__":
    main()
