#!/usr/bin/env python3
"""1054/1055 的最终修法：把 418 插入的 `request()` 分派块换成**按方法各自构造**的写法。

1054 的编译错误：`agent.get/delete` 返回 `RequestBuilder<WithoutBody>`，`agent.put/post` 返回
`RequestBuilder<WithBody>`，两者不能塞进同一个 `let req = match ...`（E0308）。

本补丁直接锚定 418 插入的那段（不依赖任何中间版本），四个分支各自 `.call()` / `.send()`，
中间只用同类型重绑定，因此也不需要写出 ureq 的 typestate 类型名。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLOUD_REQUEST_ARMS_V2"

OLD = '    // EFFECTCRAFT_OURS_CLOUD_FIX_V1 — 按方法正确分派。\n    // 原来只要 method != "GET" 就当成 POST，DELETE 因此根本没发出去（服务端只看到 GET/POST）。\n    let req = match method {\n        "GET" => agent.get(&url),\n        "DELETE" => agent.delete(&url),\n        "PUT" => agent.put(&url),\n        _ => agent.post(&url),\n    };\n    let req = match &bearer {\n        Some(b) => req.header("Authorization", b.as_str()),\n        None => req,\n    };\n    let req = req.header("Accept", "application/json");\n    let result = if method == "GET" || method == "DELETE" || body.is_none() {\n        req.call()\n    } else {\n        req.header("Content-Type", "application/json").send(body.unwrap_or(""))\n    };\n'

NEW = '    // EFFECTCRAFT_OURS_CLOUD_REQUEST_ARMS_V2 — 按方法正确分派。\n    // 原来只要 method != "GET" 就当成 POST，DELETE 根本没发出去（服务端只看到 GET/POST）。\n    // ureq 3 里 GET/DELETE 是 RequestBuilder<WithoutBody>（.call()），PUT/POST 是\n    // RequestBuilder<WithBody>（.send()）；两族类型不同，所以每个分支各自构造，\n    // 也不写具体 typestate 类型名，避免依赖 ureq 的内部类型路径。\n    let auth = bearer.as_deref();\n    let payload = body.unwrap_or("");\n    let result = match method {\n        "GET" => {\n            let mut rb = agent.get(&url).header("Accept", "application/json");\n            if let Some(b) = auth {\n                rb = rb.header("Authorization", b);\n            }\n            rb.call()\n        }\n        "DELETE" => {\n            let mut rb = agent.delete(&url).header("Accept", "application/json");\n            if let Some(b) = auth {\n                rb = rb.header("Authorization", b);\n            }\n            rb.call()\n        }\n        "PUT" => {\n            let mut rb = agent\n                .put(&url)\n                .header("Accept", "application/json")\n                .header("Content-Type", "application/json");\n            if let Some(b) = auth {\n                rb = rb.header("Authorization", b);\n            }\n            rb.send(payload)\n        }\n        _ => {\n            let mut rb = agent\n                .post(&url)\n                .header("Accept", "application/json")\n                .header("Content-Type", "application/json");\n            if let Some(b) = auth {\n                rb = rb.header("Authorization", b);\n            }\n            rb.send(payload)\n        }\n    };\n\n'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/cloud.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("per-branch request already present")
        return
    n = src.count(OLD)
    if n != 1:
        raise SystemExit(f"anchor count {n}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("request(): GET/DELETE call(), PUT/POST send(), branches built separately")


if __name__ == "__main__":
    main()
