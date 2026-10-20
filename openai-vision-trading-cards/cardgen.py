"""Draw the fictional trading cards in data/cards.json as PNGs with Pillow.

Every card is invented. Four styles keep the extraction honest: `clean`,
`rotated` (the card sits crooked on a table), `low_contrast` (pale ink on pale
card stock, slightly blurred), and `smudged` (a grey thumbprint over one stat).
Cards are redrawn into generated/ on each run, so the PNGs are never committed.
"""

import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
CARDS_FILE = HERE / "data" / "cards.json"
OUT_DIR = HERE / "generated"

W, H = 600, 840

# macOS font paths first; Pillow's built-in font is the fallback elsewhere.
FONTS = {
    "sans": ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "bold": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "serif": ["/System/Library/Fonts/Supplemental/Georgia.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
}


def load_cards() -> list[dict]:
    return json.loads(CARDS_FILE.read_text())


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for path in FONTS[kind]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_width:
            line = trial
        else:
            lines.append(line)
            line = word
    return [*lines, line]


def palette(card: dict) -> dict[str, tuple[int, int, int]]:
    r, g, b = card["theme"]
    if "low_contrast" in card["style"]:
        # Ink is only ~35 levels darker than the card stock.
        stock = (min(r + 70, 245), min(g + 70, 245), min(b + 70, 245))
        ink = (stock[0] - 38, stock[1] - 38, stock[2] - 38)
        return {"border": (r + 40, g + 40, b + 40) if max(r, g, b) < 200 else (r, g, b), "stock": stock, "ink": ink, "art": (stock[0] - 20, stock[1] - 20, stock[2] - 20)}
    return {"border": (r, g, b), "stock": (248, 244, 232), "ink": (28, 26, 24), "art": (r, g, b)}


def draw_card(card: dict) -> Image.Image:
    p = palette(card)
    img = Image.new("RGB", (W, H), p["border"])
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((22, 22, W - 22, H - 22), radius=18, fill=p["stock"])

    # Header: name on the left, HP on the right.
    d.text((46, 40), card["name"], font=font("bold", 38), fill=p["ink"])
    d.text((W - 46, 46), f"HP {card['hp']}", font=font("bold", 34), fill=p["ink"], anchor="ra")
    d.text((46, 90), f"{card['card_type']} type", font=font("sans", 22), fill=p["ink"])

    # Art box: a seeded abstract picture, so it carries no text.
    rng = random.Random(card["id"])
    d.rectangle((46, 130, W - 46, 400), fill=p["art"])
    for _ in range(9):
        x, y = rng.randint(60, W - 160), rng.randint(140, 330)
        s = rng.randint(40, 110)
        shade = tuple(max(0, min(255, c + rng.randint(-45, 45))) for c in p["art"])
        d.ellipse((x, y, x + s, y + s), fill=shade)
    d.rectangle((46, 130, W - 46, 400), outline=p["ink"], width=3)

    # Attack row.
    d.line((46, 430, W - 46, 430), fill=p["ink"], width=2)
    d.text((46, 446), card["attack_name"], font=font("bold", 32), fill=p["ink"])
    d.text((W - 46, 446), str(card["attack_damage"]), font=font("bold", 36), fill=p["ink"], anchor="ra")

    # Ability block.
    d.text((46, 506), f"Ability: {card['ability_name']}", font=font("bold", 24), fill=p["ink"])
    body = font("serif", 23)
    y = 546
    for line in wrap(d, card["ability_text"], body, W - 92):
        d.text((46, y), line, font=body, fill=p["ink"])
        y += 32

    # Footer: defense on the left, set number and rarity on the right.
    d.line((46, 730, W - 46, 730), fill=p["ink"], width=2)
    d.text((46, 748), f"Defense {card['defense']}", font=font("bold", 28), fill=p["ink"])
    d.text((W - 46, 744), card["set_number"], font=font("sans", 24), fill=p["ink"], anchor="ra")
    d.text((W - 46, 774), card["rarity"], font=font("sans", 22), fill=p["ink"], anchor="ra")

    if "low_contrast" in card["style"]:
        img = img.filter(ImageFilter.GaussianBlur(1.1))
    if card["style"] == "smudged":
        img = smudge(img, card["smudge"])
    return img


def smudge(img: Image.Image, stat: str) -> Image.Image:
    """Lay a blurred grey thumbprint over one stat so its digits are unreadable."""
    boxes = {"defense": (160, 746, 260, 786), "hp": (440, 36, 560, 90)}
    x0, y0, x1, y1 = boxes[stat]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse((x0 - 12, y0 - 8, x1 + 12, y1 + 8), fill=(150, 146, 140, 255))
    layer = layer.filter(ImageFilter.GaussianBlur(4))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def place_on_table(card_img: Image.Image, degrees: float) -> Image.Image:
    """Rotate the card and drop it on a wooden-grey table, like a phone photo."""
    table = Image.new("RGB", (900, 1100), (92, 84, 76))
    rotated = card_img.convert("RGBA").rotate(degrees, expand=True, resample=Image.BICUBIC)
    table.paste(rotated, ((900 - rotated.width) // 2, (1100 - rotated.height) // 2), rotated)
    return table


def render_all(out_dir: Path = OUT_DIR) -> dict[str, Path]:
    out_dir.mkdir(exist_ok=True)
    paths: dict[str, Path] = {}
    for card in load_cards():
        img = draw_card(card)
        if "rotation" in card:
            img = place_on_table(img, card["rotation"])
        path = out_dir / f"{card['id']}.png"
        img.save(path)
        paths[card["id"]] = path
    return paths


if __name__ == "__main__":
    for card_id, path in render_all().items():
        print(f"{card_id}: {path}")
