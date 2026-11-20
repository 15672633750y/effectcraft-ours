#!/usr/bin/env python3
"""云端工程三个客户端 bug 的修复。

1) **删除发的是 POST，不是 DELETE** —— `cloud.rs::request()` 只把 GET 和 PUT 区分开，
   其它方法（含 DELETE）一律走 `agent.post()`。服务端日志"只有 GET 和 POST"就是这么来的。
   现在按方法正确分派，并且 DELETE 不带 body。

2) **上传内容只有 2 字节 `{}`** —— 上传前没有校验文件是否真的落盘。
   新增 `upload_project_from_path()`：后台线程里重试读取（最多 ~3 秒）直到文件 > 100 字节，
   再校验是 JSON 且带 `schema` 字段，否则报"工程还没保存"。

3) **工程名每次都不一样** —— 由 `cloud_clean_name()` 换成 `cloud_project_name()`：
   自动保存/未命名工程一律用固定的「我的工程」，其余用文件名（只去掉 " auto-save N"）。
   这样服务端按名字去重才能生效。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CLOUD_FIX_V1"

# ---------------- cloud.rs
REQ_OLD = '''    let result = if method == "GET" || body.is_none() {
        let req = agent.get(&url);
        let req = match &bearer {
            Some(b) => req.header("Authorization", b.as_str()),
            None => req,
        };
        req.header("Accept", "application/json").call()
    } else {
        let req = if method == "PUT" { agent.put(&url) } else { agent.post(&url) };
        let req = match &bearer {
            Some(b) => req.header("Authorization", b.as_str()),
            None => req,
        };
        req.header("Accept", "application/json")
            .header("Content-Type", "application/json")
            .send(body.unwrap_or(""))
    };'''

REQ_NEW = '''    // EFFECTCRAFT_OURS_CLOUD_FIX_V1 — 按方法正确分派。
    // 原来只要 method != "GET" 就当成 POST，DELETE 因此根本没发出去（服务端只看到 GET/POST）。
    let req = match method {
        "GET" => agent.get(&url),
        "DELETE" => agent.delete(&url),
        "PUT" => agent.put(&url),
        _ => agent.post(&url),
    };
    let req = match &bearer {
        Some(b) => req.header("Authorization", b.as_str()),
        None => req,
    };
    let req = req.header("Accept", "application/json");
    let result = if method == "GET" || method == "DELETE" || body.is_none() {
        req.call()
    } else {
        req.header("Content-Type", "application/json").send(body.unwrap_or(""))
    };'''

DEL_OLD = '''        let path = format!("/projects/{id}");
        match request("DELETE", &path, Some(&token), Some("{}")) {
            Ok((code, text)) => {
                if (200..300).contains(&code) {
                    push(Event::Deleted(id));
                } else {
                    push(Event::CloudFailed(cloud_hint(code, &json_or_null(&text))));
                }
            }
            Err(err) => push(Event::CloudFailed(err)),
        }'''

DEL_NEW = '''        let path = format!("/projects/{id}");
        // DELETE 不带 body：部分网关会丢掉带 body 的 DELETE。
        let reply = request("DELETE", &path, Some(&token), None);
        match reply {
            Ok((code, text)) => {
                // 诊断日志：出问题时能看到完整 URL 与返回码。
                log_line(&format!(
                    "DELETE {}{} -> {} {}",
                    BASE_URL,
                    path,
                    code,
                    text.chars().take(200).collect::<String>()
                ));
                if (200..300).contains(&code) {
                    push(Event::Deleted(id));
                } else {
                    push(Event::CloudFailed(cloud_hint(code, &json_or_null(&text))));
                }
            }
            Err(err) => {
                log_line(&format!("DELETE {}{} -> error {}", BASE_URL, path, err));
                push(Event::CloudFailed(err));
            }
        }'''

UPLOAD_FN_ANCHOR = '''/// 上传：`POST /projects` 拿 id，再 `PUT /projects/:id/content` 发原始字节。'''

UPLOAD_FN_INSERT = '''/// 诊断日志：`DCIM/EffectCraft/cloud.log`（云端出问题时先看这里）。
fn log_line(line: &str) {
    let dir = std::path::Path::new("/storage/emulated/0/DCIM/EffectCraft");
    let _ = std::fs::create_dir_all(dir);
    if let Ok(mut file) = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(dir.join("cloud.log"))
    {
        use std::io::Write as _;
        let _ = writeln!(file, "{line}");
    }
}

/// 从磁盘读取工程并上传：等待落盘（最多约 3 秒）、校验大小与 JSON，再交给 [`upload_project`]。
/// 之前上传读到的是 2 字节 `{}`，服务端那边就存成空工程、下载报 missing field `schema`。
pub fn upload_project_from_path(token: String, name: String, path: String) {
    spawn(move || {
        push(Event::Uploading(true));
        let mut bytes = Vec::new();
        for _ in 0..40 {
            match std::fs::read(&path) {
                Ok(data) if data.len() > 100 => {
                    bytes = data;
                    break;
                }
                _ => std::thread::sleep(std::time::Duration::from_millis(75)),
            }
        }
        if bytes.len() <= 100 {
            push(Event::Uploading(false));
            push(Event::CloudFailed(
                "工程还没保存完成（文件太小），请保存后再上传".to_string(),
            ));
            log_line(&format!("UPLOAD skip: {path} too small"));
            return;
        }
        // 必须是工程 JSON：至少要能解析、且带 schema 字段。
        let parsed: Option<serde_json::Value> = serde_json::from_slice(&bytes).ok();
        let looks_like_project = parsed
            .as_ref()
            .map(|v| v.get("schema").is_some())
            .unwrap_or(false);
        if !looks_like_project {
            push(Event::Uploading(false));
            push(Event::CloudFailed(
                "工程文件内容不对（缺少 schema），可能还没保存完成".to_string(),
            ));
            log_line(&format!("UPLOAD skip: {path} is not project json"));
            return;
        }
        push(Event::Uploading(false));
        log_line(&format!("UPLOAD {path} {} bytes as {name}", bytes.len()));
        upload_bytes_now(token, name, bytes);
    });
}

/// [`upload_project_from_path`] 的后半段：真正发请求（复用现有 `upload_project` 的字节版）。
fn upload_bytes_now(token: String, name: String, bytes: Vec<u8>) {
    upload_project(token, name, bytes);
}

/// 上传：`POST /projects` 拿 id，再 `PUT /projects/:id/content` 发原始字节。'''

# ---------------- account_ui.rs
START_OLD = '''    // 存盘，保证上传的是最新的编辑。
    if let Err(err) = app.session.execute("file.save", serde_json::json!({ "path": path })) {
        set(ui, MESSAGE, format!("保存失败: {err}"));
        return;
    }
    match std::fs::read(&path) {
        Ok(bytes) => {
            let name = std::path::Path::new(&path)
                .file_stem()
                .map(|s| s.to_string_lossy().to_string())
                .filter(|s| !s.is_empty())
                .unwrap_or_else(|| "我的工程".to_string());
            let name = cloud_clean_name(&name);
            set(ui, UPLOADING, true);
            cloud::upload_project(token, name, bytes);
        }
        Err(err) => set(ui, MESSAGE, format!("读工程文件失败: {err}")),
    }
}'''

START_NEW = '''    // 存盘，保证上传的是最新的编辑。
    if let Err(err) = app.session.execute("file.save", serde_json::json!({ "path": path.clone() })) {
        set(ui, MESSAGE, format!("保存失败: {err}"));
        return;
    }
    // EFFECTCRAFT_OURS_CLOUD_FIX_V1 — 交给后台线程等待落盘并校验，避免上传 2 字节的 `{}`
    let name = cloud_project_name(&path);
    set(ui, UPLOADING, true);
    cloud::upload_project_from_path(token, name, path);
}'''

PENDING_OLD = '''            } else {
                match std::fs::read(&target) {
                    Ok(bytes) => {
                        let name = std::path::Path::new(&target)
                            .file_stem()
                            .map(|s| s.to_string_lossy().to_string())
                            .unwrap_or_else(|| "我的工程".to_string());
                        let name = cloud_clean_name(&name);
                        set(ui, UPLOADING, true);
                        cloud::upload_project(token.clone(), name, bytes);
                    }
                    Err(err) => set(ui, MESSAGE, format!("读工程文件失败: {err}")),
                }
            }'''

PENDING_NEW = '''            } else {
                // EFFECTCRAFT_OURS_CLOUD_FIX_V1 — 同样走"等待落盘 + 校验"的路径
                let name = cloud_project_name(&target);
                set(ui, UPLOADING, true);
                cloud::upload_project_from_path(token.clone(), name, target);
            }'''

NAME_OLD = '''/// 工程名：把自动保存叠出来的「auto-save N」全去掉，避免每次上传都变成新工程。
fn cloud_clean_name(stem: &str) -> String {
    let mut out = String::new();
    for part in stem.split(" auto-save") {
        let part = part.trim();
        if part.is_empty() { continue; }
        if !out.is_empty() { out.push(' '); }
        out.push_str(part);
    }
    let trimmed = out.trim().trim_end_matches(|c: char| c.is_ascii_digit()).trim();
    if trimmed.is_empty() { "我的工程".to_string() } else { trimmed.to_string() }
}'''

NAME_NEW = '''/// 工程名：**稳定**优先，服务端才能按名字去重。
///
/// * 自动保存/未命名工程 → 固定「我的工程」
/// * 其余用文件名，只去掉 " auto-save N" 这一段（不再裁数字，避免 "我的工程2024" 被削成 "我的工程"）
fn cloud_project_name(path: &str) -> String {
    let stem = std::path::Path::new(path)
        .file_stem()
        .map(|s| s.to_string_lossy().to_string())
        .unwrap_or_default();
    let lower = stem.to_ascii_lowercase();
    if lower.contains("auto-save") || lower.contains("untitled") || stem.trim().is_empty() {
        return "我的工程".to_string();
    }
    let mut out = String::new();
    for part in stem.split(" auto-save") {
        let part = part.trim();
        if part.is_empty() {
            continue;
        }
        if !out.is_empty() {
            out.push(' ');
        }
        out.push_str(part);
    }
    if out.trim().is_empty() { "我的工程".to_string() } else { out.trim().to_string() }
}'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()

    cloud = root / "crates/ui-egui/src/cloud.rs"
    src = cloud.read_text(encoding="utf-8")
    if MARKER in src:
        print("cloud fixes already present")
        return
    for name, old, new in (
        ("request", REQ_OLD, REQ_NEW),
        ("delete", DEL_OLD, DEL_NEW),
        ("upload fn", UPLOAD_FN_ANCHOR, UPLOAD_FN_INSERT),
    ):
        if src.count(old) != 1:
            raise SystemExit(f"cloud {name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    cloud.write_text(src, encoding="utf-8")

    ui = root / "crates/ui-egui/src/account_ui.rs"
    src = ui.read_text(encoding="utf-8")
    for name, old, new in (
        ("start_upload", START_OLD, START_NEW),
        ("pending save", PENDING_OLD, PENDING_NEW),
        ("name fn", NAME_OLD, NAME_NEW),
    ):
        if src.count(old) != 1:
            raise SystemExit(f"account_ui {name} anchor: {src.count(old)}")
        src = src.replace(old, new, 1)
    ui.write_text(src, encoding="utf-8")
    print("cloud: DELETE dispatch, upload guards, stable name")


if __name__ == "__main__":
    main()
