import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "Assets", "StreamingAssets", "Data", "world", "ui")
os.makedirs(OUT, exist_ok=True)
SS = 4


def cubic(p0, p1, p2, p3, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return pts


def mirror(pts, cx=256):
    return [(2 * cx - x, y) for x, y in pts]


def save_mask(mask, size, name, rgb=None):
    small = mask.resize(size, Image.LANCZOS)
    a = np.asarray(small, np.float32) / 255.0
    col = np.ones((size[1], size[0], 3), np.float32) if rgb is None else rgb
    img = np.concatenate([col, a[..., None]], -1)
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, name), optimize=True)
    print(name)


def shield():
    w, h = 96 * SS, 116 * SS
    def outline(inset):
        i = inset * SS
        top, side = 5 * SS + i, 5 * SS + i
        right = w - side
        mid = w / 2
        pts = [(side, top), (right, top), (right, h * 0.58)]
        pts += cubic((right, h * 0.58), (right, h * 0.8), (mid + 18 * SS, h * 0.9), (mid, h - 4 * SS - i * 1.6))
        pts += cubic((mid, h - 4 * SS - i * 1.6), (mid - 18 * SS, h * 0.9), (side, h * 0.8), (side, h * 0.58))
        return pts
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon(outline(0), fill=255)
    inner = Image.new("L", (w, h), 0)
    ImageDraw.Draw(inner).polygon(outline(4.5), fill=255)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    shade = 1.0 - 0.28 * (yy / h) - 0.1 * (xx / w)
    shade += 0.12 * np.exp(-((xx - w * 0.3) ** 2 + (yy - h * 0.18) ** 2) / (2 * (w * 0.22) ** 2))
    small_shade = np.asarray(Image.fromarray((np.clip(shade, 0, 1) * 255).astype(np.uint8)).resize((96, 116), Image.LANCZOS), np.float32) / 255.0
    save_mask(inner, (96, 116), "shield_fill.png", np.repeat(small_shade[..., None], 3, -1))
    edge = np.asarray(m, np.float32) - np.asarray(inner, np.float32)
    save_mask(Image.fromarray(np.clip(edge, 0, 255).astype(np.uint8)), (96, 116), "shield_edge.png")
    shadow = m.filter(ImageFilter.GaussianBlur(5 * SS))
    save_mask(shadow, (96, 116), "shield_shadow.png", np.zeros((116, 96, 3), np.float32))


def banner():
    w, h = 96 * SS, 128 * SS
    def cloth(inset):
        i = inset * SS
        left, right, top = 12 * SS + i, w - 12 * SS - i, 9 * SS + i * 0.4
        mid = w / 2
        return [(left, top), (right, top), (right, h * 0.74 - i * 0.3), (mid, h - 5 * SS - i * 1.8), (left, h * 0.74 - i * 0.3)]
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon(cloth(0), fill=255)
    inner = Image.new("L", (w, h), 0)
    ImageDraw.Draw(inner).polygon(cloth(3.2), fill=255)
    rod = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(rod)
    d.rectangle((4 * SS, 5 * SS, w - 4 * SS, 10 * SS), fill=255)
    for cx in (5 * SS, w - 5 * SS):
        d.ellipse((cx - 4 * SS, 3.5 * SS, cx + 4 * SS, 11.5 * SS), fill=255)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    shade = 0.9 - 0.22 * (yy / h) + 0.07 * np.sin(xx / w * math.pi * 3.0 + 0.6)
    shade -= 0.12 * np.exp(-((yy - 12 * SS) ** 2) / (2 * (6 * SS) ** 2))
    small_shade = np.asarray(Image.fromarray((np.clip(shade, 0, 1) * 255).astype(np.uint8)).resize((96, 128), Image.LANCZOS), np.float32) / 255.0
    save_mask(inner, (96, 128), "banner_fill.png", np.repeat(small_shade[..., None], 3, -1))
    edge = np.maximum(np.asarray(m, np.float32) - np.asarray(inner, np.float32), np.asarray(rod, np.float32))
    save_mask(Image.fromarray(np.clip(edge, 0, 255).astype(np.uint8)), (96, 128), "banner_edge.png")
    both = Image.fromarray(np.maximum(np.asarray(m), np.asarray(rod)))
    shadow = both.filter(ImageFilter.GaussianBlur(4 * SS))
    save_mask(shadow, (96, 128), "banner_shadow.png", np.zeros((128, 96, 3), np.float32))


def ribbon():
    w, h = 256, 48
    W, H = w * SS, h * SS
    m = Image.new("L", (W, H), 0)
    tip = 26 * SS
    ImageDraw.Draw(m).polygon([(0, 6 * SS), (W - tip, 6 * SS), (W - 2 * SS, H / 2), (W - tip, H - 6 * SS), (0, H - 6 * SS)], fill=255)
    ImageDraw.Draw(m).polygon([(W - tip - 12 * SS, 6 * SS), (W - tip + 2 * SS, 6 * SS), (W - 14 * SS, H / 2), (W - tip + 2 * SS, H - 6 * SS), (W - tip - 12 * SS, H - 6 * SS), (W - 22 * SS - tip, H / 2)], fill=0)
    yy = np.mgrid[0:h, 0:w][0].astype(np.float32)
    shade = 0.2 + 0.13 * (1 - np.abs(yy / h - 0.5) * 2)
    col = np.repeat(shade[..., None], 3, -1)
    small = np.asarray(m.resize((w, h), Image.LANCZOS), np.float32) / 255.0
    img = np.concatenate([col, (small * 0.88)[..., None]], -1)
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "ribbon.png"), optimize=True)
    print("ribbon.png")


def canvas():
    m = Image.new("L", (512, 512), 0)
    return m, ImageDraw.Draw(m)


def star(d, cx, cy, ro, ri, n, rot=-90):
    pts = []
    for k in range(n * 2):
        a = math.radians(rot + k * 180 / n)
        r = ro if k % 2 == 0 else ri
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=255)


def emblem_khordan():
    m, d = canvas()
    cx, cy = 256, 318
    d.pieslice([cx - 112, cy - 112, cx + 112, cy + 112], 180, 360, fill=255)
    for k in range(9):
        a = math.radians(180 + 10 + k * 20)
        da = math.radians(5.2)
        p = [(cx + 138 * math.cos(a - da * 0.55), cy + 138 * math.sin(a - da * 0.55)), (cx + 236 * math.cos(a), cy + 236 * math.sin(a)), (cx + 138 * math.cos(a + da * 0.55), cy + 138 * math.sin(a + da * 0.55))]
        d.polygon(p, fill=255)
    d.rectangle([40, cy + 18, 472, cy + 34], fill=255)
    hills = [(40, 470)] + cubic((40, 400), (120, 350), (200, 360), (256, 400), 30) + cubic((256, 400), (320, 352), (400, 350), (472, 405), 30) + [(472, 470)]
    d.polygon(hills, fill=255)
    return m


def emblem_azhar():
    m, d = canvas()
    cx, cy = 256, 256
    d.ellipse([cx - 214, cy - 214, cx + 214, cy + 214], fill=255)
    d.ellipse([cx - 190, cy - 190, cx + 190, cy + 190], fill=0)
    for k in range(16):
        a = math.radians(k * 22.5)
        da = math.radians(4.5)
        d.polygon([(cx + 212 * math.cos(a - da), cy + 212 * math.sin(a - da)), (cx + 252 * math.cos(a), cy + 252 * math.sin(a)), (cx + 212 * math.cos(a + da), cy + 212 * math.sin(a + da))], fill=255)
    wing = [(238, 218)] + cubic((238, 218), (200, 170), (130, 120), (78, 96), 20)
    wing += [(92, 150), (82, 162), (104, 200), (96, 214), (124, 240), (120, 256), (152, 272), (150, 288), (184, 296), (196, 310)]
    wing += [(232, 300)]
    d.polygon(wing, fill=255)
    d.polygon(mirror(wing), fill=255)
    d.ellipse([214, 196, 298, 352], fill=255)
    d.ellipse([224, 140, 288, 204], fill=255)
    d.polygon([(280, 160), (318, 176), (284, 190)], fill=255)
    d.ellipse([262, 160, 274, 172], fill=0)
    tail = [(226, 330), (286, 330), (318, 412), (296, 404), (282, 418), (256, 404), (230, 418), (216, 404), (194, 412)]
    d.polygon(tail, fill=255)
    return m


def emblem_grim():
    m, d = canvas()
    cx, cy, R = 256, 262, 214
    for side in (1, -1):
        for k in range(9):
            t = 0.38 + k * 0.27
            x, y = cx + side * R * math.sin(t), cy + R * math.cos(t)
            tx, ty = side * math.cos(t), -math.sin(t)
            nx, ny = -ty, tx
            off = 16 if k % 2 else -16
            bx, by = x + nx * off * side, y + ny * off * side
            L, Wd = 46, 17
            tip = (bx + tx * L, by + ty * L)
            base = (bx - tx * 8, by - ty * 8)
            mid1 = (bx + tx * L * 0.45 + nx * Wd, by + ty * L * 0.45 + ny * Wd)
            mid2 = (bx + tx * L * 0.45 - nx * Wd, by + ty * L * 0.45 - ny * Wd)
            d.polygon(cubic(base, mid1, mid1, tip, 10) + cubic(tip, mid2, mid2, base, 10), fill=255)
        arc = [(cx + side * (R - 2) * math.sin(0.3 + i * 0.025), cy + (R - 2) * math.cos(0.3 + i * 0.025)) for i in range(96)]
        d.line(arc, fill=255, width=9)
    d.polygon([(232, 470), (256, 440), (280, 470), (268, 482), (256, 466), (244, 482)], fill=255)
    wing = [(236, 236)] + cubic((236, 236), (204, 190), (150, 150), (104, 92), 20)
    wing += [(96, 132), (122, 142), (88, 170), (120, 182), (86, 214), (122, 222), (94, 256), (132, 258), (112, 292), (150, 288), (142, 322), (182, 306), (186, 334), (220, 312)]
    d.polygon(wing, fill=255)
    d.polygon(mirror(wing), fill=255)
    d.ellipse([218, 210, 294, 350], fill=255)
    d.ellipse([228, 142, 286, 200], fill=255)
    d.rounded_rectangle([244, 180, 268, 230], radius=10, fill=255)
    d.polygon([(278, 158), (316, 170), (300, 184), (282, 186)], fill=255)
    d.ellipse([260, 160, 271, 171], fill=0)
    d.polygon([(232, 336), (280, 336), (306, 402), (280, 392), (256, 410), (232, 392), (206, 402)], fill=255)
    d.polygon([(226, 330), (206, 360), (190, 362), (212, 370), (234, 346)], fill=255)
    d.polygon(mirror([(226, 330), (206, 360), (190, 362), (212, 370), (234, 346)]), fill=255)
    return m


def emblem_vinland():
    m, d = canvas()
    body = cubic((120, 300), (170, 236), (300, 216), (352, 236), 24) + cubic((352, 236), (396, 256), (372, 318), (300, 334), 24)
    body += cubic((300, 334), (230, 348), (160, 336), (120, 300), 24)
    d.polygon(body, fill=255)
    d.polygon([(318, 250), (330, 196), (372, 170), (404, 186), (398, 234), (360, 262)], fill=255)
    d.ellipse([340, 150, 410, 214], fill=255)
    d.polygon([(398, 168), (488, 196), (470, 206), (402, 206)], fill=255)
    d.polygon([(402, 204), (470, 206), (404, 220)], fill=255)
    d.ellipse([370, 168, 384, 182], fill=0)
    wing = [(330, 236)] + cubic((330, 236), (290, 160), (230, 90), (150, 40), 20)
    wing += [(176, 92), (110, 84), (160, 128), (96, 136), (160, 170), (104, 190), (180, 212), (140, 236), (230, 250)]
    d.polygon(wing, fill=255)
    tail = [(150, 296), (34, 330), (44, 348), (30, 366), (64, 364), (60, 384), (176, 330)]
    d.polygon(tail, fill=255)
    for x in (250, 290):
        d.polygon([(x, 330), (x - 10, 392), (x + 6, 392), (x + 14, 330)], fill=255)
        d.polygon([(x - 24, 392), (x + 22, 392), (x + 18, 402), (x - 20, 402)], fill=255)
    top = cubic((36, 440), (110, 418), (170, 418), (230, 436), 16) + cubic((230, 436), (300, 456), (380, 452), (476, 420), 16)
    bot = cubic((476, 470), (380, 492), (300, 494), (230, 476), 16) + cubic((230, 476), (170, 458), (110, 458), (36, 476), 16)
    d.polygon(top + [(476, 470)] + bot, fill=255)
    crest = cubic((96, 430), (70, 380), (130, 360), (160, 392), 16) + cubic((160, 392), (176, 410), (150, 428), (136, 414), 12)
    crest += cubic((136, 414), (120, 398), (104, 410), (118, 432), 12)
    d.polygon(crest, fill=255)
    return m

def emblem_varden():
    m, d = canvas()
    star(d, 256, 104, 76, 30, 8, -90)
    d.ellipse([150, 250, 420, 390], fill=255)
    d.ellipse([140, 228, 290, 350], fill=255)
    d.ellipse([60, 252, 196, 344], fill=255)
    d.ellipse([36, 282, 110, 334], fill=255)
    d.ellipse([110, 236, 150, 276], fill=255)
    d.ellipse([32, 290, 52, 310], fill=255)
    for x0, top in ((150, 330), (210, 340), (318, 330), (372, 320)):
        d.rounded_rectangle([x0, top, x0 + 46, 452], radius=16, fill=255)
        d.ellipse([x0 - 6, 432, x0 + 52, 462], fill=255)
    d.ellipse([360, 262, 440, 342], fill=255)
    d.polygon([(430, 290), (468, 300), (440, 316)], fill=255)
    return m


def emblem_vallerois():
    m, d = canvas()
    centre = cubic((222, 318), (180, 240), (204, 128), (256, 40), 30) + cubic((256, 40), (308, 128), (332, 240), (290, 318), 30)
    d.polygon(centre, fill=255)
    side = cubic((268, 330), (300, 236), (400, 150), (452, 196), 30) + cubic((452, 196), (488, 230), (462, 300), (412, 296), 24)
    side += cubic((412, 296), (436, 262), (418, 236), (392, 248), 20) + cubic((392, 248), (352, 268), (330, 312), (318, 340), 20)
    d.polygon(side, fill=255)
    d.polygon(mirror(side), fill=255)
    d.rounded_rectangle([132, 322, 380, 362], radius=10, fill=255)
    foot = cubic((236, 362), (226, 400), (240, 440), (256, 470), 20) + cubic((256, 470), (272, 440), (286, 400), (276, 362), 20)
    d.polygon(foot, fill=255)
    curl = cubic((236, 362), (200, 380), (160, 380), (150, 420), 20) + cubic((150, 420), (176, 400), (214, 410), (238, 392), 20)
    d.polygon(curl, fill=255)
    d.polygon(mirror(curl), fill=255)
    return m


shield()
banner()
ribbon()
for name, fn in (("vallerois", emblem_vallerois), ("varden", emblem_varden), ("khordan", emblem_khordan), ("azhar", emblem_azhar), ("grim", emblem_grim), ("vinland", emblem_vinland)):
    save_mask(fn(), (128, 128), f"emblem_{name}.png")

sheet = Image.new("RGBA", (6 * 140 + 20, 300), (60, 70, 60, 255))
cols = {"vallerois": (184, 26, 26), "varden": (31, 117, 51), "khordan": (224, 168, 41), "azhar": (117, 71, 36), "grim": (102, 36, 117), "vinland": (26, 46, 97)}
fill = Image.open(os.path.join(OUT, "shield_fill.png"))
for i, (name, c) in enumerate(cols.items()):
    f = np.asarray(fill, np.float32) / 255.0
    tinted = f.copy()
    tinted[..., :3] *= np.array(c) / 255.0
    sh = Image.fromarray((tinted * 255).astype(np.uint8), "RGBA")
    em = Image.open(os.path.join(OUT, f"emblem_{name}.png")).resize((64, 64), Image.LANCZOS)
    sheet.alpha_composite(sh, (20 + i * 140, 20))
    sheet.alpha_composite(em, (20 + i * 140 + 16, 36))
    big = Image.open(os.path.join(OUT, f"emblem_{name}.png"))
    sheet.alpha_composite(big, (10 + i * 140, 160))
sheet.save(os.path.join(ROOT, "docs", "style", "emblems_preview.png"))
print("sheet")
