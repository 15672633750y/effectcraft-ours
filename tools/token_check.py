#!/usr/bin/env python3
"""检查 GitHub 令牌还剩多少天（fine-grained token 的过期时间在响应头里）。

`github-authentication-token-expiration` 是 GitHub 在每个响应里回的过期时间；没有这个头说明是
不过期的令牌（No expiration），这正是长期的用法。
"""
from __future__ import annotations

import datetime as dt
import os
import sys
import urllib.request
from pathlib import Path

TOKEN_FILE = Path("/data/user/0/com.deepseek.harness/files/.ec_token")
REPO = "15672633750y/effectcraft-ours"


def main() -> int:
    token = TOKEN_FILE.read_text().strip()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        exp = r.headers.get("github-authentication-token-expiration")
    if not exp:
        print("token: 不过期（No expiration）✅")
        return 0
    exp = exp.replace(" UTC", " +0000")
    try:
        when = dt.datetime.strptime(exp, "%Y-%m-%d %H:%M:%S %z")
    except ValueError:
        when = dt.datetime.strptime(exp[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.timezone.utc)
    left = (when - dt.datetime.now(dt.timezone.utc)).days
    print(f"token 到期：{when:%Y-%m-%d}，还剩 {left} 天")
    if left <= 7:
        print("⚠️ 快到期了：GitHub → Settings → Developer settings → Fine-grained tokens → Regenerate（选 No expiration）")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
