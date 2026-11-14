#!/usr/bin/env python3
"""Rolled back: this changed the A/V switch clicks and the app crashed after using one.

Kept as a no-op so the patch list keeps its order and an install can be checked against it. The
crash is being found from the panic file the app writes to DCIM/EffectCraft; the switches are back
to upstream behaviour until then.
"""
from __future__ import annotations

MARKER = "EFFECTCRAFT_OURS_SWITCH_HIT_ROLLED_BACK"


def main() -> None:
    print("A/V switch click changes rolled back")


if __name__ == "__main__":
    main()
