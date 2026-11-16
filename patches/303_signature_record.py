#!/usr/bin/env python3
"""记录本机安装包的签名指纹：写进 DCIM/EffectCraft/signature.txt，并输出到日志。

Written once per install: the SHA-256 of the signing certificate, so a repacked copy (different key) is
visible at a glance and can be compared later. No blocking, so debugging and test re-signs keep working.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SIGNATURE_RECORD_V1"

HOOK = """        restoreSettingsBackup();
"""
FN = r'''

    /// EFFECTCRAFT_OURS_SIGNATURE_RECORD_V1 — 把签名指纹写出来，方便识别被重打包的副本。
    private void recordSignature() {
        try {
            android.content.pm.Signature[] sigs;
            if (Build.VERSION.SDK_INT >= 28) {
                android.content.pm.SigningInfo info = getPackageManager().getPackageInfo(getPackageName(), android.content.pm.PackageManager.GET_SIGNING_CERTIFICATES).signingInfo;
                sigs = info != null ? info.getApkContentsSigners() : null;
            } else {
                sigs = getPackageManager().getPackageInfo(getPackageName(), android.content.pm.PackageManager.GET_SIGNATURES).signatures;
            }
            if (sigs == null || sigs.length == 0) {
                return;
            }
            java.security.MessageDigest md = java.security.MessageDigest.getInstance("SHA-256");
            byte[] d = md.digest(sigs[0].toByteArray());
            StringBuilder sb = new StringBuilder();
            for (byte b : d) {
                sb.append(String.format("%02x", b));
            }
            String hex = sb.toString();
            Log.i(TAG, "signature sha256: " + hex);
            java.io.File dir = new java.io.File(Environment.getExternalStorageDirectory(), "DCIM/EffectCraft");
            if (dir.isDirectory() || dir.mkdirs()) {
                java.io.File out = new java.io.File(dir, "signature.txt");
                try (java.io.FileWriter w = new java.io.FileWriter(out, false)) {
                    w.write(getPackageName() + "\n" + hex + "\n");
                }
            }
        } catch (Throwable ignored) {
        }
    }
'''


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("signature record already present")
        return
    if src.count(HOOK) != 1:
        raise SystemExit(f"hook anchor: {src.count(HOOK)}")
    src = src.replace(HOOK, "        restoreSettingsBackup();\n        recordSignature();\n", 1)
    anchor = "    @Override\n    protected void onDestroy() {"
    if src.count(anchor) != 1:
        raise SystemExit(f"anchor: {src.count(anchor)}")
    src = src.replace(anchor, FN + "\n" + anchor, 1)
    path.write_text(src, encoding="utf-8")
    print("signature fingerprint is recorded on start")


if __name__ == "__main__":
    main()
