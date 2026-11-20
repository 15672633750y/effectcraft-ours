#!/usr/bin/env python3
"""1054 的后续：把 420 里那版（用了 ureq 的 typestate 类型名）换成**不依赖类型名**的写法。

ureq 3 的 `RequestBuilder<WithoutBody>` / `<WithBody>` 是两族类型，合并进同一个 match 会 E0308；
而且写死 `ureq::RequestBuilder<ureq::WithoutBody>` 还可能因为类型路径不在 crate 根而编译失败。
现在每个分支各自构造 builder、各自 `.call()` / `.send()`，中间只用 `let mut rb = ...; rb = rb.header(...)`
这种同类型重绑定，四个分支的返回类型一致。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLOUD_REQUEST_ARMS_V2"

OLD = '    let with_auth_get = |rb: ureq::RequestBuilder<ureq::WithoutBody>| {\n        let rb = match &bearer {\n            Some(b) => rb.header("Authorization", b.as_str()),\n            None => rb,\n        };\n        rb.header("Accept", "application/json")\n    };\n    let with_auth_send = |rb: ureq::RequestBuilder<ureq::WithBody>| {\n        let rb = match &bearer {\n            Some(b) => rb.header("Authorization", b.as_str()),\n            None => rb,\n        };\n        rb.header("Accept", "application/json")\n            .header("Content-Type", "application/json")\n    };\n    let payload = body.unwrap_or("");\n    let result = match method {\n        "GET" => with_auth_get(agent.get(&url)).call(),\n        "DELETE" => with_auth_get(agent.delete(&url)).call(),\n        "PUT" => with_auth_send(agent.put(&url)).send(payload),\n        _ => with_auth_send(agent.post(&url)).send(payload),\n    };\n'

NEW = '    let auth = bearer.as_deref();\n    let payload = body.unwrap_or("");\n    let result = match method {\n        "GET" => {\n            let mut rb = agent.get(&url).header("Accept", "application/json");\n            if let Some(b) = auth {\n                rb = rb.header("Authorization", b);\n            }\n            rb.call()\n        }\n        "DELETE" => {\n            let mut rb = agent.delete(&url).header("Accept", "application/json");\n            if let Some(b) = auth {\n                rb = rb.header("Authorization", b);\n            }\n            rb.call()\n        }\n        "PUT" => {\n            let mut rb = agent\n                .put(&url)\n                .header("Accept", "application/json")\n                .header("Content-Type", "application/json");\n            if let Some(b) = auth {\n                rb = rb.header("Authorization", b);\n            }\n            rb.send(payload)\n        }\n        _ => {\n            let mut rb = agent\n                .post(&url)\n                .header("Accept", "application/json")\n                .header("Content-Type", "application/json");\n            if let Some(b) = auth {\n                rb = rb.header("Authorization", b);\n            }\n            rb.send(payload)\n        }\n    };\n\n'


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/ui-egui/src/cloud.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("per-branch request already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {{src.count(OLD)}}")
    out = src.replace(OLD, NEW + "    // EFFECTCRAFT_OURS_CLOUD_REQUEST_ARMS_V2\n", 1)
    path.write_text(out, encoding="utf-8")
    print("request(): GET/DELETE call(), PUT/POST send(), no typestate type names")


if __name__ == "__main__":
    main()
