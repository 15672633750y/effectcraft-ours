
/// `.ffx`（RIFX）里每个参数的数值：`tdmn` 给出名字，紧随的 `tdps` 给出 1–4 个大端 float。
fn ffx_values(bytes: &[u8]) -> Vec<(String, Vec<f32>)> {
    let mut out: Vec<(String, Vec<f32>)> = Vec::new();
    let mut last_name: Option<String> = None;
    let mut i = 0usize;
    while i + 8 <= bytes.len() {
        let tag = &bytes[i..i + 4];
        let len = u32::from_be_bytes([bytes[i + 4], bytes[i + 5], bytes[i + 6], bytes[i + 7]]) as usize;
        if (tag == b"tdmn" || tag == b"tdsn") && i + 8 + len <= bytes.len() {
            let raw = &bytes[i + 8..i + 8 + len];
            let name: String = raw.iter().take_while(|b| **b != 0).map(|b| *b as char).collect();
            if !name.is_empty() {
                last_name = Some(name);
            }
            i += 8 + len;
            continue;
        }
        if tag == b"tdps" && i + 8 + len <= bytes.len() && len > 0 && len % 4 == 0 && len <= 16 {
            let raw = &bytes[i + 8..i + 8 + len];
            let floats: Vec<f32> = raw
                .chunks_exact(4)
                .map(|c| f32::from_be_bytes([c[0], c[1], c[2], c[3]]))
                .filter(|v| v.is_finite())
                .collect();
            if !floats.is_empty()
                && let Some(name) = &last_name
            {
                out.push((name.clone(), floats));
            }
            i += 8 + len;
            continue;
        }
        i += 1;
    }
    out
}

/// 预设里的参数名 → 我们的参数名；None 表示这个参数我们不认。
fn ffx_param(name: &str) -> Option<(&'static str, bool)> {
    // 第二个值：是否按百分比处理（AE 里 100 = 原值）
    Some(match name {
        "Amount" => ("amount", true),
        "Brightness" => ("brightness", true),
        "Saturation" => ("saturation", true),
        "Opacity" => ("opacity", true),
        "Squareness" => ("squareness", true),
        "Offset Darks" | "OffsetDarks" => ("offsetDarks", true),
        "Rotate" => ("rotate", false),
        "Radius" => ("radius", false),
        "Tint" => ("tint", false),
        "Color" => ("color", false),
        "Show" => ("show", false),
        "Effect" => ("effect", false),
        "Combine" => ("combine", false),
        _ => return None,
    })
}

/// 把预设里的数值写到刚应用的效果上；返回写了几个。
fn apply_ffx_values(s: &mut Session, effect_id: &str, values: &[(String, Vec<f32>)]) -> usize {
    let mut set = 0usize;
    for (name, floats) in values {
        let Some((param, percent)) = ffx_param(name) else { continue };
        let value = if floats.len() >= 3 {
            json!([floats[0], floats[1], floats[2]])
        } else {
            let mut v = floats[0] as f64;
            if percent && v.abs() > 4.0 {
                v /= 100.0;
            }
            json!(v)
        };
        let path = format!("effects/{effect_id}/{param}");
        if s.execute("prop.set", json!({"path": path, "value": value})).is_ok() {
            set += 1;
        }
    }
    set
}
