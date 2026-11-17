#!/usr/bin/env python3
"""已废止：快捷入口从工具栏最左边挪到了顶部菜单栏「帮助」后面。

用户 2026-11-18 定的方案（HANDOFF 第 13 节第一版）：工具栏最左边不再画任何图片，
「快捷」做成菜单栏里和「文件/编辑/…/帮助」同样式的文字按钮。
新的实现见 `336_quick_menu_button.py`（它同时负责菜单栏按钮与面板开关）。

这个补丁保留文件名（远端已经应用过，删掉会留下无法解释的空档），但不再改任何文件。
"""
from __future__ import annotations


def main() -> None:
    print("superseded by 336_quick_menu_button.py — the shortcut entry moved to the menu bar")


if __name__ == "__main__":
    main()
