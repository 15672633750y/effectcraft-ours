#!/usr/bin/env python3
"""Render the temporary launcher icon: an Ae-style tile (dark blue, rounded, italic Ae).

Drawn from scratch with Pillow, not copied from any vendor asset. Personal testing only.
"""
import sys
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "app-icon.png"
SIZE = 512
BG = (0, 2, 90, 255)
FG = (153, 153, 255, 255)

img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=110, fill=BG)

font = None
for path in (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf",
):
    try:
        font = ImageFont.truetype(path, 300)
        break
    except OSError:
        continue
if font is None:
    font = ImageFont.load_default()

text = "Ae"
box = d.textbbox((0, 0), text, font=font)
w, h = box[2] - box[0], box[3] - box[1]
x = (SIZE - w) / 2 - box[0]
y = (SIZE - h) / 2 - box[1] - 10
d.text((x, y), text, font=font, fill=FG)
img.save(OUT)
print(f"wrote {OUT} ({SIZE}x{SIZE})")
