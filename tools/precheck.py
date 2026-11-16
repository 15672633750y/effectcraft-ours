#!/usr/bin/env python3
"""推送前的静态检查：只查这一路真正打挂过 CI 的几类错误（宁少不误报）。"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def apply_all(tree: Path) -> list[str]:
    fails = []
    env = dict(os.environ, EFFECTCRAFT_DIR=str(tree), ARTCRAFT_DIR=str(ROOT / "builder"))
    for p in sorted((ROOT / "ours-patches").glob("*.py")):
        if p.name in {"make_icon.py"}:
            continue
        r = subprocess.run([sys.executable, str(p)], env=env, capture_output=True, text=True)
        if r.returncode != 0:
            tail = (r.stderr.strip().splitlines() or ["?"])[-1]
            fails.append(f"补丁打不上 {p.name}: {tail}")
    return fails


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="precheck-"))
    tree = tmp / "tree"
    shutil.copytree(ROOT / "repo", tree)
    problems = apply_all(tree)

    def read(rel: str) -> str:
        p = tree / rel
        return p.read_text(errors="ignore") if p.exists() else ""

    vintage = read("crates/effects/src/ffx_vintage.rs")
    if vintage.count("\nfn fitted(") > 1:
        problems.append("ffx_vintage.rs: fn fitted 定义了多次（E0428）")
    frame = read("crates/ui-egui/src/app/frame.rs")
    if frame.count("d.insert_temp(latch_id, latched);") > 1:
        problems.append("frame.rs: 还在用已删除的 latched（E0425）")
    header = read("crates/ui-egui/src/header.rs")
    if "ends[" in header:
        problems.append("header.rs: 还在用已删除的 ends（E0425）")
    anim = read("crates/engine/src/cmd/animation.rs")
    start = anim.find("fn reveal_property")
    if start >= 0:
        seg = anim[start : anim.find("\n}\n", start)]
        body_after_comp = seg.find("let comp = s.project.comp(")
        while body_after_comp >= 0:
            nxt = seg.find("\n    }\n", body_after_comp)
            window = seg[body_after_comp : nxt if nxt > 0 else len(seg)]
            if "frontend(s," in window:
                problems.append("animation.rs: comp 借用期间调用 frontend(s, …)（E0502）")
                break
            body_after_comp = seg.find("let comp = s.project.comp(", body_after_comp + 1)
    shutil.rmtree(tmp, ignore_errors=True)
    if problems:
        print("PRECHECK FAILED")
        for p in dict.fromkeys(problems):
            print(" -", p)
        return 1
    print("PRECHECK OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
