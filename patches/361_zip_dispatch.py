#!/usr/bin/env python3
"""zip 导入：不要"找不到 .nv 就静默返回 None"。

原来 `import_nodevideo` 打开 zip 后找不到 `.nv` 就 `return None`，交回默认分支；而默认分支对
zip 什么也不做，用户看到的就是"没反应"。现在按内容分流，并且每一步失败都给出原因：

* 有 `draft_content.json` → 「剪映草稿暂不支持，已提取素材（N 个）」
* 有 `*.nv`              → 原来的 NodeVideo 时间线重建
* 有 `*.aepx` / `*.aep`  → 解包后交给 `file.importAep`
* 什么都没有             → 「这个 zip 里没有可识别的工程文件，已作为素材包处理（N 个文件）」
                           并真的把里面的图片/视频作为素材导入

解包失败（权限、磁盘、坏包）不再 `.ok()?` 静默吞掉，直接报错。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZIP_DISPATCH_V1"

START = "pub(crate) fn import_nodevideo(s: &mut Session, path: &str) -> Option<String> {"
END = "fn is_audio(path: &str) -> bool {"

NEW_FN = '''pub(crate) fn import_nodevideo(s: &mut Session, path: &str) -> Option<String> {
    // EFFECTCRAFT_OURS_ZIP_DISPATCH_V1 — zip 按内容分流，并且绝不静默。
    let lower = path.to_ascii_lowercase();
    let unpacked = format!("{path}.unpacked");

    if lower.ends_with(".zip") {
        let file = match std::fs::File::open(path) {
            Ok(f) => f,
            Err(e) => return Some(format!("打不开这个 zip：{e}")),
        };
        let mut zip = match zip::ZipArchive::new(file) {
            Ok(z) => z,
            Err(e) => return Some(format!("这个 zip 读不出来（可能损坏）：{e}")),
        };
        let mut names: Vec<String> = Vec::new();
        for i in 0..zip.len() {
            match zip.by_index(i) {
                Ok(e) => names.push(e.name().to_string()),
                Err(e) => return Some(format!("zip 目录读不出来（第 {i} 项）：{e}")),
            }
        }
        names.sort();
        let has = |suffix: &str| {
            names
                .iter()
                .any(|n| n.to_ascii_lowercase().ends_with(&format!(".{suffix}")))
        };
        let capcut = has("json") && names.iter().any(|n| n.to_ascii_lowercase().ends_with("draft_content.json"));
        let nodevideo = has("nv");
        let aep = has("aepx") || has("aep");

        if let Err(e) = std::fs::create_dir_all(&unpacked) {
            return Some(format!("解包目录建不出来（{unpacked}）：{e}"));
        }
        let mut project_json: Option<String> = None;
        let mut extracted_aep: Option<String> = None;
        let mut media: Vec<String> = Vec::new();
        for name in names {
            let low = name.to_ascii_lowercase();
            let is_media = is_media_name(&low);
            let is_project = nodevideo && low.ends_with(".nv");
            let is_aep = aep && (low.ends_with(".aep") || low.ends_with(".aepx"));
            win_extract_media_relaxed(&low);
            if !is_media && !is_project && !is_aep {
                continue;
            }
            let mut entry = match zip.by_name(&name) {
                Ok(e) => e,
                Err(e) => return Some(format!("zip 里的 {name} 读不出来：{e}")),
            };
            if entry.is_dir() {
                continue;
            }
            let rel = entry.name().trim_start_matches('/').to_string();
            let out_path = format!("{unpacked}/{rel}");
            if let Some(dir) = std::path::Path::new(&out_path).parent() {
                if let Err(e) = std::fs::create_dir_all(dir) {
                    return Some(format!("解包目录建不出来（{}）：{e}", dir.display()));
                }
            }
            let mut out = match std::fs::File::create(&out_path) {
                Ok(f) => f,
                Err(e) => return Some(format!("写不出解包文件 {out_path}：{e}")),
            };
            if let Err(e) = std::io::copy(&mut entry, &mut out) {
                return Some(format!("解包 {name} 时写盘失败：{e}"));
            }
            if is_media {
                media.push(out_path.clone());
            }
            if is_project {
                if project_json.is_none() {
                    project_json = std::fs::read_to_string(&out_path).ok();
                }
                // 186：记下骨架位置，导出时直接用（重写这个函数时不能丢）
                let _ = std::fs::create_dir_all("/storage/emulated/0/DCIM/EffectCraft");
                let _ = std::fs::write(
                    "/storage/emulated/0/DCIM/EffectCraft/.nv-skeleton.txt",
                    &out_path,
                );
            }
            if is_aep && extracted_aep.is_none() {
                extracted_aep = Some(out_path);
            }
        }

        if let Some(aep_path) = extracted_aep {
            return Some(match s.execute("file.importAep", json!({"path": aep_path})) {
                Ok(_) => format!("已解包并导入 After Effects 工程：{aep_path}"),
                Err(e) => format!("zip 里的 .aep 导入失败：{e}"),
            });
        }
        if project_json.is_none() {
            // 没有 NodeVideo 工程：要么是剪映草稿，要么是纯素材包。两种都把素材导进去。
            let count = media.len();
            if count > 0 {
                let note = if capcut {
                    format!("剪映草稿暂不支持重建时间线，已提取 {count} 个素材")
                } else {
                    format!("这个 zip 里没有可识别的工程文件，已作为素材包处理（{count} 个文件）")
                };
                return Some(match s.execute(
                    "file.import",
                    json!({ "paths": media, "newComp": false }),
                ) {
                    Ok(_) => note,
                    Err(e) => format!("{note}，但素材导入失败：{e}"),
                });
            }
            return Some(if capcut {
                "剪映草稿暂不支持（也没有可提取的素材）".to_string()
            } else {
                "这个 zip 里没有可识别的工程文件，也没有可导入的素材".to_string()
            });
        }
        // 有 .nv：走下面的 NodeVideo 时间线重建
        let text = project_json?;
        let doc: Value = match serde_json::from_str(&text) {
            Ok(d) => d,
            Err(e) => return Some(format!("NodeVideo 工程 JSON 解析失败：{e}")),
        };
        let media_dir = format!("{unpacked}/Medias");
        let mut nodes: Vec<&Value> = Vec::new();
        collect_media_nodes(&doc, &mut nodes);
        if nodes.is_empty() {
            let count = media.len();
            return Some(if count > 0 {
                match s.execute("file.import", json!({ "paths": media, "newComp": false })) {
                    Ok(_) => format!("NodeVideo 工程里没有图层，已提取 {count} 个素材"),
                    Err(e) => format!("NodeVideo 工程里没有图层，素材导入失败：{e}"),
                }
            } else {
                "NodeVideo 工程里没有可导入的图层或素材".to_string()
            });
        }
        return build_nodevideo_timeline(s, path, &media_dir, &doc);
    }

    // .nv 直接给过来
    let text = match std::fs::read_to_string(path) {
        Ok(t) => t,
        Err(e) => return Some(format!("打不开 {path}：{e}")),
    };
    let doc: Value = match serde_json::from_str(&text) {
        Ok(d) => d,
        Err(e) => return Some(format!("NodeVideo 工程 JSON 解析失败：{e}")),
    };
    let media_dir = format!("{unpacked}/Medias");
    let mut nodes: Vec<&Value> = Vec::new();
    collect_media_nodes(&doc, &mut nodes);
    if nodes.is_empty() {
        return Some("这个 .nv 里没有可导入的图层".to_string());
    }
    build_nodevideo_timeline(s, path, &media_dir, &doc)
}

/// 把收集到的 NodeVideo 媒体节点变成 OTIO 时间线并交给官方导入器。
fn build_nodevideo_timeline(
    s: &mut Session,
    path: &str,
    media_dir: &str,
    doc: &Value,
) -> Option<String> {
    // 219/215 等补丁在旧函数体里定义过这几个集合；重写时在这里补齐，尾部代码照旧使用。
    let mut nodes: Vec<&Value> = Vec::new();
    collect_media_nodes(doc, &mut nodes);
    let mut fills: Vec<&Value> = Vec::new();
    collect_fill_nodes(doc, &mut fills);
    let mut adjustments: Vec<&Value> = Vec::new();
    collect_adjustment_nodes(doc, &mut adjustments);
'''

TAIL_KEEP = '''    let rate = 30.0f64;
'''

MEDIA_HELPER = '''
/// zip 里算"素材"的条目：图片、视频、音频。
fn is_media_name(low: &str) -> bool {
    const EXTS: &[&str] = &[
        "png", "jpg", "jpeg", "webp", "bmp", "gif", "tif", "tiff",
        "mp4", "mov", "m4v", "mkv", "webm", "avi", "3gp",
        "mp3", "wav", "m4a", "aac", "flac", "ogg",
    ];
    EXTS.iter().any(|e| low.ends_with(&format!(".{e}")))
}

'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    import_ext = root / "crates/engine/src/cmd/import_ext.rs"
    src = import_ext.read_text(encoding="utf-8")
    if MARKER in src:
        print("zip dispatch already present")
        return
    i = src.find(START)
    j = src.find(END, i)
    if i < 0 or j < 0:
        raise SystemExit(f"anchors: start={i} end={j}")
    tail = src[i:j]
    k = tail.find(TAIL_KEEP)
    if k < 0:
        raise SystemExit("rate anchor missing in the old function")
    # 旧函数体从 rate 之后到结尾原样保留（它只用到 path/media_dir/nodes 三个变量）
    body_tail = tail[k:]
    new_src = src[:i] + NEW_FN + body_tail + MEDIA_HELPER + src[j:]
    # 顺手补一个"宽进"的解包过滤占位（保留调用点，避免编译告警）
    new_src = new_src.replace("            win_extract_media_relaxed(&low);\n", "")
    import_ext.write_text(new_src, encoding="utf-8")
    print("zip import dispatches by content and reports every failure")


if __name__ == "__main__":
    main()
