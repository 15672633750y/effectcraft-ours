
/// 变换关键帧：NodeVideo 把二维参数拆成 `Params[0]`（X）、`Params[1]`（Y）两个 PFloat，
/// 每个 PFloat 自己带 KeyFrames；位置/锚点是 0–1 归一化，缩放 1.0 = 100%。
fn transform_keys(node: &Value, w: f64, h: f64) -> Vec<(&'static str, Vec<(f64, Value)>)> {
    let mut out: Vec<(&'static str, Vec<(f64, Value)>)> = Vec::new();
    let Some(props) = node.get("Props").and_then(Value::as_array) else { return out };
    let mut params: Option<&Value> = None;
    for p in props {
        let Some(dict) = p.get("Params") else { continue };
        if dict.get("_position").is_some() {
            params = Some(dict);
            break;
        }
    }
    let Some(params) = params else { return out };

    let axis_keys = |name: &str| -> Option<Vec<(f64, f64)>> {
        let base = params.get(name)?;
        // 标量参数自己带 KeyFrames；二维参数在 Params[i] 里
        if let Some(kf) = base.get("KeyFrames").and_then(Value::as_array) {
            if !kf.is_empty() {
                let mut v = Vec::new();
                for k in kf {
                    if let (Some(t), Some(y)) = (k.get("_x").and_then(Value::as_f64), k.get("_y").and_then(Value::as_f64)) {
                        v.push((t, y));
                    }
                }
                return Some(v);
            }
        }
        None
    };

    let axes = |name: &str| -> Option<(Vec<(f64, f64)>, Vec<(f64, f64)>)> {
        let base = params.get(name)?;
        let comps = base.get("Params").and_then(Value::as_array)?;
        let mut out: Vec<Vec<(f64, f64)>> = Vec::new();
        for c in comps.iter().take(2) {
            let kf = c.get("KeyFrames").and_then(Value::as_array)?;
            let mut v = Vec::new();
            for k in kf {
                if let (Some(t), Some(y)) = (k.get("_x").and_then(Value::as_f64), k.get("_y").and_then(Value::as_f64)) {
                    v.push((t, y));
                }
            }
            out.push(v);
        }
        if out.len() == 2 && (!out[0].is_empty() || !out[1].is_empty()) {
            Some((out[0].clone(), out[1].clone()))
        } else {
            None
        }
    };

    let value_at = |keys: &[(f64, f64)], t: f64| -> f64 {
        let mut v = keys.first().map(|k| k.1).unwrap_or(0.0);
        for (kt, kv) in keys {
            if *kt <= t + 1e-9 {
                v = *kv;
            }
        }
        v
    };

    if let Some((kx, ky)) = axes("_position") {
        let mut times: Vec<f64> = kx.iter().chain(ky.iter()).map(|k| k.0).collect();
        times.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        times.dedup_by(|a, b| (*a - *b).abs() < 1e-6);
        let keys: Vec<(f64, Value)> = times
            .into_iter()
            .map(|t| (t, json!([value_at(&kx, t) * w, value_at(&ky, t) * h])))
            .collect();
        if !keys.is_empty() {
            out.push(("transform/position", keys));
        }
    }
    if let Some((kx, ky)) = axes("_scale") {
        let mut times: Vec<f64> = kx.iter().chain(ky.iter()).map(|k| k.0).collect();
        times.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        times.dedup_by(|a, b| (*a - *b).abs() < 1e-6);
        let keys: Vec<(f64, Value)> = times
            .into_iter()
            .map(|t| (t, json!([value_at(&kx, t) * 100.0, value_at(&ky, t) * 100.0])))
            .collect();
        if !keys.is_empty() {
            out.push(("transform/scale", keys));
        }
    }
    for (name, path, scale) in [("_opacity", "transform/opacity", 100.0f64), ("_rotation", "transform/rotation", 1.0)] {
        if let Some(k) = axis_keys(name) {
            let keys: Vec<(f64, Value)> = k.into_iter().map(|(t, v)| (t, json!(v * scale))).collect();
            out.push((path, keys));
        }
    }
    out
}

fn collect_all_nodes<'a>(node: &'a Value, out: &mut Vec<&'a Value>) {
    out.push(node);
    if let Some(children) = node.get("ChildList").and_then(Value::as_array) {
        for c in children {
            collect_all_nodes(c, out);
        }
    }
}
