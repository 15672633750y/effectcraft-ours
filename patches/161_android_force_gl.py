#!/usr/bin/env python3
"""Dropped with 159: v0.24.1 starts reliably without forcing OpenGL."""
from __future__ import annotations

MARKER = "EFFECTCRAFT_OURS_FORCE_GL_DROPPED"


def main() -> None:
    print("launch guard left as upstream")
