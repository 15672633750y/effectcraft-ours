
/// `.ffx`（RIFX）里每个参数的数值：`tdmn` 给出名字，紧随的 `tdps` 给出 1–4 个大端 float。
fn ffx_values(bytes: &[u8]) -> Vec<(String, Vec<u8>)> {
    let mut out: Vec<(String, Vec<u8>)> = Vec::new();
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
            let floats: Vec<u8> = raw.to_vec();
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
        "Offset Darks" | "OffsetDarks" => ("offsetDarks", false),
        "Rotate" => ("rotate", false),
        "Radius" => ("radius", false),
        "Tint" => ("tint", false),
        "Color" => ("color", false),
        "Show" => ("show", false),
        "Effect" => ("effect", false),
        "Combine" => ("combine", false),
        "Mask Use" | "MaskUse" => ("maskUse", false),
        "Blur Mask" | "BlurMask" => ("blurMask", true),
        "Invert Mask" | "InvertMask" => ("invertMask", false),
        "Grain Amp" | "GrainAmp" => ("grainAmp", true),
        "Grain Blur" | "GrainBlur" => ("grainBlur", false),
        "Key Layer Density" | "KeyLayerDensity" => ("keyLayerDensity", true),
        "Rel Width" | "RelWidth" => ("relWidth", false),
        "Rel Height" | "RelHeight" => ("relHeight", false),
        "Edge Softness" | "EdgeSoftness" => ("edgeSoftness", false),
        "Smooth Curve" | "SmoothCurve" => ("smoothCurve", true),
        "Center XY" | "CenterXY" => ("centerXY", false),
        "Source Brightness" | "SourceBrightness" => ("sourceBrightness", true),
        "Blur Amount" | "BlurAmount" => ("blurAmount", false),
        "Blur Inside" | "BlurInside" => ("blurInside", false),
        // Sapphire 的 S_Rays / S_Glow / S_DropShadow / S_TextureFlux
        "Rays Length" => ("length", true),
        "Rays Brightness" => ("raysBrightness", true),
        "Threshold" => ("threshold", true),
        "Reverse Rays" => ("reverseRays", false),
        "Rays Color" => ("raysColor", false),
        "Source Opacity" => ("sourceOpacity", true),
        "Bg Brightness" => ("bgBrightness", true),
        "Rays From Alpha" => ("raysFromAlpha", false),
        "Rays Under Source" => ("raysUnderSource", false),
        "Affect Alpha" => ("affectAlpha", false),
        "Light Rays|Dark Rays" => ("rayKind", false),
        "Glow Width" => ("glowWidth", true),
        "Glow" => ("glow", true),
        "Glow Color" => ("glowColor", false),
        "Glow From Alpha" => ("glowFromAlpha", false),
        "Glow Under Source" => ("glowUnderSource", false),
        "Distance" => ("distance", false),
        "Direction" => ("direction", false),
        "Softness" => ("softness", false),
        "Shadow Color" => ("shadowColor", false),
        "Shift X" => ("shiftX", false),
        "Shift Y" => ("shiftY", false),
        "Fg Opacity" => ("fgOpacity", true),
        "Shadow Opacity" => ("opacity", true),
        "Shadow Blur" => ("softness", false),
        "Width X" => ("widthX", true),
        "Width Y" => ("widthY", true),
        "Light Background" => ("lightBackground", false),
        // S_TextureFlux（流光）
        "Octaves" => ("detail", false),
        "Seed" => ("seed", false),
        "Shift XY" => ("shiftX", false),
        "Bubble Amount" => ("bubbleAmount", true),
        "Color 0" => ("color0", false),
        "Color 1" => ("color1", false),
        "Brightness1" => ("brightness1", true),
        "Input Opacity" => ("inputOpacity", true),
        "Output Opacity" => ("outputOpacity", true),
        "Frequency" => ("frequency", true),
        "Speed" => ("speed", false),
        "Detail" => ("detail", false),
        "Random Seed" => ("seed", false),
        "Center X" => ("centerX", true),
        "Center Y" => ("centerY", true),
        _ => return None,
    })
}

/// 把预设里的数值写到刚应用的效果上；返回写了几个。
fn apply_ffx_values(s: &mut Session, effect_id: &str, values: &[(String, Vec<u8>)]) -> usize {
    let mut set = 0usize;
    for (name, raw) in values {
        let Some((param, percent)) = ffx_param(name) else { continue };
        let nums: Vec<f32> = raw
            .chunks_exact(4)
            .map(|c| f32::from_be_bytes([c[0], c[1], c[2], c[3]]))
            .collect();
        if nums.is_empty() {
            continue;
        }
        // 枚举/布尔参数（Show / Effect / Combine / Invert Mask…）在 RIFX 里是 4 字节整数
        let enumeration = matches!(param, "show" | "effect" | "combine" | "rayKind");
        let boolean = matches!(
            param,
            "invertMask" | "blurInside" | "reverseRays" | "raysFromAlpha" | "raysUnderSource" | "affectAlpha" | "glowFromAlpha" | "glowUnderSource" | "lightBackground"
        );
        let value = if boolean {
            let v = u32::from_be_bytes([raw[0], raw[1], raw[2], raw[3]]);
            json!(v != 0)
        } else if enumeration {
            let v = u32::from_be_bytes([raw[0], raw[1], raw[2], raw[3]]);
            // AE 的枚举从 1 开始，我们的参数从 0 开始
            let index = if param == "rayKind" { v.saturating_sub(1).min(15) } else { v.min(15) };
            json!(index)
        } else if nums.len() >= 3 {
            json!([nums[0], nums[1], nums[2], 1.0])
        } else {
            let mut v = nums[0] as f64;
            if !v.is_finite() {
                continue;
            }
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
