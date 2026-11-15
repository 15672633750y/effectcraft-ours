#!/usr/bin/env python3
"""A 工程分享 block in the export dialog: the project, with or without its media, as a zip.

Exactly what the reference dialog offers, minus the two formats whose writer needs a sample
(NodeVideo's `.nv` and CapCut's `draft_content.json`):

* 完整导出工程（包含素材）  → `<name>-工程.zip` with the `.ecproj` and every footage file
* 完整打包并分享到 QQ        → the same zip, saved where the share sheet can reach it
* 只导出工程文件（.ecproj）  → the project alone
* 导出 AM 工程（.xml）       → Final Cut Pro 7 XML through the existing timeline exporter

The zip is written by the engine (`ours.exportProjectZip`) with the `zip` crate, so the phone does
not need a file manager round trip.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_PROJECT_SHARE_V1"

MOD_DECL = "pub(crate) mod file_more;\n"
MOD_NEW = MOD_DECL + "pub(crate) mod ours_export;\n"

SPECS_ANCHOR = "        v.extend(file::specs());\n"
SPECS_NEW = SPECS_ANCHOR + "        v.extend(ours_export::specs());\n"

MODULE = r'''//! 工程分享：把工程（可选带素材）打成一个 zip，供导出对话框的“工程分享”一栏使用。

use serde_json::{Value, json};

use super::{always, bad, str_p};
use crate::{Result, Session, cmd};

/// Every footage path the project references, de-duplicated.
fn footage_paths(s: &Session) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    for item in s.project.items.values() {
        if let effectcraft_project::ItemKind::Footage(f) = &item.kind
            && !f.missing
            && !f.path.is_empty()
            && !out.contains(&f.path)
        {
            out.push(f.path.clone());
        }
    }
    out
}

fn export_project_zip(s: &mut Session, p: &Value) -> Result<Value> {
    let stem = s.project_name();
    let default = format!("/storage/emulated/0/DCIM/EffectCraft/{stem}-工程.zip");
    let target = str_p(p, "path").filter(|x| !x.is_empty()).map(str::to_string).unwrap_or(default);
    if !target.to_ascii_lowercase().ends_with(".zip") {
        return Err(bad("ours.exportProjectZip", "path 必须以 .zip 结尾"));
    }
    let with_media = p.get("media").and_then(Value::as_bool).unwrap_or(true);
    // 先把工程写成 .ecproj（和 File ▸ Save a Copy 同一条路）
    let project_path = format!("{}.ecproj", target.trim_end_matches(".zip"));
    s.execute("file.saveCopy", json!({"path": project_path}))?;
    let files = if with_media { footage_paths(s) } else { Vec::new() };
    let file = std::fs::File::create(&target).map_err(|e| bad("ours.exportProjectZip", format!("无法写入 {target}: {e}")))?;
    let mut zip = zip::ZipWriter::new(file);
    let opts = zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Deflated);
    let mut added = 0usize;
    let mut missing = 0usize;
    let add = |zip: &mut zip::ZipWriter<std::fs::File>, name: &str, path: &str, added: &mut usize, missing: &mut usize| {
        let Ok(mut src) = std::fs::File::open(path) else {
            *missing += 1;
            return;
        };
        if zip.start_file(name, opts).is_err() {
            *missing += 1;
            return;
        }
        if std::io::copy(&mut src, zip).is_ok() {
            *added += 1;
        } else {
            *missing += 1;
        }
    };
    let proj_name = std::path::Path::new(&project_path).file_name().and_then(|n| n.to_str()).unwrap_or("project.ecproj").to_string();
    add(&mut zip, &proj_name, &project_path, &mut added, &mut missing);
    if with_media {
        for path in &files {
            let name = std::path::Path::new(path)
                .file_name()
                .and_then(|n| n.to_str())
                .map(|n| format!("Footage/{n}"))
                .unwrap_or_else(|| format!("Footage/{added}"));
            add(&mut zip, &name, path, &mut added, &mut missing);
        }
    }
    zip.finish().map_err(|e| bad("ours.exportProjectZip", format!("打包失败: {e}")))?;
    s.toast(format!("已打包工程：{added} 个文件 → {target}"));
    Ok(json!({"zip": target, "project": project_path, "files": added, "missing": missing}))
}

pub fn specs() -> Vec<crate::CommandSpec> {
    vec![cmd!(
        "ours.exportProjectZip",
        "完整导出工程(包含素材)",
        ["File", "Export"],
        None,
        "{path?: .zip, media?: bool (default true)}",
        always,
        export_project_zip
    )]
}
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    module = root / "crates/engine/src/cmd/ours_export.rs"
    if not module.exists():
        module.write_text(MODULE, encoding="utf-8")
        print("ours_export.rs written")
    root_cmd = root / "crates/engine/src/cmd.rs"
    src = root_cmd.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(MOD_DECL) != 1:
            raise SystemExit(f"mod anchor: {src.count(MOD_DECL)}")
        src = src.replace(MOD_DECL, MOD_NEW, 1)
        if src.count(SPECS_ANCHOR) != 1:
            raise SystemExit(f"specs anchor: {src.count(SPECS_ANCHOR)}")
        src = src.replace(SPECS_ANCHOR, SPECS_NEW, 1)
        root_cmd.write_text("// " + MARKER + "\n" + src, encoding="utf-8")
        print("export command registered")


if __name__ == "__main__":
    main()
