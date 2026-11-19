#!/usr/bin/env python3
"""时间线轨道的颜色按品牌来（参考图里快影的轨道是紫/蓝/橙的彩色块）。

图层颜色来自 `tokens.labels`（17 个标签色），所以直接给每套布局换一组标签色：
* 快影   紫 #A855F7 / 蓝 #3B82F6 / 橙 #F97316 / 粉 #EC4899 / 青 #22D3EE
* AM    粉 #F16586 / 绿 #29E59C / 蓝 #6C8CFF / 紫 #B388FF
* Blurrr 青 #03DAC6 / 蓝 #4F9CFF / 紫 #A78BFA
* CapCut 青 #00CAE0 / 蓝 #2F80FF / 紫 #7C5CFF
这样时间线里的条块会像各家那样是彩色胶囊，而不是我们原来的同色系。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_BRAND_TRACK_COLORS_V1"

OLD = '''                self.tokens = t;
                crate::theme::apply_visuals(&ctx, &self.tokens);'''

NEW = '''                self.tokens = t;
                // EFFECTCRAFT_OURS_BRAND_TRACK_COLORS_V1 — 轨道标签色也按品牌
                {
                    let g = egui::Color32::from_rgb;
                    let pal: &[egui::Color32] = match ws.as_str() {
                        "capcut" => &[
                            g(0x00, 0xCA, 0xE0),
                            g(0x2F, 0x80, 0xFF),
                            g(0x7C, 0x5C, 0xFF),
                            g(0x00, 0xB8, 0x8B),
                            g(0xFF, 0x8A, 0x00),
                        ],
                        "kuaishou" => &[
                            g(0xA8, 0x55, 0xF7),
                            g(0x3B, 0x82, 0xF6),
                            g(0xF9, 0x73, 0x16),
                            g(0xEC, 0x48, 0x99),
                            g(0x22, 0xD3, 0xEE),
                        ],
                        "am" | "jianying" => &[
                            g(0xF1, 0x65, 0x86),
                            g(0x29, 0xE5, 0x9C),
                            g(0x6C, 0x8C, 0xFF),
                            g(0xB3, 0x88, 0xFF),
                            g(0xFF, 0xD1, 0x66),
                        ],
                        "blurrr" => &[
                            g(0x03, 0xDA, 0xC6),
                            g(0x4F, 0x9C, 0xFF),
                            g(0xA7, 0x8B, 0xFA),
                            g(0xFF, 0x7A, 0x88),
                            g(0xFF, 0xC0, 0x5B),
                        ],
                        _ => &[],
                    };
                    for (i, c) in pal.iter().enumerate() {
                        if i < self.tokens.labels.len() {
                            self.tokens.labels[i] = *c;
                        }
                    }
                }
                crate::theme::apply_visuals(&ctx, &self.tokens);'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/app/frame.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("brand track colours already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("timeline label colours follow each brand")


if __name__ == "__main__":
    main()
