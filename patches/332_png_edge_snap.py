#!/usr/bin/env python3
"""已取消（用户 2026-11-18）：PNG 拖动贴边不再做。

远端已经应用过这个文件，所以保留文件名并改成空操作；删掉它会让远端残留一份仍在生效的旧逻辑。
"""
from __future__ import annotations


def main() -> None:
    print("cancelled by the user — PNG drag edge snapping is no longer applied")


if __name__ == "__main__":
    main()
