import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "ArtSource", "ui")
OUT = os.path.join(ROOT, "Assets", "StreamingAssets", "Data", "world", "ui")

PIECES = {
    "ui_panel": {"width": 640, "border": (100, 100, 100, 100)},
    "ui_button_hover": {"height": 64, "border": (195, 40, 195, 40)},
    "ui_title": {"height": 72, "border": (333, 30, 333, 30)},
    "ui_divider": {"width": 600, "border": (0, 0, 0, 0)},
}


def is_png(path):
    with open(path, "rb") as f:
        return f.read(8) == b"\x89PNG\r\n\x1a\n"


def trim(im):
    box = im.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
    return im.crop(box) if box else im


def fit(im, spec):
    k = spec["width"] / im.width if "width" in spec else spec["height"] / im.height
    size = (max(1, round(im.width * k)), max(1, round(im.height * k)))
    border = [max(0, round(b * k)) for b in spec["border"]]
    return im.resize(size, Image.LANCZOS), border


def darker(im):
    rgb = ImageEnhance.Brightness(im.convert("RGB")).enhance(0.62)
    rgb = ImageEnhance.Color(rgb).enhance(0.85)
    out = rgb.convert("RGBA")
    out.putalpha(im.getchannel("A"))
    return out


slices = {}
for name, spec in PIECES.items():
    path = os.path.join(SRC, name + ".png")
    if not os.path.exists(path) or not is_png(path):
        print(f"skip {name}: missing or not a PNG")
        continue
    im, border = fit(trim(Image.open(path).convert("RGBA")), spec)
    im.save(os.path.join(OUT, name + ".png"), optimize=True)
    slices[name] = border
    print(f"{name}: {im.size}, border {border}")

normal = os.path.join(SRC, "ui_button.png")
spec = PIECES["ui_button_hover"]
if os.path.exists(normal) and is_png(normal):
    im, border = fit(trim(Image.open(normal).convert("RGBA")), spec)
    source = "ui_button.png"
elif "ui_button_hover" in slices:
    im, border = darker(Image.open(os.path.join(OUT, "ui_button_hover.png")).convert("RGBA")), slices["ui_button_hover"]
    source = "darkened ui_button_hover.png"
else:
    im = None
if im is not None:
    im.save(os.path.join(OUT, "ui_button.png"), optimize=True)
    slices["ui_button"] = border
    print(f"ui_button: {im.size} from {source}")

ICONS = os.path.join(OUT, "icons")
os.makedirs(ICONS, exist_ok=True)
for name in sorted(os.listdir(SRC)):
    path = os.path.join(SRC, name)
    if not (name.startswith("icon_") and name.endswith(".png")) or not is_png(path):
        continue
    im = trim(Image.open(path).convert("RGBA"))
    side = max(im.width, im.height)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
    square.resize((128, 128), Image.LANCZOS).save(os.path.join(ICONS, name), optimize=True)
    print(f"icon {name}")



def square_icon(im, path):
    side = max(im.width, im.height)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
    square.resize((128, 128), Image.LANCZOS).save(path, optimize=True)


def split_sheet(path, spec):
    im = Image.open(path).convert("RGBA")
    a = np.array(im)[..., 3]
    lab = Image.fromarray((a > 20).astype(np.int32), "I")
    arr = np.array(lab)
    label = 2
    while True:
        todo = np.argwhere(arr == 1)
        if len(todo) == 0:
            break
        y, x = todo[0]
        ImageDraw.floodfill(lab, (int(x), int(y)), label)
        arr = np.array(lab)
        label += 1
    cw, ch = im.width / spec["cols"], im.height / spec["rows"]
    owner = {}
    for l in range(2, label):
        ys, xs = np.nonzero(arr == l)
        cell = int(ys.mean() // ch) * spec["cols"] + int(xs.mean() // cw)
        owner.setdefault(cell, []).append(l)
    for cell, name in enumerate(spec["order"]):
        keep = np.isin(arr, owner.get(cell, []))
        if not keep.any():
            print(f"sheet cell {cell + 1} ({name}) is empty")
            continue
        rgba = np.array(im)
        rgba[..., 3] = np.where(keep, rgba[..., 3], 0)
        ys, xs = np.nonzero(keep)
        piece = Image.fromarray(rgba).crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        square_icon(piece, os.path.join(ICONS, spec["prefix"] + name + ".png"))
    print(f"sheet {os.path.basename(path)}: {len(spec['order'])} icons, {label - 2} pieces")


for name in sorted(os.listdir(SRC)):
    if name.endswith(".json"):
        png = os.path.join(SRC, name[:-5] + ".png")
        if os.path.exists(png) and is_png(png):
            split_sheet(png, json.load(open(os.path.join(SRC, name), encoding="utf-8")))

json.dump(slices, open(os.path.join(OUT, "ui_slices.json"), "w"), indent=1)
print("slices:", slices)
