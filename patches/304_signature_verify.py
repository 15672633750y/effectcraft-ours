#!/usr/bin/env python3
"""签名指纹写死校验：SHA-256 与官方一致才算官方版；不符只提示「非官方版本」，绝不阻止启动。

- 官方指纹：`6461ee2dbcdb7882575242218895f6ac4cab24abdfa97353bbe0d702bb4a75a3`
- `DCIM/EffectCraft/devmode.txt` 存在 → 完全跳过校验
- `DCIM/EffectCraft/allowed-signatures.txt` 每行一个哈希 → 命中即放行
- 其余情况：logcat 记一行 + 一条 Toast「非官方版本」，App 照常启动

`303_signature_record.py` 已经把实际指纹写进 `DCIM/EffectCraft/signature.txt`，这里只做判定。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SIGNATURE_VERIFY_V1"

CALL_ANCHOR = "        recordSignature();\n"
CALL_NEW = "        recordSignature();\n        verifySignature();\n"

# 303_signature_record 写进的那个方法的结尾，用来挂新方法
METHOD_ANCHOR = '''                java.io.File out = new java.io.File(dir, "signature.txt");
                try (java.io.FileWriter w = new java.io.FileWriter(out, false)) {
                    w.write(getPackageName() + "\\n" + hex + "\\n");
                }
            }
        } catch (Throwable ignored) {
        }
    }
'''

METHODS = r'''
    // EFFECTCRAFT_OURS_SIGNATURE_VERIFY_V1 — 官方签名指纹（SHA-256，证书 DER 的摘要）
    private static final String OFFICIAL_SIGNATURE_SHA256 = "6461ee2dbcdb7882575242218895f6ac4cab24abdfa97353bbe0d702bb4a75a3";

    /** 本安装包的签名证书 SHA-256（小写十六进制）；读不到时返回 null。 */
    private String currentSignatureSha256() {
        try {
            android.content.pm.Signature[] sigs;
            if (Build.VERSION.SDK_INT >= 28) {
                android.content.pm.SigningInfo info = getPackageManager().getPackageInfo(
                        getPackageName(), android.content.pm.PackageManager.GET_SIGNING_CERTIFICATES).signingInfo;
                sigs = info != null ? info.getApkContentsSigners() : null;
            } else {
                sigs = getPackageManager().getPackageInfo(
                        getPackageName(), android.content.pm.PackageManager.GET_SIGNATURES).signatures;
            }
            if (sigs == null || sigs.length == 0) {
                return null;
            }
            java.security.MessageDigest md = java.security.MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(sigs[0].toByteArray());
            StringBuilder sb = new StringBuilder();
            for (byte b : digest) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (Throwable error) {
            Log.w(TAG, "signature unavailable: " + error);
            return null;
        }
    }

    /** 允许清单：每行一个 SHA-256（大小写不敏感），命中就当作官方版。 */
    private boolean signatureAllowListed(String hex) {
        try {
            java.io.File list = new java.io.File(Environment.getExternalStorageDirectory(), "DCIM/EffectCraft/allowed-signatures.txt");
            if (!list.isFile()) {
                return false;
            }
            try (java.io.BufferedReader reader = new java.io.BufferedReader(new java.io.FileReader(list))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    String entry = line.trim().toLowerCase(java.util.Locale.ROOT);
                    if (entry.isEmpty() || entry.startsWith("#")) {
                        continue;
                    }
                    if (entry.startsWith("sha256:")) {
                        entry = entry.substring("sha256:".length()).trim();
                    }
                    if (entry.equals(hex)) {
                        return true;
                    }
                }
            }
        } catch (Throwable ignored) {
        }
        return false;
    }

    /** 签名校验：不符只提示「非官方版本」，不阻止启动（devmode.txt 存在则整段跳过）。 */
    private void verifySignature() {
        try {
            java.io.File root = Environment.getExternalStorageDirectory();
            if (new java.io.File(root, "DCIM/EffectCraft/devmode.txt").isFile()) {
                Log.i(TAG, "signature check skipped (devmode.txt)");
                return;
            }
            String hex = currentSignatureSha256();
            if (hex == null) {
                return;
            }
            if (hex.equals(OFFICIAL_SIGNATURE_SHA256)) {
                return;
            }
            if (signatureAllowListed(hex)) {
                Log.i(TAG, "signature allowed by list: " + hex);
                return;
            }
            Log.w(TAG, "non-official build, signature sha256: " + hex);
            Toast toast = android.widget.Toast.makeText(getApplicationContext(), "非官方版本", android.widget.Toast.LENGTH_LONG);
            toast.show();
        } catch (Throwable error) {
            Log.w(TAG, "signature check failed: " + error);
        }
    }
'''

IMPORT_ANCHOR = "import android.widget.FrameLayout;\n"
IMPORT_NEW = "import android.widget.FrameLayout;\nimport android.widget.Toast;\n"


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates" / "android" / "SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("signature verification already present")
        return
    if src.count(IMPORT_ANCHOR) != 1:
        raise SystemExit(f"import anchor: {src.count(IMPORT_ANCHOR)}")
    src = src.replace(IMPORT_ANCHOR, IMPORT_NEW, 1)
    if src.count(CALL_ANCHOR) != 1:
        raise SystemExit(f"call anchor: {src.count(CALL_ANCHOR)}")
    src = src.replace(CALL_ANCHOR, CALL_NEW, 1)
    if src.count(METHOD_ANCHOR) != 1:
        raise SystemExit(f"method anchor: {src.count(METHOD_ANCHOR)}")
    src = src.replace(METHOD_ANCHOR, METHOD_ANCHOR + METHODS, 1)
    path.write_text(src, encoding="utf-8")
    print("signature: official fingerprint enforced, non-official only warns")


if __name__ == "__main__":
    main()
