"""One-off script to generate placeholder JPGs for local development.
Run with: python scripts/generate_placeholders.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_IMG = BASE_DIR / "static" / "img"
PLACEHOLDER_DIR = STATIC_IMG / "placeholders"
STATIC_IMG.mkdir(parents=True, exist_ok=True)
PLACEHOLDER_DIR.mkdir(parents=True, exist_ok=True)

PALETTE = [
    ("#1f3d33", "#c9a25e"),
    ("#2c4a3e", "#d8b877"),
    ("#173029", "#b8935a"),
    ("#264539", "#e0c58a"),
]


def make_image(path, size, label, color_idx=0):
    bg, accent = PALETTE[color_idx % len(PALETTE)]
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)

    # simple diagonal accent stripes for visual texture
    for i in range(-size[1], size[0], 60):
        draw.line([(i, size[1]), (i + size[1], 0)], fill=accent, width=2)

    try:
        font = ImageFont.truetype("arial.ttf", size=max(22, size[0] // 22))
    except Exception:
        font = ImageFont.load_default()

    text = label.upper()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    box_pad = 24
    box = [
        (size[0] - tw) / 2 - box_pad,
        (size[1] - th) / 2 - box_pad,
        (size[0] + tw) / 2 + box_pad,
        (size[1] + th) / 2 + box_pad,
    ]
    draw.rectangle(box, fill=(0, 0, 0, 120))
    draw.text(((size[0] - tw) / 2, (size[1] - th) / 2 - bbox[1]), text, font=font, fill="white")

    img.save(path, "JPEG", quality=85)
    print(f"wrote {path}")


make_image(STATIC_IMG / "hero-placeholder.jpg", (1920, 1080), "Teahouse Villa", 0)
make_image(STATIC_IMG / "room-placeholder.jpg", (900, 700), "Room", 1)

gallery_items = [
    ("villa-exterior.jpg", "Villa Exterior", 0),
    ("villa-pool.jpg", "Swimming Pool", 1),
    ("villa-garden.jpg", "Garden", 2),
    ("villa-kitchen.jpg", "Kitchen", 3),
    ("bedroom-master.jpg", "Master Bedroom", 0),
    ("bedroom-garden.jpg", "Garden Room", 1),
    ("bedroom-deluxe.jpg", "Deluxe Room", 2),
    ("bathroom-1.jpg", "Bathroom", 3),
    ("nearby-beach.jpg", "Nearby Beach", 0),
]
for filename, label, idx in gallery_items:
    make_image(PLACEHOLDER_DIR / filename, (1200, 900), label, idx)
