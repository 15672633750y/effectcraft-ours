#!/usr/bin/env python3
"""Apply every patch to a scratch copy of the sources and catch the mistakes that broke builds.

Run before pushing: python3 tools/preflight.py
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "repo"          # upstream checkout used as the patch target
BUILDER = ROOT / "builder"    # builder checkout (ARTCRAFT_DIR)
PATCHES = ROOT / "ours-patches"
# builder 补丁**必须**在 CI 真正拉到的那份 cleaner builder 上验证：CI 是
# `actions/checkout` 的 v0.5.0 tag，而本地 builder/ 会被补丁改脏 —— 在脏树上验锚点会假通过。
# 这个 tarball 就是那份纯净的 0.5.0。
BUILDER_TARBALL = ROOT / "tmp" / "artcraft-0.5.0.tar.gz"


def extract_builder(dest: Path) -> None:
    """把纯净 builder 解到 `dest`（去掉 tarball 的顶层目录）。

    手动写文件而不是 tarfile.extractall：这个 Python 的 tar 安全过滤器在 FUSE 存储上
    会因为 realpath(ALLOW_MISSING) 抛 FileNotFoundError。
    """
    with tarfile.open(BUILDER_TARBALL) as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            parts = Path(member.name).parts[1:]  # 去掉顶层 artcraft-android-0.5.0/
            if not parts:
                continue
            out = dest.joinpath(*parts)
            out.parent.mkdir(parents=True, exist_ok=True)
            handle = tar.extractfile(member)
            if handle is not None:
                out.write_bytes(handle.read())
STATEMENT_RE = re.compile(r"^\s*(let|if|for|while|match|return|loop|unsafe\s*\{|\.\w+\(|\w+\s*=)")
DOC_RE = re.compile(r"^\s*///")


def apply(env_extra: dict[str, str], want_builder: bool) -> bool:
    scripts = []
    for p in sorted(PATCHES.glob("*.py")):
        if p.name == "make_icon.py":
            continue
        is_builder = "ARTCRAFT_DIR" in p.read_text(encoding="utf-8")
        if is_builder == want_builder:
            scripts.append(p)
    for script in scripts:
        env = dict(os.environ, **env_extra)
        r = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, env=env)
        if r.returncode != 0:
            print(f"FAIL patch {script.name}")
            print((r.stdout + r.stderr).strip()[-800:])
            return False
    return True


def snapshot(root: Path) -> dict[Path, int]:
    out: dict[Path, int] = {}
    for path in list(root.rglob("*.rs")) + list(root.rglob("*.java")):
        if "vendor" in path.parts or "target" in path.parts:
            continue
        try:
            out[path] = hash(path.read_bytes())
        except Exception:
            pass
    return out



def strip_literals(text: str) -> str:
    """Remove string and char literals so brace counting only sees real code."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        # 先跳过注释：注释里的引号（例如 `key="` 这种说明）会破坏下面的字符串状态机，
        # 表现为「括号明明平衡却报 491 != 492」。
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            end = text.find("*/", i + 2)
            i = n if end < 0 else end + 2
            continue
        if c == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    i += 1
                    break
                i += 1
            continue
        if c == "'" and i + 2 < n and (text[i + 1] == "\\" or text[i + 2] == "'"):
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == "'":
                    i += 1
                    break
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def check_rust(root: Path, changed: set[Path]) -> list[str]:
    problems: list[str] = []
    for path in sorted(changed):
        if "vendor" in path.parts or "target" in path.parts or not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        code = strip_literals(text)
        opens, closes = code.count("{"), code.count("}")
        if opens != closes:
            problems.append(f"{path.relative_to(root)}: braces {opens} != {closes}")
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip() == "@Override":
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                nxt = lines[j].strip() if j < len(lines) else ""
                if nxt and not nxt.startswith(("public", "protected", "private", "void")):
                    problems.append(f"{path.relative_to(root)}:{j + 1}: @Override is not followed by a method")
                    break
            if not DOC_RE.match(line):
                continue
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or lines[j].lstrip().startswith("//")):
                j += 1
            if j < len(lines) and STATEMENT_RE.match(lines[j]):
                problems.append(
                    f"{path.relative_to(root)}:{j + 1}: code inserted between a doc comment and its item"
                )
                break
    return problems


def main() -> int:
    if not REPO.is_dir():
        print("repo/ (a pristine upstream checkout) is required")
        return 2
    if not BUILDER_TARBALL.is_file():
        print(f"{BUILDER_TARBALL} is required.")
        print("Builder patches must be checked against the pristine v0.5.0 builder that CI checks")
        print("out - the local builder/ has been modified by earlier patch runs, so anchors that")
        print("only exist there would pass here and fail in CI (SafActivity.java: 2520 vs 1560 lines).")
        return 2
    ok = True
    for target, env_key in ((REPO, "EFFECTCRAFT_DIR"), (None, "ARTCRAFT_DIR")):
        scratch = Path(tempfile.mkdtemp())
        work = scratch / "src"
        if target is None:
            # 纯净 builder：每次从 tarball 还原，绝不用本地 builder/。
            work.mkdir(parents=True)
            extract_builder(work)
        else:
            shutil.copytree(target, work, symlinks=True)
        before = snapshot(work)
        if not apply({env_key: str(work)}, env_key == "ARTCRAFT_DIR"):
            ok = False
            shutil.rmtree(scratch, ignore_errors=True)
            continue
        after = snapshot(work)
        changed = {p for p, h in after.items() if before.get(p) != h}
        problems = check_rust(work, changed)
        if problems:
            ok = False
            print(f"--- structural problems in {env_key} tree")
            for p in problems[:20]:
                print(" ", p)
        shutil.rmtree(scratch, ignore_errors=True)
    print("PREFLIGHT OK" if ok else "PREFLIGHT FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
