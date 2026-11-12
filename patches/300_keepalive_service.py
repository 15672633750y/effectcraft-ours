#!/usr/bin/env python3
"""A foreground service keeps the render alive when the app is in the background."""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_KEEPALIVE_V1"

SERVICE_JAVA = '''
package __PACKAGE__;

// __MARKER__
// Android kills backgrounded apps to reclaim memory. A foreground service with a quiet
// notification tells the system the work (a render) is still wanted.
public final class KeepAlive extends android.app.Service {
    private static final String CHANNEL = "effectcraft-sx-keepalive";
    private static final int NOTIFICATION_ID = 42;

    private void ensureChannel() {
        if (android.os.Build.VERSION.SDK_INT < 26) {
            return;
        }
        android.app.NotificationManager nm =
            (android.app.NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (nm.getNotificationChannel(CHANNEL) != null) {
            return;
        }
        android.app.NotificationChannel ch = new android.app.NotificationChannel(
            CHANNEL, "后台渲染", android.app.NotificationManager.IMPORTANCE_MIN);
        ch.setShowBadge(false);
        nm.createNotificationChannel(ch);
    }

    private android.app.Notification build() {
        android.app.Notification.Builder b = android.os.Build.VERSION.SDK_INT >= 26
            ? new android.app.Notification.Builder(this, CHANNEL)
            : new android.app.Notification.Builder(this);
        return b.setContentTitle("EffectCraft Sx")
            .setContentText("正在后台保持工程")
            .setSmallIcon(android.R.drawable.stat_sys_download_done)
            .setOngoing(true)
            .build();
    }

    @Override
    public int onStartCommand(android.content.Intent intent, int flags, int startId) {
        ensureChannel();
        try {
            startForeground(NOTIFICATION_ID, build());
        } catch (Throwable ignored) {
            // Without the notification permission the app keeps running as before.
        }
        try {
            android.os.PowerManager pm = (android.os.PowerManager) getSystemService(POWER_SERVICE);
            if (pm != null && !pm.isIgnoringBatteryOptimizations(getPackageName())) {
                android.content.Intent ask = new android.content.Intent(
                    android.provider.Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                    android.net.Uri.parse("package:" + getPackageName()));
                ask.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivity(ask);
            }
        } catch (Throwable ignored) { }
        return START_STICKY;
    }

    @Override
    public android.os.IBinder onBind(android.content.Intent intent) {
        return null;
    }
}
'''


def patch_sh(path: Path) -> bool:
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        return False
    anchor = '        (java_dir / f"{saf[\'activity\']}.java").write_text(java_src)\n'
    if src.count(anchor) != 1:
        raise SystemExit(f"java staging anchor: {src.count(anchor)}")
    extra = anchor + '''        # Foreground service so Android does not kill a backgrounded render.
        service_src = __SERVICE__ .replace("__PACKAGE__", pkg)
        (java_dir / "KeepAlive.java").write_text(service_src)
        java_src = java_src.replace(
            "        super.onCreate(savedInstanceState);",
            "        super.onCreate(savedInstanceState);\\n        try {\\n            startService(new android.content.Intent(this, KeepAlive.class));\\n        } catch (Throwable ignored) { }",
            1,
        )
        (java_dir / f"{saf['activity']}.java").write_text(java_src)
'''.replace("__SERVICE__", '"""' + SERVICE_JAVA.replace("'''", "\\'\\'\\'") + '"""')
    path.write_text(src.replace(anchor, extra, 1), encoding="utf-8")
    return True


def patch_manifest(path: Path) -> bool:
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        return False
    perm_anchor = "    application = android_meta.get(\"application\") or {}\n"
    if src.count(perm_anchor) != 1:
        raise SystemExit("manifest permission anchor missing")
    src = src.replace(
        perm_anchor,
        '    # ' + MARKER + '\n'
        '    lines.append("    <uses-permission android:name=\\"android.permission.FOREGROUND_SERVICE\\" />")\n'
        '    lines.append("    <uses-permission android:name=\\"android.permission.FOREGROUND_SERVICE_DATA_SYNC\\" />")\n'
        '    lines.append("    <uses-permission android:name=\\"android.permission.POST_NOTIFICATIONS\\" />")\n'
            '    lines.append("    <uses-permission android:name=\\"android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS\\" />")\n'
        + perm_anchor,
        1,
    )
    app_end = '    lines.append("    </application>")\n'
    if src.count(app_end) != 1:
        raise SystemExit("manifest application anchor missing")
    src = src.replace(
        app_end,
        '    lines.append("        <service android:name=\\".KeepAlive\\" android:exported=\\"false\\" android:foregroundServiceType=\\"dataSync\\" />")\n' + app_end,
        1,
    )
    path.write_text(src, encoding="utf-8")
    return True


def main() -> None:
    root = Path(os.environ.get("ARTCRAFT_DIR") or "").resolve()
    if not str(root):
        print("ARTCRAFT_DIR not set; skipping keep-alive service")
        return
    did_sh = patch_sh(root / "lib/build-common.sh")
    did_manifest = patch_manifest(root / "lib/android_project.py")
    print(
        "keep-alive service installed"
        if (did_sh or did_manifest)
        else "keep-alive service already installed"
    )


if __name__ == "__main__":
    main()
