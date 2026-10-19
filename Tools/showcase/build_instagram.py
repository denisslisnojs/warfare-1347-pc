import json
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR = os.path.join(ROOT, "docs", "showcase", "instagram")
FONTS = os.path.join(ROOT, "Assets", "Resources", "Fonts")
W, H = 1080, 1350
MARGIN = 64
BG = (23, 17, 13)
GOLD = (201, 163, 91)
GOLD_DARK = (122, 96, 52)
CREAM = (239, 227, 200)
TEXT = (226, 216, 194)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def background():
    img = Image.new("RGB", (W, H), BG)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((-200, -300, W + 200, H * 0.75), fill=60)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    warm = Image.new("RGB", (W, H), (58, 40, 26))
    return Image.composite(warm, img, glow)


def spaced(draw, xy, text, fnt, fill, spacing):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + spacing
    return x


def wrap(draw, text, fnt, width):
    lines, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if draw.textlength(test, font=fnt) <= width:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def framed(canvas, src, crop, box, label=None, fit=False):
    x0, y0, x1, y1 = box
    img = Image.open(os.path.join(DIR, "raw", src)).convert("RGB").crop(tuple(crop))
    tw, th = x1 - x0 - 12, y1 - y0 - 12
    scale = (min if fit else max)(tw / img.width, th / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    d = ImageDraw.Draw(canvas)
    d.rectangle(box, fill=(14, 10, 8), outline=GOLD_DARK, width=2)
    if fit:
        canvas.paste(img, (x0 + 6 + (tw - img.width) // 2, y0 + 6 + (th - img.height) // 2))
    else:
        left, top = (img.width - tw) // 2, (img.height - th) // 2
        canvas.paste(img.crop((left, top, left + tw, top + th)), (x0 + 6, y0 + 6))
    if label:
        f = font("AlegreyaSC-Regular.ttf", 26)
        tw2 = d.textlength(label, font=f)
        pad = 14
        lx, ly = x0 + 20, y1 - 58
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(overlay).rectangle((lx, ly, lx + tw2 + pad * 2, ly + 40), fill=(18, 13, 10, 205))
        canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB"))
        d = ImageDraw.Draw(canvas)
        d.text((lx + pad, ly + 4), label, font=f, fill=GOLD)


def slide(data, index, total, footer):
    canvas = background()
    d = ImageDraw.Draw(canvas)
    y = 64
    spaced(d, (MARGIN, y), data["kicker"].upper(), font("AlegreyaSC-Regular.ttf", 26), GOLD, 3)
    y += 44
    cover = data["layout"] == "cover"
    title_font = font("AlegreyaSC-Bold.ttf", 92 if cover else 66)
    d.text((MARGIN, y), data["title"], font=title_font, fill=CREAM)
    y += 112 if cover else 86
    d.line((MARGIN, y, W - MARGIN, y), fill=GOLD_DARK, width=2)
    y += 30
    body = font("Alegreya.ttf", 31)
    lines = []
    for b in data["bullets"]:
        lines.append(wrap(d, b, body, W - MARGIN * 2 - 34))
    text_h = sum(len(l) for l in lines) * 42 + (len(lines) - 1) * 16
    img_bottom = H - 110 - text_h - 36
    images = data["images"]
    if data["layout"] in ("cover", "single"):
        framed(canvas, images[0]["src"], images[0]["crop"], (MARGIN, y, W - MARGIN, img_bottom), images[0].get("label"), images[0].get("fit", False))
    elif data["layout"] == "stack":
        mid = (y + img_bottom) // 2
        framed(canvas, images[0]["src"], images[0]["crop"], (MARGIN, y, W - MARGIN, mid - 8), images[0].get("label"))
        framed(canvas, images[1]["src"], images[1]["crop"], (MARGIN, mid + 8, W - MARGIN, img_bottom), images[1].get("label"))
    else:
        mx, my = W // 2, (y + img_bottom) // 2
        boxes = [(MARGIN, y, mx - 8, my - 8), (mx + 8, y, W - MARGIN, my - 8), (MARGIN, my + 8, mx - 8, img_bottom), (mx + 8, my + 8, W - MARGIN, img_bottom)]
        for im, box in zip(images, boxes):
            framed(canvas, im["src"], im["crop"], box, im.get("label"))
    d = ImageDraw.Draw(canvas)
    ty = img_bottom + 36
    for block in lines:
        d.ellipse((MARGIN + 4, ty + 15, MARGIN + 14, ty + 25), fill=GOLD)
        for line in block:
            d.text((MARGIN + 34, ty), line, font=body, fill=TEXT)
            ty += 42
        ty += 16
    small = font("AlegreyaSC-Regular.ttf", 24)
    d.line((MARGIN, H - 74, W - MARGIN, H - 74), fill=GOLD_DARK, width=1)
    d.text((MARGIN, H - 60), f"{index}/{total}", font=small, fill=GOLD_DARK)
    fw = d.textlength(footer, font=small)
    d.text((W - MARGIN - fw, H - 60), footer, font=small, fill=GOLD)
    canvas.save(os.path.join(DIR, data["file"]), quality=92)
    print(data["file"], "text bottom", ty)


cfg = json.load(open(os.path.join(DIR, "slides.json"), encoding="utf-8"))
for i, s in enumerate(cfg["slides"], 1):
    slide(s, i, len(cfg["slides"]), cfg["footer"])
