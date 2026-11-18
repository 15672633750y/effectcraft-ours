#!/usr/bin/env python3
"""已并入 `341_account_ui.py`（2026-11-18）。

头像本地文件（`<config>/avatar.png`）、`paint_texture`/`paint_avatar` 这些都已经搬进 341，
因为资料卡整体重写（性别三选一、生日调节器、签名多行）需要它们同处一个文件。
远端已经应用过这个文件名，所以保留并改成空操作，避免出现「改了一半」的中间状态。
"""
from __future__ import annotations


def main() -> None:
    print("merged into 341_account_ui.py - avatar support lives there now")


if __name__ == "__main__":
    main()
