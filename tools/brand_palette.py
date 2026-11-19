#!/usr/bin/env python3
"""从 APK 的 resources.arsc 里读出颜色，用来核对/更新各布局的品牌色板。

用法：
    python3 tools/brand_palette.py "/path/to/App.apk" [-n 20]

只读 `resources.arsc`（zip 内的单文件），不需要 apktool / aapt。
输出出现频率最高的 N 个 int 颜色值（#AARRGGBB），用于人工挑选背景 / 文字 / 主色。
"""
from __future__ import annotations

import argparse
import struct
import zipfile
from collections import Counter


def _string_pool(buf: bytes, start: int) -> list[str]:
    if start + 28 > len(buf):
        return []
    str_count, _style_count, flags, strings_start, _styles_start = struct.unpack_from(
        "<IIIII", buf, start + 8
    )
    utf8 = bool(flags & 0x100)
    offsets = struct.unpack_from("<%dI" % str_count, buf, start + 8 + 8)
    base = start + strings_start
    out: list[str] = []
    for off in offsets:
        p = base + off
        if utf8:
            n = buf[p]
            p += 1
            if n & 0x80:
                p += 1
            m = buf[p]
            p += 1
            if m & 0x80:
                m = ((m & 0x7F) << 8) | buf[p]
                p += 1
            out.append(buf[p : p + m].decode("utf-8", "replace"))
        else:
            n = struct.unpack_from("<H", buf, p)[0]
            p += 2
            if n & 0x8000:
                n2 = struct.unpack_from("<H", buf, p)[0]
                p += 2
                n = ((n & 0x7FFF) << 16) | n2
            out.append(buf[p : p + n * 2].decode("utf-16-le", "replace"))
    return out


def colours(apk: str) -> Counter:
    with zipfile.ZipFile(apk) as z:
        data = z.read("resources.arsc")
    _typ, hsize, size = struct.unpack_from("<HHI", data, 0)
    found: Counter = Counter()
    off = hsize
    while off + 8 <= size:
        typ, hs, sz = struct.unpack_from("<HHI", data, off)
        if sz < 8:
            break
        if typ == 0x0001:
            for s in _string_pool(data, off):
                s = s.strip().lower()
                if s.startswith("#") and 4 <= len(s) <= 9:
                    found[s] += 1
        elif typ == 0x0200:
            p = off + hs
            while p + 8 <= off + sz:
                ct, chs, csz = struct.unpack_from("<HHI", data, p)
                if csz < 8:
                    break
                if ct == 0x0201:
                    entry_count, entries_start = struct.unpack_from("<II", data, p + 12)
                    offs = struct.unpack_from("<%dI" % entry_count, data, p + chs)
                    base = p + entries_start
                    for e in offs:
                        if e == 0xFFFFFFFF:
                            continue
                        ep = base + e
                        esize, eflags = struct.unpack_from("<HH", data, ep)
                        if eflags & 0x0001:
                            continue
                        vp = ep + esize
                        dtype = data[vp + 3]
                        dval = struct.unpack_from("<I", data, vp + 4)[0]
                        if dtype in (0x1C, 0x1D, 0x1E, 0x1F):
                            found["#%08x" % dval] += 1
                p += csz
        off += sz
    return found


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("apk")
    ap.add_argument("-n", type=int, default=20)
    args = ap.parse_args()
    found = colours(args.apk)
    print(f"{args.apk}: {len(found)} distinct colours")
    for col, n in found.most_common(args.n):
        print(f"  {col}  x{n}")


if __name__ == "__main__":
    main()
