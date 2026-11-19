#!/usr/bin/env python3
"""zip 导入：把"找不到 .nv 就静默 return None"换成按内容分流。

**只替换这一处早退**，函数体其它部分（`fills`/`adjustments`/`all_nodes` 等由 219/224 注入的集合、
尾部的时间线组装）一律不动——之前整段搬函数连续两轮漏变量，编译不过。

分流：
* 有 `.aep/.aepx` → 解包后交给 `file.importAep`
* 有 `.nv`        → 保持原有 NodeVideo 流程
* 有 `draft_content.json` → 「剪映草稿暂不支持重建时间线，已提取 N 个素材」
* 其它           → 「这个 zip 里没有可识别的工程文件，已作为素材包处理（N 个文件）」
并且解包失败一律报错，不再 `.ok()?` 静默。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ZIP_DISPATCH_V1"

OLD = '''        if !names.iter().any(|n| n.to_ascii_lowercase().ends_with(".nv")) {
            return None; // 不是 NodeVideo 工程，交给后面的分支
        }
'''

NEW = '''        // EFFECTCRAFT_OURS_ZIP_DISPATCH_V1 — 找不到 .nv 时不要静默：按内容分流并给出结果。
        let has_nv = names.iter().any(|n| n.to_ascii_lowercase().ends_with(".nv"));
        if !has_nv {
            let has_aep = names
                .iter()
                .any(|n| {
                    let l = n.to_ascii_lowercase();
                    l.ends_with(".aep") || l.ends_with(".aepx")
                });
            let has_capcut = names
                .iter()
                .any(|n| n.to_ascii_lowercase().ends_with("draft_content.json"));
            if let Err(e) = std::fs::create_dir_all(&unpacked) {
                return Some(format!("解包目录建不出来（{unpacked}）：{e}"));
            }
            let mut media: Vec<String> = Vec::new();
            let mut aep_path: Option<String> = None;
            for name in &names {
                let low = name.to_ascii_lowercase();
                let is_media = ["png", "jpg", "jpeg", "webp", "bmp", "gif", "tif", "tiff", "mp4", "mov", "m4v", "mkv", "webm", "avi", "3gp", "mp3", "wav", "m4a", "aac", "flac", "ogg"]
                    .iter()
                    .any(|ext| low.ends_with(&format!(".{ext}")));
                let is_aep = has_aep && (low.ends_with(".aep") || low.ends_with(".aepx"));
                if !is_media && !is_aep {
                    continue;
                }
                let mut entry = match zip.by_name(name) {
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
                if is_aep && aep_path.is_none() {
                    aep_path = Some(out_path);
                }
            }
            if let Some(aep) = aep_path {
                return Some(match s.execute("file.importAep", json!({"path": aep})) {
                    Ok(_) => format!("已解包并导入 After Effects 工程：{aep}"),
                    Err(e) => format!("zip 里的 .aep 导入失败：{e}"),
                });
            }
            let count = media.len();
            if count > 0 {
                let note = if has_capcut {
                    format!("剪映草稿暂不支持重建时间线，已提取 {count} 个素材")
                } else {
                    format!("这个 zip 里没有可识别的工程文件，已作为素材包处理（{count} 个文件）")
                };
                return Some(match s.execute("file.import", json!({ "paths": media, "newComp": false })) {
                    Ok(_) => note,
                    Err(e) => format!("{note}，但素材导入失败：{e}"),
                });
            }
            return Some(if has_capcut {
                "剪映草稿暂不支持（也没有可提取的素材）".to_string()
            } else {
                "这个 zip 里没有可识别的工程文件，也没有可导入的素材".to_string()
            });
        }
'''


def main() -> None:
    root = Path(os.environ["EFFECTCRAFT_DIR"]).resolve()
    path = root / "crates/engine/src/cmd/import_ext.rs"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("zip dispatch already present")
        return
    if src.count(OLD) != 1:
        raise SystemExit(f"anchor: {src.count(OLD)}")
    path.write_text(src.replace(OLD, NEW, 1), encoding="utf-8")
    print("zip dispatches by content, nothing else touched")


if __name__ == "__main__":
    main()
