#!/usr/bin/env python3
"""导出 NodeVideo 工程包：拿一个现成的 `.nv` 当骨架，克隆它的节点结构。

NodeVideo's layers carry a half-megabyte parameter tree each, so a generated file has to reuse a
real one. The exporter looks for any `.nv` already on the phone — what our own importer unpacked
next to a `.zip`, or one the user exported from NodeVideo — and clones it:

* the root node keeps its `Props`, its duration is set to the comp's
* every media layer clones a media node's `Props`/`TexSource`, with the asset paths, size, duration
  and `TimeLine` replaced
* the media files ride along in `Medias/` inside the zip

Without a template it refuses with a message instead of writing a file NodeVideo cannot open.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_NV_EXPORT_V1"

SPEC_OLD = '''pub fn specs() -> Vec<crate::CommandSpec> {
    vec![cmd!(
        "ours.exportProjectZip",
'''
SPEC_NEW = '''pub fn specs() -> Vec<crate::CommandSpec> {
    vec![cmd!(
        "ours.exportNodeVideo",
        "导出 NodeVideo 工程包(.zip)",
        ["File", "Export"],
        None,
        "{path?: .zip}",
        |s: &Session, _| !s.project.items.is_empty(),
        export_nv
    ), cmd!(
        "ours.exportProjectZip",
'''

MODULE = r'''

// ---------------------------------------------------------------- NodeVideo 导出

/// 找一份现成的 `.nv` 当骨架：我们导入时解包出来的，或用户从 NodeVideo 导出的。
fn find_nv_template() -> Option<(String, serde_json::Value)> {
    let roots = [
        "/storage/emulated/0/DCIM/EffectCraft",
        "/storage/emulated/0/Download",
        "/storage/emulated/0/work/effectcraft/inbox",
    ];
    let mut candidates: Vec<String> = Vec::new();
    for root in roots {
        let Ok(entries) = std::fs::read_dir(root) else { continue };
        for e in entries.flatten() {
            let p = e.path();
            let name = p.file_name().and_then(|n| n.to_str()).unwrap_or("");
            if name.to_ascii_lowercase().ends_with(".nv") {
                candidates.push(p.to_string_lossy().to_string());
            } else if name.ends_with(".unpacked") {
                if let Ok(inner) = std::fs::read_dir(&p) {
                    for f in inner.flatten() {
                        if f.path().extension().is_some_and(|x| x.eq_ignore_ascii_case("nv")) {
                            candidates.push(f.path().to_string_lossy().to_string());
                        }
                    }
                }
            }
        }
    }
    for path in candidates {
        if let Ok(text) = std::fs::read_to_string(&path)
            && let Ok(v) = serde_json::from_str::<serde_json::Value>(&text)
            && v.get("ChildList").is_some()
        {
            return Some((path, v));
        }
    }
    None
}

fn export_nv(s: &mut Session, p: &Value) -> Result<Value> {
    let Some((template_path, template)) = find_nv_template() else {
        return Err(bad(
            "ours.exportNodeVideo",
            "需要一个 NodeVideo 工程做骨架：先在 NodeVideo 里导出过一次工程（.zip），再把它导入 EffectCraft 一次",
        ));
    };
    let Some(cid) = s.active_comp_id() else { return Err(bad("ours.exportNodeVideo", "没有打开的合成")) };
    let Some(comp) = s.project.comp(cid).cloned() else { return Err(bad("ours.exportNodeVideo", "合成不存在")) };
    let name = s.project.item(cid).map(|i| i.name.clone()).unwrap_or_else(|| "NodeVideo".into());
    let default = format!("/storage/emulated/0/DCIM/EffectCraft/{name}-NV工程.zip");
    let target = str_p(p, "path").filter(|x| !x.is_empty()).map(str::to_string).unwrap_or(default);
    if !target.to_ascii_lowercase().ends_with(".zip") {
        return Err(bad("ours.exportNodeVideo", "path 必须以 .zip 结尾"));
    }
    // 模板里的“媒体节点”和“根节点”
    let mut media_template: Option<serde_json::Value> = None;
    fn walk(n: &serde_json::Value, out: &mut Option<serde_json::Value>) {
        if out.is_none()
            && n.get("$type").and_then(serde_json::Value::as_str).is_some_and(|t| t.contains("NodeMediaVideo") || t.contains("NodeMediaImage"))
        {
            *out = Some(n.clone());
            return;
        }
        if let Some(children) = n.get("ChildList").and_then(serde_json::Value::as_array) {
            for c in children {
                walk(c, out);
            }
        }
    }
    walk(&template, &mut media_template);
    let Some(node_template) = media_template else {
        return Err(bad("ours.exportNodeVideo", format!("{template_path} 里没有媒体节点，换一个骨架")));
    };
    let root_template = template.clone();
    let dur = comp.duration.seconds().max(0.1);
    let mut children: Vec<serde_json::Value> = Vec::new();
    let mut media_files: Vec<(String, String)> = Vec::new();
    let mut next_id: i64 = 100_000;
    for layer in comp.layers.iter() {
        let effectcraft_project::LayerSource::Footage(item) = layer.source else { continue };
        let Some(item_obj) = s.project.item(item) else { continue };
        let effectcraft_project::ItemKind::Footage(f) = &item_obj.kind else { continue };
        if f.missing || f.path.is_empty() {
            continue;
        }
        let mut node = node_template.clone();
        next_id += 10;
        let id = next_id.to_string();
        let vis = (layer.out_point - layer.in_point).seconds().max(0.05);
        let src_in = (layer.in_point - layer.start_time).seconds().max(0.0);
        node["$id"] = json!(id);
        node["Name"] = json!(layer.name);
        node["Hided"] = json!(!layer.switches.video);
        node["UID"] = json!(format!("{}-{:x}", id, next_id));
        node["TimeLine"] = json!({
            "$id": id,
            "Pos": layer.start_time.seconds(),
            "Start": src_in,
            "End": src_in + vis,
            "Duration": src_in + vis,
            "Stretch": if layer.stretch > 1.0 { 100.0 / layer.stretch } else { 1.0 },
            "Trimed": false
        });
        for asset in ["AssetVideo", "AssetAudio", "AssetImage"] {
            if let Some(a) = node.get_mut(asset).and_then(serde_json::Value::as_object_mut) {
                a.insert("AbsolutePath".into(), json!(f.path));
                if let Some(w) = f.width { a.insert("Width".into(), json!(w)); }
                if let Some(h) = f.height { a.insert("Height".into(), json!(h)); }
                a.insert("Duration".into(), json!(f.duration.unwrap_or(dur)));
                a.insert("LinkBroken".into(), json!(false));
            }
        }
        if let Some(tex) = node.get_mut("TexSource").and_then(serde_json::Value::as_object_mut) {
            tex.insert("Node".into(), json!({"$ref": id}));
        }
        let file_name = std::path::Path::new(&f.path).file_name().and_then(|n| n.to_str()).unwrap_or("media").to_string();
        if !media_files.iter().any(|(n, _)| *n == file_name) {
            media_files.push((file_name.clone(), f.path.clone()));
        }
        children.push(node);
    }
    if children.is_empty() {
        return Err(bad("ours.exportNodeVideo", "这个合成里没有可导出的媒体图层"));
    }
    let mut root = root_template;
    root["ChildList"] = json!(children);
    if let Some(tl) = root.get_mut("TimeLine").and_then(serde_json::Value::as_object_mut) {
        tl.insert("Pos".into(), json!(0.0));
        tl.insert("Start".into(), json!(0.0));
        tl.insert("End".into(), json!(dur));
        tl.insert("Duration".into(), json!(dur));
        tl.insert("Stretch".into(), json!(1.0));
    }
    root["FixedDuration"] = json!(dur);
    let file = std::fs::File::create(&target).map_err(|e| bad("ours.exportNodeVideo", format!("无法写入 {target}: {e}")))?;
    let mut zip = zip::ZipWriter::new(file);
    let opts = zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Deflated);
    let nv_name = format!("{name}.nv");
    zip.start_file(&nv_name, opts).map_err(|e| bad("ours.exportNodeVideo", format!("打包失败: {e}")))?;
    use std::io::Write as _;
    zip.write_all(root.to_string().as_bytes()).map_err(|e| bad("ours.exportNodeVideo", format!("打包失败: {e}")))?;
    let mut missing = 0usize;
    let mut packed = 0usize;
    for (file_name, path) in &media_files {
        let Ok(mut src) = std::fs::File::open(path) else {
            missing += 1;
            continue;
        };
        if zip.start_file(format!("Medias/{file_name}"), opts).is_err() {
            missing += 1;
            continue;
        }
        if std::io::copy(&mut src, &mut zip).is_ok() {
            packed += 1;
        }
    }
    zip.finish().map_err(|e| bad("ours.exportNodeVideo", format!("打包失败: {e}")))?;
    s.toast(format!("已导出 NodeVideo 工程：{packed} 个素材 → {target}"));
    Ok(json!({"zip": target, "media": packed, "missing": missing, "template": template_path}))
}
'''

BUTTON_OLD = '''            if ui.button("导出 NodeVideo 工程包（.zip）").clicked() {
                app.ui.status = "暂不支持：需要 NodeVideo 工程样本才能写出可打开的 .nv".into();
            }'''
BUTTON_NEW = '''            if ui.button("导出 NodeVideo 工程包（.zip）").clicked() {
                match crate::menus::invoke(app, ui.ctx(), "ours.exportNodeVideo", serde_json::json!({})) {
                    Ok(r) => {
                        let zip = r.get("zip").and_then(|v| v.as_str()).unwrap_or("").to_string();
                        app.ui.status = format!("已导出 NodeVideo 工程：{zip}");
                    }
                    Err(e) => app.ui.status = format!("导出失败：{e}"),
                }
            }'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    module = root / "crates/engine/src/cmd/ours_export.rs"
    src = module.read_text(encoding="utf-8")
    if MARKER not in src:
        if src.count(SPEC_OLD) != 1:
            raise SystemExit(f"spec anchor: {src.count(SPEC_OLD)}")
        src = src.replace(SPEC_OLD, SPEC_NEW, 1)
        src += MODULE
        module.write_text(src, encoding="utf-8")
        print("NodeVideo export command added")
    ui = [p for p in (root / "crates/ui-egui/src").rglob("*.rs") if BUTTON_OLD in p.read_text(encoding="utf-8", errors="ignore")]
    if not ui:
        print("dialog button not found; command only")
        return
    path = ui[0]
    src = path.read_text(encoding="utf-8")
    if "ours.exportNodeVideo" in src:
        print("NodeVideo button already wired")
        return
    path.write_text(src.replace(BUTTON_OLD, BUTTON_NEW, 1), encoding="utf-8")
    print("导出 NodeVideo button wired")


if __name__ == "__main__":
    main()
