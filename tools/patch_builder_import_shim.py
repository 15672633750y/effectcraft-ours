#!/usr/bin/env python3
"""Teach the Android builder about ImportShim (no SAF recipe, no Rust/JNI bridge).

Three edits to ``lib/build-common.sh``, all string-level and count-verified:

1. Always emit ``java_sources = "java"`` (the non-SAF branch used to omit it, so Gradle never
   compiled any Java and the trampoline class could not exist).
2. Write ``templates/android/ImportShim.java`` into the generated Java source tree, with
   ``__PACKAGE__`` replaced by the app's package.
3. Give the generated manifest a second activity for it: an ``ACTION_VIEW`` filter with the
   document path patterns plus an ``ACTION_SEND`` filter, ``exported = true``.

Run from the builder checkout root (``artcraft/``) before ``bash lib/build-common.sh``.
"""
from __future__ import annotations

import sys
from pathlib import Path

# --- 1. java_sources, and the class itself ------------------------------------------------
A_OLD = """    java_sources = 'java_sources = "java"\\n' if saf else ''"""
A_NEW = '''    java_sources = 'java_sources = "java"\\n'
    # ImportShim lives in templates/android and must be compiled for every app that wants
    # "Open with" support, not only for the ones with a full SAF recipe.
    shim_java_dir = staging_dir / "java" / Path(*pkg.split("."))
    shim_java_dir.mkdir(parents=True, exist_ok=True)
    _shim_src = Path(__import__("os").environ["IMPORT_SHIM_JAVA"]).read_text(encoding="utf-8")
    (shim_java_dir / "ImportShim.java").write_text(
        _shim_src.replace("__PACKAGE__", pkg), encoding="utf-8"
    )'''

# --- 3. the second activity ---------------------------------------------------------------
C_OLD = '''    else:
        activity_block = f\'\'\'[package.metadata.android.application.activity]
config_changes = "{config_changes}"
label = "{title}"
launch_mode = "singleTask"
orientation = "sensor"
exported = true
intent_filter = {intent_filter_value}
\'\'\''''

C_NEW = '''    else:
        shim_exts = file_associations.ASSOCIATIONS.get(app, [])
        shim_data = file_associations._by_extension_data(shim_exts, typed=True)
        shim_filters = (
            '{ actions = ["android.intent.action.VIEW"], '
            'categories = ["android.intent.category.DEFAULT", "android.intent.category.BROWSABLE"], '
            'data = [' + shim_data + '] }, '
            '{ actions = ["android.intent.action.SEND", "android.intent.action.SEND_MULTIPLE"], '
            'categories = ["android.intent.category.DEFAULT"], data = [{ mime_type = "*/*" }] }'
        )
        activity_block = f\'\'\'[[package.metadata.android.application.activity]]
config_changes = "{config_changes}"
label = "{title}"
launch_mode = "singleTask"
orientation = "sensor"
exported = true
intent_filter = {intent_filter_value}

# ImportShim: headless trampoline for "Open with" / "Share to" (see templates/android/ImportShim.java).
[[package.metadata.android.application.activity]]
name = ".ImportShim"
config_changes = "{config_changes}"
label = "{title}"
theme = "@android:style/Theme.NoDisplay"
exclude_from_recents = true
exported = true
intent_filter = [{shim_filters}]
\'\'\''''


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "artcraft").resolve()
    sh = root / "lib" / "build-common.sh"
    src = sh.read_text(encoding="utf-8")
    if "ImportShim" in src:
        print("builder already patched")
        return 0
    for name, old in (("java_sources", A_OLD), ("activity_block", C_OLD)):
        if src.count(old) != 1:
            print(f"FAIL {name}: expected 1, found {src.count(old)}", file=sys.stderr)
            return 1
    src = src.replace(A_OLD, A_NEW, 1)
    src = src.replace(C_OLD, C_NEW, 1)
    sh.write_text(src, encoding="utf-8")
    print("builder patched: java_sources always on, ImportShim activity in the manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
