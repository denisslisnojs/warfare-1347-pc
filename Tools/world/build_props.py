import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Assets", "StreamingAssets", "Data", "world", "props")
os.makedirs(OUT, exist_ok=True)
N = 256
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / N
rng = np.random.default_rng(7)


def fractal(beta, seed, lo=1.0):
    r = np.random.default_rng(seed)
    f = np.fft.fft2(r.standard_normal((N, N)))
    fx = np.fft.fftfreq(N)[None, :] * N
    fy = np.fft.fftfreq(N)[:, None] * N
    k = np.sqrt(fx * fx + fy * fy)
    k[0, 0] = 1.0
    amp = k ** (-beta / 2.0)
    amp[k < lo] = 0.0
    out = np.real(np.fft.ifft2(f * amp)).astype(np.float32)
    out -= out.min()
    return out / max(out.max(), 1e-6)


def save(name, v):
    v = np.clip(v - v.mean() + 0.5, 0, 1)
    Image.fromarray((np.stack([v, v, v], -1) * 255).astype(np.uint8)).save(os.path.join(OUT, name + ".png"), optimize=True)
    print(name, round(float(v.std()), 3))


grain = fractal(1.0, 1)
soft = fractal(2.0, 2)
fine = fractal(0.4, 3, 30)


def courses(rows, cols, stagger, seed):
    r = np.random.default_rng(seed)
    row = np.floor(yy * rows).astype(int)
    shift = np.where(row % 2 == 1, stagger, 0.0)
    u = (xx * cols + shift) % cols
    col = np.floor(u).astype(int)
    tone = r.random((rows, cols + 1))[row, col]
    fu = u % 1.0
    fv = (yy * rows) % 1.0
    return tone, fu, fv


tone, fu, fv = courses(6, 3, 0.5, 11)
joint = np.minimum(np.minimum(fu, 1 - fu) * 3 * 2.2, np.minimum(fv, 1 - fv) * 6 * 0.55)
mortar = np.clip(joint / 0.06, 0, 1)
bevel = np.clip((0.5 - fv) * 0.3, -0.06, 0.06)
stone = (0.42 + tone * 0.16 + (fine - 0.5) * 0.12 + bevel) * (0.55 + 0.45 * mortar)
save("stone", stone)

rows = 4
fv = (yy * rows) % 1.0
log_shade = 0.32 + 0.3 * np.sin(np.pi * fv) ** 0.6
seam = np.clip(np.minimum(fv, 1 - fv) / 0.06, 0, 1)
streak = fractal(0.9, 4)
streak = np.roll(np.repeat(streak[:, :1], N, 1), 0, 0) * 0 + np.sin((xx * 3 + grain * 0.6) * np.pi * 2 * 6) * 0.03
logs = (log_shade + streak + (fine - 0.5) * 0.06) * (0.6 + 0.4 * seam)
save("logs", logs)

cols = 6
fu = (xx * cols) % 1.0
board = np.floor(xx * cols).astype(int)
btone = rng.random(cols)[board]
gap = np.clip(np.minimum(fu, 1 - fu) / 0.05, 0, 1)
grain_v = np.sin((yy * 5 + grain * 0.8 + board * 0.37) * np.pi * 2 * 5) * 0.03
planks = (0.42 + btone * 0.14 + grain_v + (fine - 0.5) * 0.06) * (0.55 + 0.45 * gap)
save("planks", planks)

tone, fu, fv = courses(8, 5, 0.5, 12)
edge = np.clip(np.minimum(fu, 1 - fu) / 0.05, 0, 1)
drop = 0.62 - fv * 0.22
shingles = (drop * (0.75 + tone * 0.35) + (grain - 0.5) * 0.08) * (0.7 + 0.3 * edge)
save("shingles", shingles)

rows, cols = 7, 6
fv = (yy * rows) % 1.0
fu = (xx * cols + np.where(np.floor(yy * rows) % 2 == 1, 0.5, 0.0)) % 1.0
bulge = 0.38 + 0.26 * np.sin(np.pi * fu) ** 0.8
lip = 0.75 + 0.25 * np.clip(fv / 0.18, 0, 1)
tiles = bulge * lip * (0.92 + (soft - 0.5) * 0.25) + (fine - 0.5) * 0.04
save("tiles", tiles)

tone, fu, fv = courses(10, 6, 0.5, 13)
line = np.clip(np.minimum(np.minimum(fu, 1 - fu) * 1.4, np.minimum(fv, 1 - fv)) / 0.06, 0, 1)
slate = (0.42 + tone * 0.18 + (fine - 0.5) * 0.05) * (0.7 + 0.3 * line)
save("slate", slate)

plaster = 0.5 + (soft - 0.5) * 0.12 + (fine - 0.5) * 0.05
save("plaster", plaster)

tone, fu, fv = courses(5, 2, 0.5, 14)
seam = np.clip(np.minimum(np.minimum(fu, 1 - fu) * 2 * 1.6, np.minimum(fv, 1 - fv) * 5 * 0.4) / 0.05, 0, 1)
straw = (fractal(0.2, 15, 60) > 0.7) * 0.05
mudbrick = (0.44 + tone * 0.12 + (soft - 0.5) * 0.14 + (fine - 0.5) * 0.08 + straw) * (0.7 + 0.3 * seam)
save("mudbrick", mudbrick)


def stamp(img, cx, cy, rx, ry, ang, val, soft_edge=0.35):
    R = int(np.ceil(max(rx, ry))) + 2
    ys, xs = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32)
    ca, sa = np.cos(ang), np.sin(ang)
    u = (xs * ca + ys * sa) / rx
    v = (-xs * sa + ys * ca) / ry
    d = np.sqrt(u * u + v * v)
    a = np.clip((1.0 - d) / soft_edge, 0, 1)
    shade = val * (1.0 - 0.35 * np.clip(v, -1, 1))
    iy = (np.arange(-R, R + 1) + int(cy)) % N
    ix = (np.arange(-R, R + 1) + int(cx)) % N
    win = img[np.ix_(iy, ix)]
    img[np.ix_(iy, ix)] = win * (1 - a) + shade * a


r = np.random.default_rng(21)
leaves = np.full((N, N), 0.3, np.float32)
for _ in range(2600):
    stamp(leaves, r.uniform(0, N), r.uniform(0, N), r.uniform(3.0, 5.5), r.uniform(1.6, 2.8), r.uniform(0, np.pi), r.uniform(0.35, 0.8))
leaves = leaves + (soft - 0.5) * 0.12
save("leaves", leaves)

r = np.random.default_rng(22)
needles = np.full((N, N), 0.32, np.float32)
for _ in range(3800):
    stamp(needles, r.uniform(0, N), r.uniform(0, N), r.uniform(4.0, 7.0), r.uniform(0.7, 1.1), np.pi / 2 + r.uniform(-0.6, 0.6), r.uniform(0.35, 0.75), 0.5)
needles = needles + (soft - 0.5) * 0.1
save("needles", needles)

streak = np.asarray(Image.fromarray((fractal(1.2, 23, 2) * 255).astype(np.uint8)).resize((N // 8, N), Image.BICUBIC).resize((N, N), Image.BICUBIC), np.float32) / 255.0
bark = 0.45 + (streak - 0.5) * 1.4 + (fine - 0.5) * 0.2
bark = np.where(np.roll(streak, 3, 1) - streak > 0.08, bark * 0.7, bark)
save("bark", bark)

r = np.random.default_rng(24)
birch = np.full((N, N), 0.78, np.float32) + (soft - 0.5) * 0.08
for _ in range(260):
    stamp(birch, r.uniform(0, N), r.uniform(0, N), r.uniform(3, 10), r.uniform(0.6, 1.4), r.uniform(-0.08, 0.08), r.uniform(0.12, 0.3), 0.6)
for _ in range(40):
    stamp(birch, r.uniform(0, N), r.uniform(0, N), r.uniform(5, 12), r.uniform(3, 7), r.uniform(-0.3, 0.3), r.uniform(0.25, 0.4), 0.8)
save("birch", birch)

crag = fractal(1.4, 25, 2)
cell = fractal(2.6, 26, 1)
cracks = np.clip(1.0 - np.abs(np.sin(cell * 18.0)) * 3.0, 0, 1)
rockp = 0.5 + (crag - 0.5) * 0.7 + (fine - 0.5) * 0.25 - cracks * 0.18 + (grain - 0.5) * 0.12
save("rock", rockp)
