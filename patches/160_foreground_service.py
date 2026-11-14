#!/usr/bin/env python3
"""A silent foreground service keeps the session alive while EffectCraft is in the background.

Android treats a backgrounded app as reclaimable and kills it under memory pressure — "leave it in
the background for a few minutes and it is gone". A foreground service tells the system the process
is still wanted.

The notification: Android requires *a* notification for a foreground service, but nothing forces it
to be noticeable — this uses a MINIMUM-importance channel, silent, no badge, no timestamp. On
Android 13+ notifications are not requested at all, so nothing appears in the shade; the service
still runs. The service starts when the app is no longer visible (onStop) and stops the moment it
comes back (onStart), so it never costs anything while the app is on screen.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_FOREGROUND_KEEPALIVE_V1"

SERVICE_JAVA = '''
    // EFFECTCRAFT_OURS_FOREGROUND_KEEPALIVE_V1
    /** 无声前台服务：让系统知道这个进程还要用，后台几分钟不会被回收。 */
    public static final class KeepAlive extends android.app.Service {
        private static final String CHANNEL = "effectcraft-keepalive";
        private static final int NOTIFICATION_ID = 41;

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
                CHANNEL, "后台运行", android.app.NotificationManager.IMPORTANCE_MIN);
            ch.setShowBadge(false);
            ch.setSound(null, null);
            ch.enableVibration(false);
            ch.setLockscreenVisibility(android.app.Notification.VISIBILITY_SECRET);
            nm.createNotificationChannel(ch);
        }

        @Override
        public void onCreate() {
            super.onCreate();
            ensureChannel();
            android.app.Notification.Builder b = android.os.Build.VERSION.SDK_INT >= 26
                ? new android.app.Notification.Builder(this, CHANNEL)
                : new android.app.Notification.Builder(this);
            b.setContentTitle("EffectCraft")
                .setContentText("保持编辑会话")
                .setSmallIcon(android.R.drawable.stat_notify_sync)
                .setOngoing(true)
                .setShowWhen(false)
                .setPriority(android.app.Notification.PRIORITY_MIN)
                .setSound(null);
            try {
                startForeground(NOTIFICATION_ID, b.build());
            } catch (Throwable ignored) {
            }
        }

        @Override
        public int onStartCommand(Intent intent, int flags, int startId) {
            return START_STICKY;
        }

        @Override
        public android.os.IBinder onBind(Intent intent) {
            return null;
        }
    }

    private boolean keepAliveRunning = false;

    /** 退到后台时启动（onStop），回到前台立刻停掉（onStart）：前台时不占任何开销。 */
    private void setKeepAlive(boolean on) {
        if (on == keepAliveRunning) {
            return;
        }
        try {
            Intent i = new Intent(this, KeepAlive.class);
            if (on) {
                // API 26+ 从后台启动服务必须用 startForegroundService，否则抛 IllegalStateException。
                if (android.os.Build.VERSION.SDK_INT >= 26) {
                    startForegroundService(i);
                } else {
                    startService(i);
                }
                keepAliveRunning = true;
            } else {
                stopService(i);
                keepAliveRunning = false;
            }
        } catch (Throwable error) {
            Log.w(TAG, "keep-alive service unavailable", error);
        }
    }

    @Override
    protected void onStop() {
        setKeepAlive(true);
        super.onStop();
    }

    @Override
    protected void onStart() {
        super.onStart();
        setKeepAlive(false);
    }

'''

MANIFEST_PERMS = '''    lines.append("    <uses-permission android:name=\\"android.permission.FOREGROUND_SERVICE\\" />")
    lines.append("    <uses-permission android:name=\\"android.permission.FOREGROUND_SERVICE_SPECIAL_USE\\" />")
'''

MANIFEST_SERVICE = '''
    _svc = (activities[0].get("name") or ".SafActivity") + "$KeepAlive"
    lines.append(f'        <service android:name="{_esc(_svc)}" android:exported="false" android:foregroundServiceType="specialUse">')
    lines.append('            <property android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE" android:value="keeps an editing session alive in the background" />')
    lines.append("        </service>")
'''


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()

    java = root / "templates/android/SafActivity.java"
    src = java.read_text(encoding="utf-8")
    if MARKER not in src:
        anchor = "    @Override\n    protected void onCreate(Bundle savedInstanceState) {\n"
        if src.count(anchor) != 1:
            raise SystemExit(f"onCreate anchor: {src.count(anchor)}")
        java.write_text(src.replace(anchor, SERVICE_JAVA + anchor, 1), encoding="utf-8")
        print("keep-alive service added to the shell")

    gen = root / "lib/android_project.py"
    src = gen.read_text(encoding="utf-8")
    if MARKER not in src:
        perm_anchor = '''    # EFFECTCRAFT_OURS_KEEPALIVE_V1'''
        app_anchor = '''    lines.append(f'    <application {" ".join(app_attrs)}>')'''
        close_anchor = '''    lines.append("    </application>")'''
        if src.count(perm_anchor) == 0:
            # no previous keep-alive patch: put the permissions after the last uses_permission loop
            perm_anchor = '''    # EFFECTCRAFT_OURS_KEEPALIVE_V1'''
        for a in (app_anchor, close_anchor):
            if src.count(a) != 1:
                raise SystemExit(f"manifest anchor {a[:40]!r}: {src.count(a)}")
        src = src.replace(app_anchor, MANIFEST_PERMS + app_anchor, 1)
        src = src.replace(close_anchor, MANIFEST_SERVICE + close_anchor, 1)
        src = src.replace("def manifest_xml(android_meta):", "// " + MARKER + "\ndef manifest_xml(android_meta):", 1) if False else src
        src = src.replace('"""Render AndroidManifest.xml from ``[package.metadata.android]``."""',
                          '"""Render AndroidManifest.xml from ``[package.metadata.android]``."""\n    # ' + MARKER, 1)
        gen.write_text(src, encoding="utf-8")
        print("manifest declares the keep-alive service")


if __name__ == "__main__":
    main()
