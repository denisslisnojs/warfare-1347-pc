import json, os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "Assets", "StreamingAssets", "Data", "world")
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "Assets", "StreamingAssets", "Data", "world", "factions", "vallerois.json")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "docs", "factions", os.path.splitext(os.path.basename(src))[0] + "_settlements_preview.png")

meta = json.load(open(os.path.join(DATA, "world.json")))
data = json.load(open(src, encoding="utf-8"))
pts = [(s["lon"], s["lat"]) for k in ("towns", "castles", "villages") for s in data[k]]
box = data.get("previewBox") or (min(p[0] for p in pts) - 2.5, min(p[1] for p in pts) - 1.5, max(p[0] for p in pts) + 2.5, max(p[1] for p in pts) + 1.5)
color = Image.open(os.path.join(DATA, "color.png")).convert("RGB")
cs = meta["colorScale"]


def px(lon, lat):
    return ((lon - meta["lonMin"]) * meta["pxPerDegLat"] * meta["lonFactor"] * cs, (meta["latMax"] - lat) * meta["pxPerDegLat"] * cs)


x0, y0 = px(box[0], box[3])
x1, y1 = px(box[2], box[1])
crop = color.crop((int(x0), int(y0), int(x1), int(y1)))
k = max(2, min(4, round(2600 / crop.width)))
img = crop.resize((crop.width * k, crop.height * k), Image.BICUBIC)
d = ImageDraw.Draw(img)
font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)


def at(s):
    x, y = px(s["lon"], s["lat"])
    return (x - int(x0)) * k, (y - int(y0)) * k


def label(x, y, text, f, fill):
    for dx in (-2, 0, 2):
        for dy in (-2, 0, 2):
            d.text((x + dx, y + dy), text, font=f, fill=(20, 20, 30))
    d.text((x, y), text, font=f, fill=fill)


for s in data["villages"]:
    x, y = at(s)
    d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(240, 235, 200), outline=(40, 30, 20), width=2)
    label(x + 10, y - 10, s["name"], small, (250, 245, 220))
for s in data["castles"]:
    x, y = at(s)
    d.rectangle([x - 11, y - 11, x + 11, y + 11], fill=(150, 160, 175), outline=(20, 20, 30), width=3)
    label(x + 14, y + 4, s["name"], small, (210, 225, 255))
for s in data["towns"]:
    x, y = at(s)
    r = 20 if s.get("capital") else 15
    d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 185, 50), outline=(30, 40, 120), width=4)
    label(x + r + 6, y - 18, s["name"] + (" ★" if s.get("capital") else ""), font, (255, 220, 110))
d.rectangle([20, 20, 560, 150], fill=(25, 28, 40))
d.ellipse([40, 40, 70, 70], fill=(235, 185, 50), outline=(30, 40, 120), width=4)
label(85, 40, "город (★ — столица)", small, (255, 220, 110))
d.rectangle([44, 84, 66, 106], fill=(150, 160, 175), outline=(20, 20, 30), width=3)
label(85, 82, "замок", small, (210, 225, 255))
d.ellipse([48, 118, 62, 132], fill=(240, 235, 200), outline=(40, 30, 20), width=2)
label(85, 114, "деревня", small, (250, 245, 220))
img.save(out, optimize=True)
print(out, img.size)
