
/// 变换关键帧：从节点的 Props[0].Params 里取。
fn transform_keys(node: &Value) -> Vec<(&'static str, &'static str, Vec<(f64, Value)>)> {
    let mut out: Vec<(&'static str, &'static str, Vec<(f64, Value)>)> = Vec::new();
    let Some(params) = node
        .get("Props")
        .and_then(Value::as_array)
        .and_then(|a| a.first())
        .and_then(|p| p.get("Params"))
    else {
        return out;
    };
    for (name, path, dims) in [
        ("_position", "transform/position", 2usize),
        ("_scale", "transform/scale", 2),
        ("_rotation", "transform/rotation", 1),
        ("_opacity", "transform/opacity", 1),
    ] {
        let Some(kf) = params.get(name).and_then(|p| p.get("KeyFrames")).and_then(Value::as_array) else { continue };
        let mut keys: Vec<(f64, Value)> = Vec::new();
        for k in kf {
            let t = k.get("_x").and_then(Value::as_f64).unwrap_or(f64::NAN);
            if !t.is_finite() {
                continue;
            }
            let v = if dims == 2 {
                let g = |a: &str, b: &str| k.get(a).and_then(Value::as_f64).or_else(|| k.get(b).and_then(Value::as_f64));
                match (g("vx", "x"), g("vy", "y")) {
                    (Some(x), Some(y)) => Value::Vec2([x, y]),
                    _ => continue,
                }
            } else {
                match k.get("_y").and_then(Value::as_f64) {
                    Some(v) if path == "transform/opacity" => Value::Scalar(v * 100.0),
                    Some(v) => Value::Scalar(v),
                    None => continue,
                }
            };
            keys.push((t, v));
        }
        if !keys.is_empty() {
            out.push((name, path, keys));
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
