#!/usr/bin/env python3
"""缺素材提示中文化 + 导入结果带上具体条目名。"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZH_AND_DETAILS_V1"

# ① 缺素材文案：保留 "Missing footage" 这个英文关键词（现有 UI 测试断言它），
#    但整个句子改成中文，并给出手机上的实际做法。
FOOT_OLD = '''    (f.missing && !f.path.is_empty() && f.kind != effectcraft_project::FootageKind::Data).then(|| format!("Missing footage: {}. {remedy}", f.path))'''
FOOT_NEW = '''    (f.missing && !f.path.is_empty() && f.kind != effectcraft_project::FootageKind::Data).then(|| {
        format!(
            "缺失素材 Missing footage：{}\\n把同名文件和工程放在一起，或用「文件 › 依赖 › 重新链接素材」。{}",
            f.path, remedy
        )
    })'''
FOOT_CALL_OLD = '''ItemKind::Footage(f) => missing_problem(f, "Use File ▸ Dependencies ▸ Relink Missing Footage or Replace Footage.").or_else(|| self.problem(f)),'''
FOOT_CALL_NEW = '''ItemKind::Footage(f) => missing_problem(f, "（导入 .aep 时会自动在 DCIM/EffectCraft 里按文件名重连。）").or_else(|| self.problem(f)),'''

# ② 导入 toast 带条目名
TOAST_OLD = '''        format!("Imported {name} ({losses} unsupported: {})", res.report.summary())'''
TOAST_NEW = '''        {
            let details: Vec<String> = res
                .report
                .losses
                .iter()
                .flat_map(|l| l.details.iter().take(3).cloned())
                .take(6)
                .collect();
            if details.is_empty() {
                format!("Imported {name} ({losses} unsupported: {})", res.report.summary())
            } else {
                format!(
                    "Imported {name} ({losses} unsupported: {}; {})",
                    res.report.summary(),
                    details.join("; ")
                )
            }
        }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    foot = root / "crates/render/src/footage.rs"
    src = foot.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(FOOT_OLD) != 1:
            raise SystemExit(f"footage anchor: {src.count(FOOT_OLD)}")
        src = src.replace(FOOT_OLD, FOOT_NEW, 1)
        if src.count(FOOT_CALL_OLD) != 1:
            raise SystemExit(f"footage call anchor: {src.count(FOOT_CALL_OLD)}")
        src = src.replace(FOOT_CALL_OLD, FOOT_CALL_NEW, 1)
        foot.write_text(src, encoding="utf-8")
        print("missing-footage notice is Chinese")

    aep = root / "crates/engine/src/cmd/aep.rs"
    src = aep.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(TOAST_OLD) != 1:
            raise SystemExit(f"toast anchor: {src.count(TOAST_OLD)}")
        aep.write_text(src.replace(TOAST_OLD, TOAST_NEW, 1), encoding="utf-8")
        print("import toast lists item names")


if __name__ == "__main__":
    main()
