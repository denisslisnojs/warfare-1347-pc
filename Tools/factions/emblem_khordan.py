import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "factions", "khordan", "emblem.png")
FINAL = 1024
K = 4
S = FINAL * K


def col(rgb):
    return np.array(rgb, np.float32) / 255.0


SKY_TOP = col((8, 64, 74))
SKY_LOW = col((38, 138, 138))
GLOW = col((255, 214, 140))
GOLD = col((222, 168, 72))
GOLD_LIGHT = col((250, 222, 150))
BRONZE = col((168, 112, 48))
HILL_FAR = col((16, 92, 96))
HILL_MID = col((10, 70, 76))
HILL_NEAR = col((6, 50, 56))

yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / S
cx, cy, R = 0.5, 0.6, 0.155

t = np.clip(yy / cy, 0, 1) ** 1.3
img = SKY_TOP[None, None, :] * (1 - t[..., None]) + SKY_LOW[None, None, :] * t[..., None]
d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
glow = np.exp(-((d / 0.33) ** 2)) * 0.55
img = img * (1 - glow[..., None]) + GLOW[None, None, :] * glow[..., None]


def paste(mask, color):
    global img
    m = mask[..., None]
    img = img * (1 - m) + color * m


def poly_mask(points):
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).polygon([(x * S, y * S) for x, y in points], fill=255)
    return np.asarray(m, np.float32) / 255.0


for k in range(9):
    a = math.pi * (k + 0.5) / 9
    long = k % 2 == 0
    r0, r1 = R * 1.16, R * (2.15 if long else 1.72)
    w = 0.085 if long else 0.06
    base_l = (cx - math.cos(a - w) * r0, cy - math.sin(a - w) * r0)
    base_r = (cx - math.cos(a + w) * r0, cy - math.sin(a + w) * r0)
    tip = (cx - math.cos(a) * r1, cy - math.sin(a) * r1)
    mask = poly_mask([base_l, tip, base_r])
    shade = np.clip(1 - (d - r0) / (r1 - r0), 0, 1)[..., None]
    paste(mask, GOLD * (0.82 + 0.18 * shade) + GOLD_LIGHT * 0.0)

sun = np.clip((R - d) * S / 2.0, 0, 1) * (yy <= cy + 0.002)
inner = np.clip(1 - d / R, 0, 1)
sun_col = GOLD[None, None, :] * (1 - inner[..., None]) + GOLD_LIGHT[None, None, :] * inner[..., None]
img = img * (1 - sun[..., None]) + sun_col * sun[..., None]
rim = np.clip(1 - np.abs(d - R) * S / 6.0, 0, 1) * (yy <= cy)
paste(rim * 0.6, BRONZE)


def hills(base, amp, freq, phase, color):
    h = base + amp * np.sin(xx * math.pi * 2 * freq + phase) + amp * 0.4 * np.sin(xx * math.pi * 2 * freq * 2.3 + phase * 1.7)
    edge = np.clip((yy - h) * S / 2.0, 0, 1)
    paste(edge, color)


hills(cy - 0.004, 0.012, 1.2, 0.6, HILL_FAR)
hills(cy + 0.05, 0.02, 0.9, 2.1, HILL_MID)
hills(cy + 0.12, 0.025, 0.7, 4.0, HILL_NEAR)
line = np.clip(1 - np.abs(yy - (cy + 0.004 + 0.012 * np.sin(xx * math.pi * 2 * 1.2 + 0.6) + 0.0048 * np.sin(xx * math.pi * 2 * 2.76 + 1.02))) * S / 3.0, 0, 1)
paste(line * (np.abs(xx - cx) < 0.36) * 0.85, GOLD)

center = 0.5
dc = np.sqrt((xx - center) ** 2 + (yy - center) ** 2)
outer_r, ring_w = 0.47, 0.03
inside = np.clip((outer_r - ring_w - dc) * S / 2.0, 0, 1)
ring = np.clip((outer_r - dc) * S / 2.0, 0, 1) - inside
ring_shade = 0.75 + 0.25 * np.clip(1 - (yy - 0.03) / 0.94, 0, 1)
ring_col = GOLD[None, None, :] * ring_shade[..., None]
thin = np.clip(1 - np.abs(dc - (outer_r - ring_w - 0.012)) * S / 3.0, 0, 1)
alpha = np.clip((outer_r - dc) * S / 2.0, 0, 1)
out = img * inside[..., None] + ring_col * ring[..., None]
out = out * (1 - thin[..., None] * 0.9) + GOLD_LIGHT[None, None, :] * thin[..., None] * 0.9
rgba = np.concatenate([np.clip(out, 0, 1), alpha[..., None]], -1)
im = Image.fromarray((rgba * 255).astype(np.uint8), "RGBA").resize((FINAL, FINAL), Image.LANCZOS)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
im.save(OUT)
print(OUT)
