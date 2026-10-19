import os
import sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "ArtSource", "textures")
DETAIL = os.path.join(ROOT, "Assets", "StreamingAssets", "Data", "world", "detail")
PROPS_DIR = os.path.join(ROOT, "Assets", "StreamingAssets", "Data", "world", "props")
SIZE = 1024
PROP_SIZE = 512
LUMA = np.array([0.299, 0.587, 0.114], np.float32)

GROUND = {
    "grass": ((0.488, 0.513, 0.468), 0.3, 0.485, 0.077),
    "forest_floor": ((0.534, 0.589, 0.476), 0.35, 0.485, 0.077),
    "taiga_floor": ((0.499, 0.553, 0.470), 0.35, 0.485, 0.077),
    "farm": ((0.495, 0.507, 0.442), 0.3, 0.592, 0.034),
    "steppe": ((0.513, 0.498, 0.448), 0.3, 0.474, 0.105),
    "desert": ((0.513, 0.498, 0.468), 0.25, 0.492, 0.049),
    "tundra": ((0.488, 0.498, 0.488), 0.3, 0.326, 0.395),
    "snow": ((0.483, 0.493, 0.518), 0.15, 0.48, 0.135),
    "rock": ((0.498, 0.488, 0.468), 0.35, 0.64, 0.186),
}

PROPS = {
    "stone": 0.28, "plaster": 0.16, "planks": 0.28, "logs": 0.3, "tiles": 0.3, "shingles": 0.3, "slate": 0.3,
    "mudbrick": 0.25, "thatch": 0.3, "brick": 0.28, "paving": 0.3, "felt": 0.2, "rock": 0.3,
    "leaves": 0.32, "needles": 0.32, "bark": 0.3, "birch": 0.3,
}
MIN_CONTRAST = {"desert": 0.12, "snow": 0.1}
ROWS = {"tiles", "shingles"}
CROSSFADE = {"bark"}


def load(name, size):
    img = Image.open(os.path.join(SRC, name + ".png")).convert("RGB")
    if name == "foam":
        w, h = img.size
        if w > h * 1.5:
            img = img.crop((w // 2 + 3, 3, w - 3, h - 3))
    a = np.asarray(img).astype(np.float32) / 255
    if name in ROWS:
        a = align_rows(a)
    a = np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)).astype(np.float32) / 255
    if name in CROSSFADE:
        a = crossfade(a)
    return a


def period(profile, lo, hi):
    v = profile - profile.mean()
    best, score = 0, -1e9
    for p in range(lo, min(hi, len(v) // 2)):
        c = float(np.dot(v[:-p], v[p:]) / (len(v) - p))
        if c > score:
            best, score = p, c
    return best


def align_rows(a):
    L = a @ LUMA
    p = period(L.mean(axis=1), 20, len(L) // 2)
    if p <= 0:
        return a
    rows = max(1, len(L) // p)
    best_off, best = 0, 1e9
    for off in range(0, len(L) - rows * p + 1, 2):
        d = float(np.abs(L[off] - L[off + rows * p - 1]).mean())
        if d < best:
            best_off, best = off, d
    return a[best_off:best_off + rows * p]


def crossfade(a, frac=0.18):
    h, w, _ = a.shape
    shifted = np.roll(np.roll(a, w // 2, 1), h // 2, 0)
    x = np.abs(np.arange(w, dtype=np.float32) / (w - 1) - 0.5) * 2
    y = np.abs(np.arange(h, dtype=np.float32) / (h - 1) - 0.5) * 2
    t = np.clip((np.maximum(x[None, :], y[:, None]) - (1 - frac * 2)) / (frac * 2), 0, 1)
    m = (t * t * (3 - 2 * t))[..., None]
    return a * (1 - m) + shifted * m


def wrap_blur(a, sigma):
    h, w = a.shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-2.0 * (np.pi * sigma) ** 2 * (fx * fx + fy * fy))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g)).astype(np.float32)


def smooth_along(v, n):
    k = np.ones(n, np.float32) / n
    p = np.concatenate([v[-n:], v, v[:n]])
    return np.stack([np.convolve(p[:, c], k, mode="same")[n:-n] for c in range(v.shape[1])], -1)


def seamless(a, frac=0.1):
    out = a.copy()
    h, w, _ = a.shape
    b = max(4, int(w * frac))
    t = np.linspace(1.0, 0.0, b, dtype=np.float32)
    ramp = t * t * (3 - 2 * t)
    delta = smooth_along(out[:, -4:].mean(axis=1) - out[:, :4].mean(axis=1), 15) * 0.5
    out[:, :b] += delta[:, None, :] * ramp[None, :, None]
    out[:, w - b:] -= delta[:, None, :] * ramp[::-1][None, :, None]
    delta = smooth_along(out[-4:, :].mean(axis=0) - out[:4, :].mean(axis=0), 15) * 0.5
    out[:b, :] += delta[None, :, :] * ramp[:, None, None]
    out[h - b:, :] -= delta[None, :, :] * ramp[::-1][:, None, None]
    return out


def edge_score(a):
    L = a @ LUMA
    inner = (np.abs(np.diff(L, axis=1)).mean() + np.abs(np.diff(L, axis=0)).mean()) / 2
    seam = (np.abs(L[:, 0] - L[:, -1]).mean() + np.abs(L[0, :] - L[-1, :]).mean()) / 2
    return seam / max(inner, 1e-6)


def ground(name, src):
    target, contrast, alpha_mean, alpha_std = GROUND[name]
    a = load(name, SIZE)
    before = edge_score(a)
    a = np.clip(seamless(a), 0, 1)
    L = a @ LUMA
    rel = a / np.maximum(a.mean(axis=(0, 1)), 0.02) - 1.0
    std = max(float((rel @ LUMA).std()), 1e-4)
    rel *= max(MIN_CONTRAST.get(name, 0.0) / std, min(1.0, contrast / std))
    rgb = np.clip(np.array(target, np.float32) * (1.0 + rel), 0, 1)
    hb = wrap_blur(L, 2.0)
    alpha = np.clip(alpha_mean + (hb - hb.mean()) / max(hb.std(), 1e-4) * alpha_std, 0, 1)
    out = np.concatenate([rgb, alpha[..., None]], -1)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(DETAIL, name + ".png"), optimize=True)
    print(f"{name}: seam {before:.2f} -> {edge_score(rgb):.2f}, relative contrast {float((rel @ LUMA).std()):.2f}")


def prop(name):
    a = load(name, PROP_SIZE)
    before = edge_score(a)
    a = np.clip(seamless(a), 0, 1)
    L = a @ LUMA
    rel = L / max(float(L.mean()), 0.02) - 1.0
    rel *= min(1.0, PROPS[name] / max(float(rel.std()), 1e-4))
    g = np.clip(0.5 * (1.0 + rel), 0, 1)
    Image.fromarray((np.repeat(g[..., None], 3, -1) * 255 + 0.5).astype(np.uint8), "RGB").save(os.path.join(PROPS_DIR, name + ".png"), optimize=True)
    print(f"prop {name}: seam {before:.2f} -> {edge_score(np.repeat(g[..., None], 3, -1)):.2f}")


def water():
    a = np.clip(seamless(load("water", SIZE)), 0, 1)
    hgt = wrap_blur(a @ LUMA, 1.5)
    hgt = (hgt - hgt.min()) / max(float(hgt.max() - hgt.min()), 1e-4)
    gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 9
    gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 9
    n = np.stack([-gx, -gy, np.ones_like(hgt)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    foam = hgt
    if os.path.exists(os.path.join(SRC, "foam.png")):
        f = np.clip(seamless(load("foam", SIZE)), 0, 1) @ LUMA
        foam = np.clip(0.5 + (f - f.mean()) / max(float(f.std()), 1e-4) * 0.15, 0, 1)
    out = np.concatenate([n * 0.5 + 0.5, foam[..., None]], -1)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(DETAIL, "waves.png"), optimize=True)
    print(f"waves: normal std {float(n[..., 0].std()):.3f}, foam from {'foam.png' if foam is not hgt else 'height'}")


names = sys.argv[1:] or sorted({n[:-4] for n in os.listdir(SRC) if n.endswith(".png")})
for n in names:
    if not os.path.exists(os.path.join(SRC, n + ".png")):
        print(f"{n}: no source")
        continue
    if n in GROUND:
        ground(n, os.path.join(SRC, n + ".png"))
    if n in PROPS:
        prop(n)
    if n == "water":
        water()
    if n not in GROUND and n not in PROPS and n not in ("water", "foam"):
        print(f"{n}: unknown texture")
