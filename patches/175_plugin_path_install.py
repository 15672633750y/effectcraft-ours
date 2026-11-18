#!/usr/bin/env python3
"""已并入 `105_keyframe_buttons.py`（2026-11-19）。

插件面板重排后，拖放区/文件选择本身就是「安装一个指定文件」的入口，175 里那段
「路径输入框 + 安装这个文件」按钮已经不需要了。远端应用过这个文件名，所以保留并改成空操作。
"""
from __future__ import annotations


def main() -> None:
    print("merged into 105_keyframe_buttons.py - the drop zone installs a picked file")


if __name__ == "__main__":
    main()
