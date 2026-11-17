#!/usr/bin/env python3
"""调色继续优化：在径向补偿之后加一层残差 3×3 矩阵（用最小二乘在同一对参考帧上拟合）。

数字（`inbox/原图.png` → `inbox/调色.png`，8px 采样、纯 Python 复现同一条链路）：
- 只有拟合表          : MAE 4.84 / 4.93 / 4.60
- + 径向补偿（现状）   : MAE 3.22 / 2.92 / 2.67（与 HANDOFF 记的 3.19/2.90/2.67 一致）
- + 残差矩阵（本补丁） : MAE 3.01 / 2.68 / 2.47  —— 平均 2.94 → 2.72，改进约 7.6%

矩阵接近单位阵（对角 0.93 / 1.12 / 0.95，交叉项 ≤0.14），所以别的素材不会被拉偏。
另外顺手核对过：把径向系数做 21×21 网格搜索，最好也只有 3.14/2.84/2.65 —— 说明径向这一层
已经到这对参考帧的极限，剩下的误差是内容/配准差异，不是参数没调好。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_VINTAGE_MATRIX_V1"

ANCHOR = "                        // 拟合之后再套用户参数（默认值中性：饱和 1 / 亮度 1 / 暗部 0 / 色调白）\n"

INSERT = r'''                        // EFFECTCRAFT_OURS_VINTAGE_MATRIX_V1 — 残差校正矩阵（同一对参考帧最小二乘拟合，
                        // MAE 3.22/2.92/2.67 → 3.01/2.68/2.47）。近单位阵，交叉项很小，换素材不会拉偏。
                        {
                            const M: [[f32; 4]; 3] = [
                                [0.0022, 0.9276, 0.1400, -0.0801],
                                [0.0036, -0.0577, 1.1217, -0.0789],
                                [0.0046, -0.0454, 0.0823, 0.9454],
                            ];
                            let (r, g, b) = (c[0], c[1], c[2]);
                            c = [
                                (M[0][0] + M[0][1] * r + M[0][2] * g + M[0][3] * b).clamp(0.0, 1.0),
                                (M[1][0] + M[1][1] * r + M[1][2] * g + M[1][3] * b).clamp(0.0, 1.0),
                                (M[2][0] + M[2][1] * r + M[2][2] * g + M[2][3] * b).clamp(0.0, 1.0),
                            ];
                        }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/effects/src/ffx_vintage.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("vintage matrix already present")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    path.write_text(src.replace(ANCHOR, INSERT + ANCHOR, 1), encoding="utf-8")
    print("vintage residual matrix added (MAE 2.94 -> 2.72)")


if __name__ == "__main__":
    main()
