"""Draw nutrition-facts label PNGs with Pillow from the fictional data in data/.

Nothing binary is committed: `nutrilabel render` regenerates every image. Four
labels are deliberately hard (smudge, rotation, tiny print, a missing line).
"""

import json
import random
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .config import DATA_FILE, LABELS_DIR

INK = (20, 20, 20)
PAPER = (250, 248, 240)


def load_products(path: Path = DATA_FILE) -> list[dict[str, Any]]:
    return json.loads(path.read_text())


def _font(size: int) -> ImageFont.FreeTypeFont:
    # Pillow's bundled default font scales to any size, so output is the same on every OS.
    return ImageFont.load_default(size=size)


def label_lines(product: dict[str, Any]) -> list[tuple[str, str, bool]]:
    """(left text, right text, bold) rows for the panel, honouring `omit`."""
    omit = set(product["style"].get("omit", []))

    def g(key: str, unit: str) -> str:
        return "" if product[key] is None else f"{product[key]:g}{unit}"

    rows = [
        ("Serving size", product["serving_size"], True),
        ("Calories", g("calories", ""), True),
        ("Total Fat", g("total_fat_g", "g"), False),
        ("Sodium", g("sodium_mg", "mg"), False),
        ("Total Carbohydrate", g("total_carbs_g", "g"), False),
        ("  Total Sugars", g("sugars_g", "g"), False),
        ("Protein", g("protein_g", "g"), False),
    ]
    keys = [None, "calories", "total_fat_g", "sodium_mg", "total_carbs_g", "sugars_g", "protein_g"]
    return [row for row, key in zip(rows, keys) if key not in omit]


def render_label(product: dict[str, Any]) -> Image.Image:
    """One label image. The product's `style` flags add the hard-case distortions."""
    style = product["style"]
    scale = 0.42 if style.get("tiny") else 1.0
    w, h = int(520 * scale), int(640 * scale)
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    pad = int(22 * scale)
    d.rectangle([6, 6, w - 7, h - 7], outline=INK, width=3)

    y = pad
    d.text((pad, y), product["brand"], font=_font(int(20 * scale)), fill=INK)
    y += int(38 * scale)
    d.text((pad, y), "Nutrition Facts", font=_font(int(36 * scale)), fill=INK)
    y += int(50 * scale)
    d.text((pad, y), f"{product['servings_per_container']} servings per container", font=_font(int(20 * scale)), fill=INK)
    y += int(34 * scale)
    d.line([pad, y, w - pad, y], fill=INK, width=max(2, int(8 * scale)))
    y += int(14 * scale)

    for left, right, bold in label_lines(product):
        size = int((26 if bold else 22) * scale)
        d.text((pad, y), left, font=_font(size), fill=INK)
        right_w = d.textlength(right, font=_font(size))
        d.text((w - pad - right_w, y), right, font=_font(size), fill=INK)
        y += int(40 * scale)
        d.line([pad, y - int(6 * scale), w - pad, y - int(6 * scale)], fill=INK, width=1)

    y += int(10 * scale)
    allergens = ", ".join(product["allergens"]) or None
    if allergens:
        d.text((pad, y), f"Contains: {allergens}", font=_font(int(19 * scale)), fill=INK)

    if style.get("smudge"):
        img = _smudge(img)
    if style.get("tiny"):
        # Upscale-free shrink: the model sees a small, soft label with tiny print.
        img = img.filter(ImageFilter.GaussianBlur(0.6))
    if style.get("rotate"):
        img = img.rotate(style["rotate"], expand=True, fillcolor=(120, 118, 112), resample=Image.BICUBIC)
    return img


def _smudge(img: Image.Image) -> Image.Image:
    """Blur a band across the middle and overlay grey ink, like a wet thumb."""
    rng = random.Random(7)  # fixed seed: the smudge is the same on every run
    w, h = img.size
    box = (0, int(h * 0.38), w, int(h * 0.68))
    band = img.crop(box).filter(ImageFilter.GaussianBlur(3))
    img.paste(band, box)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(22):
        x, y = rng.randint(0, w), rng.randint(box[1], box[3])
        r = rng.randint(8, 22)
        od.ellipse([x - r, y - r, x + r, y + r], fill=(60, 60, 70, 55))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def render_all(out_dir: Path = LABELS_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for product in load_products():
        path = out_dir / f"{product['id']}.png"
        render_label(product).save(path)
        paths.append(path)
    return paths
