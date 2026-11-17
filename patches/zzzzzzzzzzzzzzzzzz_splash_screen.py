#!/usr/bin/env python3
"""开屏界面改成自绘 View：黑底 + 圆角图标（等比缩放不裁切）+ 主标题/副标题淡入，1 秒淡出、1.5 秒兜底。

系统的 windowBackground 贴图路径会把图标裁切、边缘出黑斑（源图和包内图标都验证过是干净的，
问题在渲染管线），所以这里不再让系统画图标：

1. `lib/app_icons.py` 额外产出两张 drawable：
   - `res/drawable-nodpi/splash_icon.png` —— 原图（不抠底、不裁切）缩到 512，开屏自己画圆角
   - `res/drawable-nodpi/splash_blank.png` —— 1×1 透明图，给系统开屏当图标（等于不显示）
2. `lib/android_project.py` 的主题加上 Android 12+ 的系统开屏属性：背景纯黑、图标用透明图，
   于是系统那一屏只剩黑底，不再有裁切/黑斑。
3. `templates/android/SafActivity.java` 里新增自绘 `SplashView`：黑底 + 22% 圆角图标 + 主标题
   `Shimove Aex` + 副标题 `本软件由施信开发 · 基于开源项目`；图标 350ms 淡入、文字延迟 120ms 跟 300ms；
   1.0 秒淡出、1.5 秒无条件移除（绝不拖长开屏）。
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_SPLASH_VIEW_V1"

# --- 1. SafActivity：onCreate 里装开屏 ---
ONCREATE_ANCHOR = "        super.onCreate(savedInstanceState);\n"
ONCREATE_NEW = "        super.onCreate(savedInstanceState);\n        installSplashView();\n"

# --- 2. SafActivity：方法 + 自绘 View 插在 installInputView() 之后 ---
METHODS_ANCHOR = '''                inputView.setFocusableInTouchMode(false);
            }
        } catch (Throwable e) {
            Log.e(TAG, "Failed to install input view", e);
        }
    }
'''

METHODS = r'''
    // EFFECTCRAFT_OURS_SPLASH_VIEW_V1 — 自绘开屏：黑底 + 圆角图标（等比缩放、不裁切）+ 主副标题淡入，
    // 1.0 秒淡出、1.5 秒无条件移除，确保不会拖长开屏或卡在开屏。
    private SplashView splashView;

    private void installSplashView() {
        try {
            if (splashView != null) {
                return;
            }
            android.view.ViewGroup content = getWindow() != null
                    ? getWindow().getDecorView().findViewById(android.R.id.content) : null;
            if (content == null) {
                return;
            }
            splashView = new SplashView(this);
            content.addView(splashView, new android.view.ViewGroup.LayoutParams(
                    android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                    android.view.ViewGroup.LayoutParams.MATCH_PARENT));
            splashView.start();
            splashView.postDelayed(this::dismissSplash, 1000L);
            content.postDelayed(this::dismissSplash, 1500L);
        } catch (Throwable error) {
            Log.w(TAG, "splash screen skipped: " + error);
            splashView = null;
        }
    }

    private void dismissSplash() {
        final SplashView view = splashView;
        if (view == null) {
            return;
        }
        splashView = null;
        try {
            view.fadeOutAndRemove();
        } catch (Throwable ignored) {
        }
    }

    /**
     * EFFECTCRAFT_OURS_SPLASH_VIEW_V1 — 黑底、圆角图标（22% 圆角，等比缩放不裁切）、
     * 主标题与副标题。图标 350ms 淡入，文字延迟 120ms 再 300ms 淡入，整体 240ms 淡出后移除。
     */
    private static final class SplashView extends android.view.View {
        private static final long ICON_MS = 350L;
        private static final long TEXT_DELAY_MS = 120L;
        private static final long TEXT_MS = 300L;
        private static final long FADE_OUT_MS = 240L;
        private static final String TITLE = "Shimove Aex";
        private static final String SUBTITLE = "本软件由施信开发 · 基于开源项目";

        private final android.graphics.Paint titlePaint = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        private final android.graphics.Paint subtitlePaint = new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        private final android.graphics.Path clip = new android.graphics.Path();
        private final android.graphics.RectF iconRect = new android.graphics.RectF();
        private final android.graphics.drawable.Drawable icon;
        private float iconAlpha;
        private float textAlpha;

        SplashView(Context context) {
            super(context);
            setBackgroundColor(android.graphics.Color.BLACK);
            setClickable(false);
            setFocusable(false);
            float scaled = context.getResources().getDisplayMetrics().scaledDensity;
            titlePaint.setColor(android.graphics.Color.WHITE);
            titlePaint.setTextAlign(android.graphics.Paint.Align.CENTER);
            titlePaint.setTypeface(android.graphics.Typeface.create(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD));
            titlePaint.setTextSize(27f * scaled);
            subtitlePaint.setColor(0xFFB4B4B4);
            subtitlePaint.setTextAlign(android.graphics.Paint.Align.CENTER);
            subtitlePaint.setTextSize(13f * scaled);
            android.graphics.drawable.Drawable found = null;
            try {
                int id = context.getResources().getIdentifier("splash_icon", "drawable", context.getPackageName());
                if (id != 0) {
                    found = context.getResources().getDrawable(id, null);
                }
            } catch (Throwable ignored) {
            }
            icon = found;
        }

        void start() {
            android.animation.ValueAnimator iconIn = android.animation.ValueAnimator.ofFloat(0f, 1f);
            iconIn.setDuration(ICON_MS);
            iconIn.addUpdateListener(animation -> {
                iconAlpha = ((Number) animation.getAnimatedValue()).floatValue();
                invalidate();
            });
            iconIn.start();
            android.animation.ValueAnimator textIn = android.animation.ValueAnimator.ofFloat(0f, 1f);
            textIn.setStartDelay(TEXT_DELAY_MS);
            textIn.setDuration(TEXT_MS);
            textIn.addUpdateListener(animation -> {
                textAlpha = ((Number) animation.getAnimatedValue()).floatValue();
                invalidate();
            });
            textIn.start();
        }

        void fadeOutAndRemove() {
            android.animation.ValueAnimator out = android.animation.ValueAnimator.ofFloat(1f, 0f);
            out.setDuration(FADE_OUT_MS);
            out.addUpdateListener(animation -> setAlpha(((Number) animation.getAnimatedValue()).floatValue()));
            out.addListener(new android.animation.AnimatorListenerAdapter() {
                @Override
                public void onAnimationEnd(android.animation.Animator animation) {
                    android.view.ViewGroup parent = (android.view.ViewGroup) getParent();
                    if (parent != null) {
                        parent.removeView(SplashView.this);
                    }
                }
            });
            out.start();
        }

        @Override
        protected void onDraw(android.graphics.Canvas canvas) {
            float w = getWidth();
            float h = getHeight();
            canvas.drawColor(android.graphics.Color.BLACK);
            if (icon != null) {
                float side = Math.min(w, h) * 0.42f;
                float cx = w / 2f;
                float cy = h * 0.40f;
                iconRect.set(cx - side / 2f, cy - side / 2f, cx + side / 2f, cy + side / 2f);
                icon.setBounds((int) iconRect.left, (int) iconRect.top, (int) iconRect.right, (int) iconRect.bottom);
                icon.setAlpha((int) (Math.max(0f, Math.min(1f, iconAlpha)) * 255f));
                clip.reset();
                float radius = side * 0.22f;
                clip.addRoundRect(iconRect, radius, radius, android.graphics.Path.Direction.CW);
                canvas.save();
                canvas.clipPath(clip);
                icon.draw(canvas);
                canvas.restore();
            }
            int alpha = (int) (Math.max(0f, Math.min(1f, textAlpha)) * 255f);
            titlePaint.setAlpha(alpha);
            subtitlePaint.setAlpha(alpha);
            float cx = w / 2f;
            float titleY = (icon != null ? iconRect.bottom : h * 0.40f) + h * 0.10f;
            canvas.drawText(TITLE, cx, titleY, titlePaint);
            canvas.drawText(SUBTITLE, cx, titleY + 26f * getResources().getDisplayMetrics().scaledDensity, subtitlePaint);
        }
    }
'''

# --- 3. app_icons.py：多写两张 drawable ---
ICONS_ANCHOR = '    foreground.save(res_dir / "drawable-xxxhdpi" / "ic_launcher_foreground.png")\n'
ICONS_NEW = '''    foreground.save(res_dir / "drawable-xxxhdpi" / "ic_launcher_foreground.png")
    # EFFECTCRAFT_OURS_SPLASH_VIEW_V1 — 开屏用自己的方图（不抠底、不裁切），外加一张 1x1 透明图
    # 让系统的启动图标层什么都不画（自绘 View 才是唯一会显示的开屏）。
    nodpi = res_dir / "drawable-nodpi"
    nodpi.mkdir(parents=True, exist_ok=True)
    pristine.resize((512, 512), Image.LANCZOS).save(nodpi / "splash_icon.png")
    Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(nodpi / "splash_blank.png")
'''

# --- 4. android_project.py：主题里的系统开屏属性 ---
THEME_ANCHOR = '''        <item name="android:windowBackground">@android:color/black</item>
'''
THEME_NEW = '''        <item name="android:windowBackground">@android:color/black</item>
        <!-- EFFECTCRAFT_OURS_SPLASH_VIEW_V1 — Android 12+ 的系统开屏：纯黑底 + 透明图标，
             不再让系统按 mipmap 裁切我们的图标（自绘 SplashView 负责真正的开屏画面）。 -->
        <item name="android:windowSplashScreenBackground">@android:color/black</item>
        <item name="android:windowSplashScreenAnimatedIcon">@drawable/splash_blank</item>
        <item name="android:windowSplashScreenIconBackgroundColor">@android:color/black</item>
'''


def patch_text(path: Path, old: str, new: str, want: int = 1) -> bool:
    src = path.read_text(encoding="utf-8")
    if new in src:
        return False
    got = src.count(old)
    if got != want:
        raise SystemExit(f"{path.name}: anchor count {got} != {want}")
    path.write_text(src.replace(old, new, 1), encoding="utf-8")
    return True


def main() -> None:
    build_root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    saf = build_root / "templates" / "android" / "SafActivity.java"
    src = saf.read_text(encoding="utf-8")
    if MARKER in src:
        print("splash view already installed")
        return
    patch_text(saf, ONCREATE_ANCHOR, ONCREATE_NEW)
    patch_text(saf, METHODS_ANCHOR, METHODS_ANCHOR + METHODS)
    patch_text(build_root / "lib" / "app_icons.py", ICONS_ANCHOR, ICONS_NEW)
    patch_text(build_root / "lib" / "android_project.py", THEME_ANCHOR, THEME_NEW)
    print("splash: custom view + splash drawables + black system splash")


if __name__ == "__main__":
    main()
