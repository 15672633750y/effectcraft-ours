    // 变换关键帧：按图层名对上刚导入的图层，再逐帧加键
    let mut keyed = 0usize;
    let mut skipped = 0usize;
    if let Some(cid) = s.active_comp_id() {
        let layers: Vec<(String, u64)> = s
            .project
            .comp(cid)
            .map(|c| c.layers.iter().map(|l| (l.name.clone(), l.id.0)).collect())
            .unwrap_or_default();
        for node in &all_nodes {
            let Some(nname) = node.get("Name").and_then(Value::as_str) else { continue };
            let Some((_, lid)) = layers.iter().find(|(n, _)| n == nname) else { continue };
            for (_param, path, keys) in transform_keys(node) {
                for (t, v) in keys {
                    if s.execute("prop.addKey", json!({"layer": lid, "path": path, "time": t, "timeBase": "comp", "value": v})).is_ok() {
                        keyed += 1;
                    } else {
                        skipped += 1;
                    }
                }
            }
        }
    }
