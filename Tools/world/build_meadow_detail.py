from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

rng = np.random.default_rng(1347)
size = 1024
def noise(n, blur=0):
    raw = rng.standard_normal((size, size))
    freq = np.fft.fftfreq(size)
    radius = freq[:, None] ** 2 + freq[None, :] ** 2
    filtered = np.fft.ifft2(np.fft.fft2(raw) * np.exp(-2 * np.pi ** 2 * (size / n / 2) ** 2 * radius)).real
    return np.clip(0.5 + filtered / filtered.std() * 0.16, 0, 1).astype(np.float32)

patch = noise(12)
fine = noise(80)
base = np.clip(0.49 + (patch - 0.5) * 0.07 + (fine - 0.5) * 0.045, 0, 1)
canvas = Image.fromarray((base * 255).astype(np.uint8))
draw = ImageDraw.Draw(canvas)
for _ in range(38000):
    x, y = rng.uniform(0, size, 2)
    p = float(patch[int(y) % size, int(x) % size])
    angle = rng.uniform(0, np.pi * 2)
    length = rng.uniform(3, 17) * (0.65 + p * 0.55)
    dx, dy = np.cos(angle) * length, np.sin(angle) * length
    bend = rng.uniform(-0.25, 0.25)
    color = int(rng.uniform(106, 150))
    for ox in (-size, 0, size):
        for oy in (-size, 0, size):
            a = (x + ox, y + oy)
            b = (x + ox + dx * 0.55 - dy * bend, y + oy + dy * 0.55 + dx * bend)
            c = (x + ox + dx, y + oy + dy)
            draw.line([a, b, c], fill=color, width=int(rng.integers(1, 3)))
tone = np.asarray(canvas.filter(ImageFilter.GaussianBlur(0.5))).astype(np.float32) / 255
height = np.clip(0.47 + (tone - 0.49) * 0.65 + (patch - 0.5) * 0.13, 0, 1)
pixels = np.stack([tone * 0.99, tone * 1.015, tone * 0.96, height], axis=-1)
out = Path(__file__).resolve().parents[2] / 'Assets/StreamingAssets/Data/world/detail/meadow.png'
Image.fromarray((np.clip(pixels, 0, 1) * 255).astype(np.uint8)).save(out)
print(out)
