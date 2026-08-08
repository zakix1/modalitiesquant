"""Render the ModalitiesQuant mark to PNG and ICO.

There is no SVG rasteriser on this machine — no ImageMagick, no Inkscape, no
cairosvg — so rather than add a dependency this redraws the mark from the same
numbers the SVG uses, with Pillow.

The geometry below is the single source of truth shared with logo.svg and
favicon.svg: pentagon vertices at 72 degrees on r=230, hexagon at 60 on r=160,
both centred on (256,256) in a 512 box. If you change one, change the other —
check_geometry() at the bottom re-derives the vertices from the angles and will
fail loudly if the numbers drift apart.

Everything is drawn at SS times final size and downsampled with LANCZOS; that
supersampling is what stands in for the renderer's antialiasing.

    python render_png.py
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw

SS = 6                      # supersample factor over the 512 unit box
CANVAS = 512 * SS
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "png")

CYAN, BLUE, PALE = (0x00, 0xC6, 0xFF), (0x1E, 0x88, 0xE5), (0x7F, 0xDC, 0xFF)
GREEN, MINT, SEA = (0x00, 0xE6, 0x76), (0x3A, 0xD3, 0x9A), (0x5C, 0xE0, 0xA0)

PENTAGON = [(256, 26), (474.74, 184.93), (391.19, 442.07),
            (120.81, 442.07), (37.26, 184.93)]
HEXAGON = [(256, 96), (394.56, 176), (394.56, 336),
           (256, 416), (117.44, 336), (117.44, 176)]
BONDS = [((256, 46), (256, 88)),
         ((455.72, 191.11), (415.78, 204.09)),
         ((379.43, 425.89), (354.75, 391.91)),
         ((132.57, 425.89), (157.25, 391.91)),
         ((56.28, 191.11), (96.22, 204.09))]


# ── painting ────────────────────────────────────────────────────────────────

def new_mask(size):
    m = Image.new("L", (size, size), 0)
    return m, ImageDraw.Draw(m)


def paint(canvas, mask, spec, opacity=1.0):
    """Composite `mask` onto `canvas` filled with `spec`.

    spec is ("solid", rgb) or ("linear", (x1,y1,x2,y2), rgb0, rgb1). Linear
    gradients are resolved against the mask's own bounding box, matching SVG's
    default gradientUnits="objectBoundingBox" — which is why each is computed
    per shape rather than once for the whole image.
    """
    bbox = mask.getbbox()
    if bbox is None:
        return
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    sub = mask.crop(bbox)
    if opacity < 1.0:
        sub = sub.point(lambda a: int(a * opacity))

    if spec[0] == "solid":
        layer = Image.new("RGBA", (w, h), tuple(spec[1]) + (255,))
    else:
        _, (gx1, gy1, gx2, gy2), c0, c1 = spec
        u = np.linspace(0.0, 1.0, w, dtype=np.float32)[None, :]
        v = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]
        dx, dy = gx2 - gx1, gy2 - gy1
        denom = dx * dx + dy * dy
        t = np.clip(((u - gx1) * dx + (v - gy1) * dy) / denom, 0.0, 1.0)
        rgb = np.stack([c0[i] + (c1[i] - c0[i]) * t for i in range(3)], axis=-1)
        layer = Image.fromarray(rgb.astype(np.uint8), "RGB").convert("RGBA")

    layer.putalpha(sub)
    canvas.alpha_composite(layer, (x0, y0))


def stroke(draw, pts, width, closed=False, round_ends=True):
    """Polyline with round joins and caps.

    Pillow's joint="curve" rounds the interior joins but leaves the ends flat,
    so the endpoint discs are drawn explicitly — without them the trend line's
    tail and the helix strands end in visible square nibs.
    """
    p = [tuple(q) for q in pts]
    if closed:
        p = p + [p[0]]
    draw.line(p, fill=255, width=int(round(width)), joint="curve")
    r = width / 2.0
    verts = p if (closed or round_ends) else p[1:-1]
    for x, y in verts:
        draw.ellipse([x - r, y - r, x + r, y + r], fill=255)


def cubic(p0, c0, c1, p1, n=180):
    out = []
    for i in range(n + 1):
        t = i / n
        m = 1 - t
        out.append((m**3 * p0[0] + 3 * m*m*t * c0[0] + 3 * m*t*t * c1[0] + t**3 * p1[0],
                    m**3 * p0[1] + 3 * m*m*t * c0[1] + 3 * m*t*t * c1[1] + t**3 * p1[1]))
    return out


def quad(p0, c, p1, n=120):
    out = []
    for i in range(n + 1):
        t = i / n
        m = 1 - t
        out.append((m*m * p0[0] + 2 * m*t * c[0] + t*t * p1[0],
                    m*m * p0[1] + 2 * m*t * c[1] + t*t * p1[1]))
    return out


# ── the full mark ───────────────────────────────────────────────────────────

def render_mark(ss=SS):
    S = 512 * ss
    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    def sc(pts):
        return [(x * ss, y * ss) for x, y in pts]

    def w(v):
        return v * ss

    edge = ("linear", (0, 0, 1, 1), CYAN, BLUE)

    # Pentagon plate: the faint radial wash inside the outline.
    m, d = new_mask(S)
    d.polygon(sc(PENTAGON), fill=255)
    arr = np.asarray(m, dtype=np.float32) / 255.0
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    dist = np.sqrt(((xx - 0.5 * S) / (0.75 * S))**2 + ((yy - 0.42 * S) / (0.75 * S))**2)
    wash = np.clip(1.0 - dist, 0.0, 1.0) * 0.10 * arr
    plate = Image.new("RGBA", (S, S), CYAN + (0,))
    plate.putalpha(Image.fromarray((wash * 255).astype(np.uint8), "L"))
    canvas.alpha_composite(plate)
    del arr, yy, xx, dist, wash

    m, d = new_mask(S)
    stroke(d, sc(PENTAGON), w(12), closed=True)
    paint(canvas, m, edge)

    m, d = new_mask(S)
    for a, b in BONDS:
        stroke(d, sc([a, b]), w(5))
    paint(canvas, m, edge, opacity=0.55)

    m, d = new_mask(S)
    for x, y in sc(PENTAGON):
        r = w(11)
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    paint(canvas, m, ("solid", CYAN))

    m, d = new_mask(S)
    stroke(d, sc(HEXAGON), w(7), closed=True)
    paint(canvas, m, ("linear", (0, 0, 0, 1), PALE, BLUE), opacity=0.9)

    # Chart baseline and ticks.
    m, d = new_mask(S)
    stroke(d, sc([(150, 344), (372, 344)]), w(3))
    for x in (186, 240, 294, 348):
        stroke(d, sc([(x, 344), (x, 353)]), w(3))
    paint(canvas, m, ("solid", CYAN), opacity=0.28)

    # Helix strands.
    a = cubic((132, 208), (160, 208), (160, 304), (188, 304)) + \
        cubic((188, 304), (216, 304), (216, 208), (244, 208))
    b = cubic((132, 304), (160, 304), (160, 208), (188, 208)) + \
        cubic((188, 208), (216, 208), (216, 304), (244, 304))
    m, d = new_mask(S)
    stroke(d, sc(a), w(7))
    paint(canvas, m, ("linear", (0, 0, 1, 0), CYAN, SEA))
    m, d = new_mask(S)
    stroke(d, sc(b), w(7))
    paint(canvas, m, ("linear", (0, 0, 1, 0), BLUE, CYAN))

    # Base pairs.
    m, d = new_mask(S)
    for x, y0, y1 in ((132, 208, 304), (147, 222, 290), (188, 208, 304),
                      (229, 222, 290), (244, 208, 304)):
        stroke(d, sc([(x, y0), (x, y1)]), w(4.5))
    paint(canvas, m, ("solid", CYAN), opacity=0.62)

    # The strands converge on one node.
    m, d = new_mask(S)
    stroke(d, sc(quad((244, 208), (268, 210), (273, 251))), w(7))
    stroke(d, sc(quad((244, 304), (268, 302), (273, 261))), w(7))
    paint(canvas, m, ("solid", MINT))

    m, d = new_mask(S)
    r = w(9)
    d.ellipse([276 * ss - r, 256 * ss - r, 276 * ss + r, 256 * ss + r], fill=255)
    stroke(d, sc([(276, 256), (296, 238), (316, 252), (338, 210), (358, 190)]), w(8))
    d.polygon(sc([(372, 176), (348, 178), (370, 200)]), fill=255)
    for x, y0, y1 in ((292, 292, 338), (318, 268, 324), (344, 242, 308)):
        stroke(d, sc([(x, y0), (x, y1)]), w(3.5))
    paint(canvas, m, ("solid", GREEN))

    m, d = new_mask(S)
    for x, y, bw, bh in ((285, 300, 14, 30), (311, 276, 14, 40), (337, 250, 14, 50)):
        d.rounded_rectangle([x * ss, y * ss, (x + bw) * ss, (y + bh) * ss],
                            radius=w(3), fill=255)
    paint(canvas, m, ("solid", GREEN), opacity=0.92)

    return canvas


# ── the small cut ───────────────────────────────────────────────────────────

def render_small(ss=32):
    S = 64 * ss
    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    pent = [(32, 3), (59.58, 23.04), (49.05, 55.46), (14.95, 55.46), (4.42, 23.04)]
    hexa = [(32, 12), (49.32, 22), (49.32, 42), (32, 52), (14.68, 42), (14.68, 22)]

    def sc(pts):
        return [(x * ss, y * ss) for x, y in pts]

    m, d = new_mask(S)
    stroke(d, sc(pent), 3.6 * ss, closed=True)
    paint(canvas, m, ("linear", (0, 0, 1, 1), CYAN, BLUE))

    m, d = new_mask(S)
    for x, y in sc(pent):
        r = 3.2 * ss
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    paint(canvas, m, ("solid", CYAN))

    m, d = new_mask(S)
    stroke(d, sc(hexa), 2.8 * ss, closed=True)
    paint(canvas, m, ("solid", PALE))

    # Two segments, both climbing — see the note in favicon.svg.
    m, d = new_mask(S)
    stroke(d, sc([(18, 40.5), (28.5, 34.5), (36.9, 28)]), 3.8 * ss)
    d.polygon(sc([(43.15, 23.04), (39.56, 31.43), (34.14, 24.51)]), fill=255)
    paint(canvas, m, ("solid", GREEN))

    return canvas


def check_geometry():
    """Re-derive the vertex tables from the angles they claim to come from."""
    for name, table, n, r, start in (("pentagon", PENTAGON, 5, 230, -90),
                                     ("hexagon", HEXAGON, 6, 160, -90)):
        step = 360 / n
        for i, (gx, gy) in enumerate(table):
            ang = math.radians(start + i * step)
            ex, ey = 256 + r * math.cos(ang), 256 + r * math.sin(ang)
            if abs(ex - gx) > 0.02 or abs(ey - gy) > 0.02:
                raise SystemExit(
                    f"{name} vertex {i} drifted: table ({gx}, {gy}) "
                    f"but {r} at {start + i * step:g} deg gives ({ex:.2f}, {ey:.2f})")
    print("geometry: pentagon and hexagon match their stated angles and radii")


if __name__ == "__main__":
    check_geometry()
    os.makedirs(OUT, exist_ok=True)

    mark = render_mark()
    for size in (1024, 512, 256, 128):
        p = os.path.join(OUT, f"logo-{size}.png")
        mark.resize((size, size), Image.LANCZOS).save(p)
        print(f"  {os.path.getsize(p):>7,} B  png/logo-{size}.png")

    small = render_small()
    for size in (256, 128, 64, 48, 32, 16):
        p = os.path.join(OUT, f"mark-{size}.png")
        small.resize((size, size), Image.LANCZOS).save(p)
        print(f"  {os.path.getsize(p):>7,} B  png/mark-{size}.png")

    ico = os.path.join(os.path.dirname(OUT), "favicon.ico")
    small.resize((256, 256), Image.LANCZOS).save(
        ico, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"  {os.path.getsize(ico):>7,} B  favicon.ico  (6 sizes)")

    # iOS ignores SVG here and composites the icon onto its own ground, so this
    # one is a PNG with the site's background painted in rather than left
    # transparent — otherwise the mark lands on black on a home screen.
    touch = Image.new("RGBA", (180, 180), (0x06, 0x0B, 0x13, 255))
    touch.alpha_composite(mark.resize((146, 146), Image.LANCZOS), (17, 17))
    p = os.path.join(os.path.dirname(OUT), "apple-touch-icon.png")
    touch.convert("RGB").save(p)
    print(f"  {os.path.getsize(p):>7,} B  apple-touch-icon.png  (180, opaque)")
