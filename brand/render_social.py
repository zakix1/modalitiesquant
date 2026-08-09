"""Render the two share cards: one square, one landscape 1200x628.

These are the images that appear when the site is pasted into LinkedIn, X,
WhatsApp, Slack or an email preview. They are the only part of the brand most
people see before they decide whether to click, so they carry the name and the
one line that says what the thing is — a bare logo on a dark square tells a
stranger nothing.

    python render_social.py

Landscape is 1200x628 as asked. Note that the Open Graph convention is 1200x630
(1.91:1); 628 is two pixels shorter and still inside every platform's accepted
ratio, so nothing crops — it is simply a slightly different rectangle.

Text is drawn with Segoe UI because the site's Space Grotesk and Inter are
loaded from Google Fonts and are not installed here. Pillow silently falls back
to a bitmap default if a font path is missing, which is why load_font() raises
instead.
"""

import os

from PIL import Image, ImageDraw, ImageFont

from render_png import CYAN, GREEN, render_mark

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "social")

GROUND = (0x06, 0x0B, 0x13)
INK = (0xE8, 0xEA, 0xED)
INK2 = (0x90, 0xA4, 0xB4)
INK3 = (0x54, 0x6E, 0x7A)

FONTS = {
    "bold": "C:/Windows/Fonts/segoeuib.ttf",
    "semi": "C:/Windows/Fonts/segoeuisl.ttf",
    "regular": "C:/Windows/Fonts/segoeui.ttf",
}


def load_font(kind, size):
    path = FONTS[kind]
    if not os.path.exists(path):
        raise SystemExit(
            f"font not found: {path}\n"
            "Pillow would fall back to a 10px bitmap face and the card would "
            "ship looking broken, so this stops instead.")
    return ImageFont.truetype(path, size)


def ground(w, h, glow_at, glow_r):
    """Dark ground with one soft cyan bloom behind the mark."""
    img = Image.new("RGB", (w, h), GROUND)
    gx, gy = glow_at
    glow = Image.new("L", (w, h), 0)
    gd = ImageDraw.Draw(glow)
    rings = 42
    for i in range(rings, 0, -1):
        r = glow_r * i / rings
        gd.ellipse([gx - r, gy - r, gx + r, gy + r], fill=int(46 * (1 - i / rings) ** 1.7))
    tint = Image.new("RGB", (w, h), (0x0E, 0x4A, 0x6E))
    return Image.composite(tint, img, glow)


def accent_bar(img, height):
    """A cyan-to-green rule along the bottom: the mark's own two colours."""
    w, h = img.size
    bar = Image.new("RGB", (w, height))
    px = bar.load()
    for x in range(w):
        t = x / (w - 1)
        px[x, 0] = tuple(int(CYAN[i] + (GREEN[i] - CYAN[i]) * t) for i in range(3))
    for y in range(1, height):
        bar.paste(bar.crop((0, 0, w, 1)), (0, y))
    img.paste(bar, (0, h - height))


def wordmark(draw, xy, size, anchor="ls"):
    """ModalitiesQuant, with Quant in the accent — as on the site."""
    f = load_font("bold", size)
    x, y = xy
    a, b = "Modalities", "Quant"
    if anchor == "ms":                       # centre the pair on x
        total = draw.textlength(a, font=f) + draw.textlength(b, font=f)
        x -= total / 2
    draw.text((x, y), a, font=f, fill=INK, anchor="ls")
    draw.text((x + draw.textlength(a, font=f), y), b, font=f, fill=CYAN, anchor="ls")


def landscape(mark):
    W, H = 1200, 628
    img = ground(W, H, (250, H // 2), 470)
    d = ImageDraw.Draw(img)

    m = mark.resize((268, 268), Image.LANCZOS)
    img.paste(m, (86, 166), m)

    x, right = 412, W - 86
    wordmark(d, (x, 292), 74)
    d.text((x, 348), "From biology to markets — in one desktop app.",
           font=load_font("semi", 31), fill=INK2, anchor="ls")
    d.text((x, 400), "Protein function · Medical diagnosis · DNA genomics · Nash-equilibrium markets",
           font=load_font("regular", 20), fill=INK3, anchor="ls")

    # Footer row. Without it the bottom-right quarter of the card is empty,
    # which reads as a cropped image rather than a composition.
    d.line([(x, 494), (right, 494)], fill=(0x1B, 0x2C, 0x42), width=1)
    d.text((x, 540), "OFFLINE  ·  PERPETUAL LICENCE  ·  WINDOWS",
           font=load_font("semi", 19), fill=CYAN, anchor="ls")
    d.text((right, 540), "zakix1.github.io/modalitiesquant",
           font=load_font("regular", 19), fill=INK3, anchor="rs")

    accent_bar(img, 7)
    return img


def square(mark):
    W = H = 1200
    img = ground(W, H, (W // 2, 415), 560)
    d = ImageDraw.Draw(img)

    m = mark.resize((470, 470), Image.LANCZOS)
    img.paste(m, ((W - 470) // 2, 178), m)

    wordmark(d, (W // 2, 800), 104, anchor="ms")
    d.text((W // 2, 866), "From biology to markets — in one desktop app.",
           font=load_font("semi", 38), fill=INK2, anchor="ms")
    d.text((W // 2, 928), "Protein function · Medical diagnosis · DNA genomics · Nash-equilibrium markets",
           font=load_font("regular", 24), fill=INK3, anchor="ms")

    d.text((W // 2, 1036), "OFFLINE  ·  PERPETUAL LICENCE  ·  WINDOWS",
           font=load_font("semi", 24), fill=CYAN, anchor="ms")
    d.text((W // 2, 1102), "zakix1.github.io/modalitiesquant",
           font=load_font("regular", 22), fill=INK3, anchor="ms")

    accent_bar(img, 8)
    return img


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    mark = render_mark()

    for name, img in (("og-landscape-1200x628", landscape(mark)),
                      ("og-square-1200x1200", square(mark))):
        p = os.path.join(OUT, f"{name}.png")
        img.save(p, optimize=True)
        print(f"  {img.size[0]}x{img.size[1]}  {os.path.getsize(p):>8,} B  social/{name}.png")
