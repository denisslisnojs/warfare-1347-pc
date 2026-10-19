import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Assets", "StreamingAssets", "Data", "world", "detail")
os.makedirs(OUT, exist_ok=True)
N = 512
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / N


def fractal(beta, seed, lo=1.0, hi=None):
    r = np.random.default_rng(seed)
    f = np.fft.fft2(r.standard_normal((N, N)))
    fx = np.fft.fftfreq(N)[None, :] * N
    fy = np.fft.fftfreq(N)[:, None] * N
    k = np.sqrt(fx * fx + fy * fy)
    k[0, 0] = 1.0
    amp = k ** (-beta / 2.0)
    amp[k < lo] = 0.0
    if hi:
        amp[k > hi] = 0.0
    out = np.real(np.fft.ifft2(f * amp)).astype(np.float32)
    out -= out.min()
    return out / max(out.max(), 1e-6)


def voronoi(count, seed, jitter=1.0):
    r = np.random.default_rng(seed)
    side = int(np.ceil(np.sqrt(count)))
    g = (np.stack(np.meshgrid(np.arange(side), np.arange(side)), -1).reshape(-1, 2) + 0.5 + (r.random((side * side, 2)) - 0.5) * jitter) / side
    f1 = np.full((N, N), 9.0, np.float32)
    f2 = np.full((N, N), 9.0, np.float32)
    cell = np.zeros((N, N), np.int32)
    for i, (px, py) in enumerate(g):
        dx = np.abs(xx - px)
        dy = np.abs(yy - py)
        dx = np.minimum(dx, 1 - dx)
        dy = np.minimum(dy, 1 - dy)
        d = np.sqrt(dx * dx + dy * dy)
        closer = d < f1
        f2 = np.where(closer, f1, np.minimum(f2, d))
        cell = np.where(closer, i, cell)
        f1 = np.where(closer, d, f1)
    return f1 * side, f2 * side, cell, r.random(side * side)


def canopy(count, rmin, rmax, seed):
    r = np.random.default_rng(seed)
    h = np.zeros((N, N), np.float32)
    for px, py, rad in zip(r.random(count), r.random(count), r.uniform(rmin, rmax, count)):
        dx = np.abs(xx - px)
        dy = np.abs(yy - py)
        dx = np.minimum(dx, 1 - dx)
        dy = np.minimum(dy, 1 - dy)
        d2 = (dx * dx + dy * dy) / (rad * rad)
        h = np.maximum(h, np.sqrt(np.clip(1 - d2, 0, 1)) * (0.75 + 0.25 * rad / rmax))
    return h


def lit(h, strength):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * strength
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * strength
    n = np.stack([-gx, -gy, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return np.clip(n @ np.array([-0.5, -0.45, 0.74], np.float32), 0, 1)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def save(name, v, tint, height):
    v = v - v.mean() + 0.5
    rgb = np.clip(v[..., None] * np.array(tint, np.float32)[None, None, :], 0, 1)
    a = np.clip(height, 0, 1)[..., None]
    Image.fromarray((np.concatenate([rgb, a], -1) * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, name + ".png"), optimize=True)
    print(name, round(float(v.std()), 3))


big = fractal(2.2, 1)
mid = fractal(1.6, 2)
fine = fractal(0.6, 3, 40)
speck = fractal(0.0, 4, 120)

grass = 0.5 + (big - 0.5) * 0.2 + (mid - 0.5) * 0.24 + (fine - 0.5) * 0.22 - (speck > 0.7) * 0.12
save("grass", grass, (0.98, 1.03, 0.94), mid * 0.6 + fine * 0.4)

h = canopy(260, 0.035, 0.07, 11)
shade = lit(h, 40)
forest = np.where(h > 0.02, 0.3 + shade * 0.34 + h * 0.06, 0.2) + (fine - 0.5) * 0.08
save("forest", forest, (0.96, 1.04, 0.92), h)

h = canopy(700, 0.018, 0.034, 12) ** 0.6
shade = lit(h, 30)
taiga = np.where(h > 0.02, 0.28 + shade * 0.32 + h * 0.05, 0.18) + (fine - 0.5) * 0.06
save("taiga", taiga, (0.94, 1.02, 0.98), h)

r = np.random.default_rng(13)
rows = 6
wx = xx + (fractal(3.4, 70) - 0.5) * 0.07
wy = yy + (fractal(3.4, 71) - 0.5) * 0.07
row = np.floor(wy * rows).astype(int) % rows
offs = r.random(rows)
widths = r.integers(3, 7, rows)
col = np.floor((wx + offs[row]) * widths[row]).astype(int)
fid = row * 16 + col % widths[row]
tone = r.random(rows * 16)
hue = r.random(rows * 16)
fx = (wx + offs[row]) * widths[row] % 1.0
fy = wy * rows % 1.0
edge = np.minimum(np.minimum(fx, 1 - fx) * 6, np.minimum(fy, 1 - fy) * 6 * rows / 6)
hedge = smooth(0.0, 0.12, edge)
angle = (r.random(rows * 16) > 0.5)[fid]
furrow = np.where(angle, np.sin(xx * N * 0.9), np.sin(yy * N * 0.9)) * 0.03
farm = 0.42 + tone[fid] * 0.15 + furrow + (fine - 0.5) * 0.06
farm = farm * (0.55 + 0.45 * hedge)
tint = np.where(hue[fid][..., None] > 0.5, np.array([1.04, 1.0, 0.86]), np.array([0.94, 1.04, 0.92]))
v = farm - farm.mean() + 0.5
rgb = np.clip(v[..., None] * tint, 0, 1)
Image.fromarray((np.concatenate([rgb, (0.4 + hedge * 0.2)[..., None]], -1) * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "farm.png"), optimize=True)
print("farm", round(float(v.std()), 3))

tuft = (fractal(0.3, 14, 60) > 0.66).astype(np.float32)
soil = smooth(0.55, 0.7, mid)
steppe = 0.52 + (big - 0.5) * 0.2 + (fine - 0.5) * 0.16 - tuft * 0.12 + soil * 0.1
save("steppe", steppe, (1.03, 1.0, 0.9), mid)

warp = fractal(2.4, 15)
ripples = np.sin((xx * 9 + yy * 3 + warp * 2.5) * np.pi * 2 * 4) * 0.04
dunes = np.sin((xx * 2 + yy + warp * 1.4) * np.pi * 2) * 0.07
desert = 0.5 + ripples + dunes + (fine - 0.5) * 0.04
save("desert", desert, (1.03, 1.0, 0.94), dunes + 0.5)

moss = smooth(0.45, 0.6, mid)
stones = (fractal(0.2, 16, 80) > 0.78).astype(np.float32)
tundra = 0.46 + moss * 0.12 + stones * 0.16 + (fine - 0.5) * 0.14
save("tundra", tundra, (0.98, 1.0, 0.98), moss)

streak = np.sin((yy * 22 + warp * 3) * np.pi * 2) * 0.02
snow = 0.5 + (big - 0.5) * 0.06 + (fine - 0.5) * 0.03 + streak
save("snow", snow, (0.97, 0.99, 1.04), big)

ridge = 1 - np.abs(fractal(1.9, 17) * 2 - 1)
crag = ridge ** 2.2 * 0.85 + fractal(1.7, 18) * 0.15
strata = np.sin((yy * 16 + warp * 2.2 + mid * 0.8) * np.pi * 2) * 0.035
rock = 0.3 + lit(crag, 9) * 0.32 + crag * 0.12 + strata + (fine - 0.5) * 0.05
save("rock", rock, (1.0, 0.98, 0.94), crag)

hw = fractal(2.8, 50) * 0.65 + fractal(1.8, 51) * 0.35
gx = (np.roll(hw, -1, 1) - np.roll(hw, 1, 1)) * 9
gy = (np.roll(hw, -1, 0) - np.roll(hw, 1, 0)) * 9
nw = np.stack([-gx, -gy, np.ones_like(hw)], -1)
nw /= np.linalg.norm(nw, axis=-1, keepdims=True)
Image.fromarray((np.concatenate([nw * 0.5 + 0.5, hw[..., None]], -1) * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "waves.png"), optimize=True)
print("waves")


def floor_tex(name, base_tint, moss_tint, litter_tint, seed, litter_amount, moss_amount):
    r = np.random.default_rng(seed)
    moss = smooth(0.55, 0.75, fractal(1.8, seed + 1)) * moss_amount
    litter = (fractal(0.0, seed + 2, 90) > 1.0 - litter_amount).astype(np.float32)
    litter = np.maximum(litter, np.roll(litter, 1, 1) * 0.6)
    v = 0.5 + (big - 0.5) * 0.18 + (mid - 0.5) * 0.22 + (fine - 0.5) * 0.24 - (speck > 0.75) * 0.1
    v = v - v.mean() + 0.5
    rgb = v[..., None] * np.array(base_tint, np.float32)
    rgb = rgb * (1 - moss[..., None]) + (v * 0.86)[..., None] * np.array(moss_tint, np.float32) * moss[..., None]
    rgb = rgb * (1 - litter[..., None] * 0.7) + (v * 1.05)[..., None] * np.array(litter_tint, np.float32) * litter[..., None] * 0.7
    a = np.clip(mid * 0.6 + fine * 0.4, 0, 1)[..., None]
    Image.fromarray((np.clip(np.concatenate([rgb, a], -1), 0, 1) * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, name + ".png"), optimize=True)
    print(name, round(float(rgb.mean()), 3))


floor_tex("forest_floor", (1.1, 1.2, 0.98), (0.9, 1.16, 0.82), (1.32, 1.08, 0.72), 60, 0.035, 0.6)
floor_tex("taiga_floor", (1.02, 1.12, 0.96), (0.84, 1.1, 0.8), (1.24, 0.98, 0.7), 61, 0.05, 0.75)
