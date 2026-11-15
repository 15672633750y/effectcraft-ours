#!/usr/bin/env python3
"""Keeps the upstream manifest as it is: `configChanges` declared, orientation unrestricted.

(An earlier revision of this file removed `configChanges` and then locked the orientation; both
made the app worse — see NIGHT_LOG. The pristine builder already declares both correctly, so this
patch now only documents why nothing is changed.)
"""
from __future__ import annotations

import os
from pathlib import Path

MARKER = "EFFECTCRAFT_OURS_ROTATE_KEEP_V1"


def main() -> None:
    root = Path(os.environ["ARTCRAFT_DIR"]).resolve()
    src = (root / "lib/build-common.sh").read_text(encoding="utf-8")
    ok = 'config_changes = "{config_changes}"' in src and 'orientation = "sensor"' in src
    print("manifest left as upstream (configChanges + sensor)" if ok else "WARNING: manifest differs")
