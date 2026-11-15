#!/usr/bin/env python3
"""Dropped: on v0.24.1 the graphics stack no longer crashes at start-up, so forcing OpenGL on
Android is unnecessary — and forcing a backend is exactly the kind of guess that cost us two hours.
"""
from __future__ import annotations

MARKER = "EFFECTCRAFT_OURS_ANDROID_GL_DROPPED"


def main() -> None:
    print("Android keeps the default graphics backend")
