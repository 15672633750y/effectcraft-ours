#!/usr/bin/env python3
"""崩溃取证：文件直接写 DCIM（并 fsync），再加“异常退出”检测。

The Java handler existed but never produced a file on the phone: it inserted through MediaStore and
fell back to the app's private folder on any failure — invisible to the user. It now writes the trace
straight into `DCIM/EffectCraft` with `FileOutputStream` and `sync()`, keeping the app-private copy as
a second record. A heartbeat file is refreshed while the app runs; on the next start a stale heartbeat
means the previous run died without unwinding (a native abort or a kill), which is written as
`crash-abnormal-<time>.txt` — the only way to see those.
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_CRASH_FORENSICS_V1"

ANCHOR = "    private void installCrashLogger() {"
NEW_HANDLER = '''    // EFFECTCRAFT_OURS_CRASH_FORENSICS_V1 — 直接写 DCIM 并 fsync；再加心跳判定异常退出
    private static final String CRASH_DIR = "/storage/emulated/0/DCIM/EffectCraft";
    private static final String HEARTBEAT = "/storage/emulated/0/DCIM/EffectCraft/.running";

    private void writeCrashFile(String text) {
        String name = "crash-" + System.currentTimeMillis() + ".txt";
        try {
            java.io.File dir = new java.io.File(CRASH_DIR);
            if (!dir.isDirectory()) dir.mkdirs();
            java.io.File out = new java.io.File(dir, name);
            try (java.io.FileOutputStream os = new java.io.FileOutputStream(out)) {
                os.write(text.getBytes("UTF-8"));
                os.flush();
                os.getFD().sync();
            }
        } catch (Throwable ignored) {
        }
        try {
            java.io.File out = new java.io.File(getExternalFilesDir(null), name);
            try (java.io.FileOutputStream os = new java.io.FileOutputStream(out)) {
                os.write(text.getBytes("UTF-8"));
                os.flush();
                os.getFD().sync();
            }
        } catch (Throwable ignored) {
        }
    }

    private void startHeartbeat() {
        final java.io.File beat = new java.io.File(HEARTBEAT);
        Thread t = new Thread(() -> {
            while (true) {
                try {
                    java.io.File dir = new java.io.File(CRASH_DIR);
                    if (!dir.isDirectory()) dir.mkdirs();
                    try (java.io.FileOutputStream os = new java.io.FileOutputStream(beat)) {
                        os.write(Long.toString(System.currentTimeMillis()).getBytes("UTF-8"));
                        os.flush();
                    }
                    Thread.sleep(5000L);
                } catch (InterruptedException e) {
                    return;
                } catch (Throwable ignored) {
                    try { Thread.sleep(5000L); } catch (InterruptedException e) { return; }
                }
            }
        }, "heartbeat");
        t.setDaemon(true);
        t.start();
    }

    private void reportAbnormalExit() {
        try {
            java.io.File beat = new java.io.File(HEARTBEAT);
            if (!beat.isFile()) return;
            long last = 0L;
            try (java.io.FileInputStream in = new java.io.FileInputStream(beat)) {
                byte[] b = new byte[32];
                int n = in.read(b);
                if (n > 0) last = Long.parseLong(new String(b, 0, n, "UTF-8").trim());
            }
            long now = System.currentTimeMillis();
            if (now - last > 30000L) {
                String text = "上次运行没有正常退出（不是 Java 异常，可能是原生崩溃或被系统杀掉）\\n"
                    + "最后心跳：" + last + "（约 " + ((now - last) / 1000L) + " 秒前）\\n"
                    + "时间：" + now + "\\n";
                writeCrashFile(text);
            }
        } catch (Throwable ignored) {
        }
    }

''' + ANCHOR


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    path = root / "templates/android/SafActivity.java"
    src = path.read_text(encoding="utf-8")
    if MARKER in src:
        print("crash forensics already installed")
        return
    if src.count(ANCHOR) != 1:
        raise SystemExit(f"anchor: {src.count(ANCHOR)}")
    src = src.replace(ANCHOR, NEW_HANDLER, 1)
    # 换掉原来的 handler 写法：优先直写文件
    old_write = '''                try {
                    android.content.ContentValues v = new android.content.ContentValues();'''
    new_write = '''                // EFFECTCRAFT_OURS_CRASH_FORENSICS_V1 — 先直写文件（并 fsync）
                writeCrashFile(text);
                try {
                    android.content.ContentValues v = new android.content.ContentValues();'''
    if src.count(old_write) == 1:
        src = src.replace(old_write, new_write, 1)
    # onCreate 里：报异常退出 + 起心跳
    call_old = "        installCrashLogger();\n"
    call_new = '''        installCrashLogger();
        // EFFECTCRAFT_OURS_CRASH_FORENSICS_V1 — 先报告上次异常退出，再起心跳
        try {
            reportAbnormalExit();
            startHeartbeat();
            // 自证：每次启动都写一个 startup.txt（带时间），用来确认“写得进 DCIM”
            try {
                java.io.File dir = new java.io.File(CRASH_DIR);
                if (!dir.isDirectory()) dir.mkdirs();
                try (java.io.FileOutputStream os = new java.io.FileOutputStream(new java.io.File(dir, "startup.txt"))) {
                    os.write(("启动于 " + System.currentTimeMillis() + "\n").getBytes("UTF-8"));
                    os.flush();
                    os.getFD().sync();
                }
            } catch (Throwable ignored) {
            }
        } catch (Throwable ignored) {
        }
'''
    if src.count(call_old) == 1:
        src = src.replace(call_old, call_new, 1)
    path.write_text(src, encoding="utf-8")
    print("crash forensics installed")


if __name__ == "__main__":
    main()
