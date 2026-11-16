#!/usr/bin/env python3
"""参数要在拟合之后生效（否则滑块全被拟合覆盖，等于失效）。

The fitted transform replaces `c`, so the sliders applied before it were thrown away: saturation,
brightness, tint and offset darks did nothing. They are now applied *after* the fit, with their
defaults neutral (saturation 1, brightness 1, darks 0, tint white), so the fitted look is the baseline
and the sliders still work on top of it.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PARAMS_AFTER_FIT_V1"

OLD = """                            c = [c[0] * g, c[1] * g, c[2] * g];
                        }
                    }
"""
NEW = """                            c = [c[0] * g, c[1] * g, c[2] * g];
                        }
                        // 拟合之后再套用户参数（默认值中性：饱和 1 / 亮度 1 / 暗部 0 / 色调白）
                        let k_sat2 = (cx.params.f("saturation") as f32).clamp(-4.0, 8.0);
                        let k_bri2 = (cx.params.f("brightness") as f32).clamp(-8.0, 8.0);
                        let k_drk2 = (cx.params.f("offsetDarks") as f32).clamp(-1.0, 1.0);
                        let k_tint2 = cx.params.color("tint");
                        let l2 = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
                        c = [
                            (l2 + (c[0] - l2) * k_sat2) * k_bri2 * k_tint2[0] + k_drk2,
                            (l2 + (c[1] - l2) * k_sat2) * k_bri2 * k_tint2[1] + k_drk2,
                            (l2 + (c[2] - l2) * k_sat2) * k_bri2 * k_tint2[2] + k_drk2,
                        ];
                    }
"""


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("parameters already applied after the fit")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("saturation/brightness/tint/darks apply after the fit")


if __name__ == "__main__":
    main()
