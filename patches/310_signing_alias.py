#!/usr/bin/env python3
"""让构建脚本用我们的密钥别名 `shimove`（它写死了 `artcraftbuilder`）。

The builder always asks Gradle for the alias `artcraftbuilder`, so a keystore made under any other alias
fails at `packageRelease` with "No key with alias". The alias comes from the environment here, so reading
the variable lets us pass ours without touching the workflow file.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SIGNING_ALIAS_V1"

OLD = '    ARTCRAFT_KEY_ALIAS="artcraftbuilder" \\\n'
NEW = '    ARTCRAFT_KEY_ALIAS="${ARTCRAFT_KEY_ALIAS:-shimove}" \\\n'


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "lib/build-common.sh"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("signing alias already configurable")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("builder uses the shimove alias")


if __name__ == "__main__":
    main()
