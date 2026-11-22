#!/usr/bin/env python3
"""Build a 256x256 Workshop preview.png. Needs Pillow (pip install pillow).

Text card:        python make_preview.py --title "My Mod" [--subtitle BETA] --out MyMod/preview.png
From screenshot:  python make_preview.py --shot raw.png [--crop x1,y1,x2,y2] --title "TOP TEXT" [--bottom "BOTTOM TEXT"] --out MyMod/preview.png

Drawn at 512 then downscaled with LANCZOS so text stays smooth. Copy this into your repo's tools/ and
tune colours per mod; keep the script so the image can be rebuilt.
"""
import argparse
from PIL import Image, ImageDraw, ImageFont

BIG = 512
FONTS = ["impact.ttf", "C:/Windows/Fonts/impact.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"]


def font(px):
    for f in FONTS:
        try:
            return ImageFont.truetype(f, px)
        except OSError:
            pass
    return ImageFont.load_default()


def fit(draw, text, px, width):
    f = font(px)
    while px > 12 and draw.textlength(text, font=f) > width:
        px -= 2
        f = font(px)
    return f


def outlined(draw, text, y, px, fill):
    f = fit(draw, text, px, BIG - 32)
    w = draw.textlength(text, font=f)
    draw.text(((BIG - w) / 2, y), text, font=f, fill=fill, stroke_width=4, stroke_fill=(0, 0, 0))


def from_shot(a):
    img = Image.open(a.shot).convert("RGB")
    if a.crop:
        img = img.crop(tuple(int(v) for v in a.crop.split(",")))
    side = min(img.size)  # centre square
    l, t = (img.width - side) // 2, (img.height - side) // 2
    img = img.crop((l, t, l + side, t + side)).resize((BIG, BIG), Image.LANCZOS).convert("RGBA")
    band = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(band)
    d.rectangle([0, 0, BIG, 96], fill=(0, 0, 0, 170))
    if a.bottom:
        d.rectangle([0, BIG - 96, BIG, BIG], fill=(0, 0, 0, 170))
    img = Image.alpha_composite(img, band)
    d = ImageDraw.Draw(img)
    outlined(d, a.title, 8, 70, (255, 221, 0))
    if a.bottom:
        outlined(d, a.bottom, BIG - 86, 58, (255, 221, 0))
    return img


def card(a):
    img = Image.new("RGBA", (BIG, BIG), (14, 14, 12, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([8, 8, BIG - 9, BIG - 9], outline=(92, 92, 92), width=8)
    outlined(d, a.title, BIG // 2 - 60, 72, (255, 255, 255))
    if a.subtitle:
        outlined(d, a.subtitle, BIG // 2 + 40, 48, (235, 60, 40))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle")
    ap.add_argument("--bottom")
    ap.add_argument("--shot")
    ap.add_argument("--crop")
    ap.add_argument("--out", default="preview.png")
    a = ap.parse_args()
    img = from_shot(a) if a.shot else card(a)
    img.convert("RGB").resize((256, 256), Image.LANCZOS).save(a.out, optimize=True)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
