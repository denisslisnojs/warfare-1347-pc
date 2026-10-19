import os, sys, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "Assets", "Resources", "Audio")
VARIANTS = os.path.join(ROOT, "ArtSource", "audio", "coins")
RATE = 44100


def save(path, left, right):
    peak = max(np.abs(left).max(), np.abs(right).max(), 1e-9)
    data = np.stack([left, right], 1) / peak * 0.7
    pcm = (np.clip(data, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())
    print(f"{os.path.basename(path)} {len(left) / RATE:.2f}s")


def band(x, lo, hi):
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(x.size, 1 / RATE)
    spec *= ((f >= lo) & (f <= hi)).astype(float)
    return np.fft.irfft(spec, x.size)


class Mix:
    def __init__(self, length):
        self.n = int(RATE * length)
        self.t = np.arange(self.n) / RATE
        self.l = np.zeros(self.n)
        self.r = np.zeros(self.n)

    def add(self, start, sound, pan=0.5, gain=1.0):
        i = int(start * RATE)
        if i >= self.n:
            return
        m = min(sound.size, self.n - i)
        self.l[i:i + m] += sound[:m] * gain * (1 - pan)
        self.r[i:i + m] += sound[:m] * gain * pan

    def done(self, fade=0.06):
        k = np.clip((self.t[-1] - self.t) / fade, 0, 1)
        return self.l * k, self.r * k


def ring(f0, tau, length, partials=((1.0, 1.0), (2.76, 0.55), (5.40, 0.3), (8.93, 0.15)), rng=None, hit=0.5):
    t = np.arange(int(RATE * length)) / RATE
    out = np.zeros_like(t)
    for ratio, weight in partials:
        phase = rng.uniform(0, 6.28) if rng is not None else 0.0
        out += weight * np.sin(2 * np.pi * f0 * ratio * t + phase) * np.exp(-t / (tau / ratio ** 0.5))
    if hit > 0:
        noise = rng.standard_normal(t.size) if rng is not None else np.random.default_rng(0).standard_normal(t.size)
        out += hit * noise * np.exp(-t / 0.0015)
    return out


def thud(freq, tau, length, noise=0.3, rng=None):
    t = np.arange(int(RATE * length)) / RATE
    body = np.sin(2 * np.pi * freq * t * (1 - 0.25 * t / length)) * np.exp(-t / tau)
    grit = band((rng or np.random.default_rng(1)).standard_normal(t.size), 80, 900) * np.exp(-t / (tau * 0.6)) * noise
    return body + grit


def wood(rng, f=900, tau=0.012, length=0.08):
    t = np.arange(int(RATE * length)) / RATE
    click = band(rng.standard_normal(t.size), 400, 3500) * np.exp(-t / 0.004)
    res = np.sin(2 * np.pi * f * t) * np.exp(-t / tau) * 0.8
    return click + res


def v1_single_coin_on_table(rng):
    m = Mix(1.1)
    m.add(0.0, ring(3400, 0.09, 0.6, rng=rng, hit=0.8), 0.5)
    gap, f, a, s = 0.09, 3400, 0.7, 0.09
    while s < 0.9 and a > 0.05:
        m.add(s, ring(f, 0.03, 0.2, rng=rng, hit=0.3), 0.5, a)
        s += gap
        gap *= 0.78
        a *= 0.86
        f *= 1.01
    return m.done()


def v2_purse_shake(rng):
    m = Mix(0.7)
    for i in range(40):
        s = rng.uniform(0, 0.45)
        m.add(s, band(ring(rng.uniform(1800, 3200), 0.025, 0.15, rng=rng, hit=0.4), 300, 6000), rng.uniform(0.3, 0.7), rng.uniform(0.2, 0.5))
    m.add(0.0, thud(140, 0.08, 0.3, 0.6, rng), 0.5, 0.8)
    return m.done()


def v3_coin_stack(rng):
    m = Mix(0.8)
    for i, s in enumerate((0.0, 0.11, 0.2, 0.27)):
        m.add(s, ring(1900 + i * 80, 0.035, 0.25, rng=rng, hit=0.9), 0.5, 1.0 - i * 0.12)
        m.add(s, wood(rng, 600, 0.01), 0.5, 0.4)
    return m.done()


def v4_trade_bell(rng):
    m = Mix(1.6)
    bell = ((1.0, 1.0), (2.0, 0.5), (2.4, 0.45), (3.0, 0.25), (4.2, 0.15), (5.4, 0.08))
    m.add(0.0, ring(880, 0.9, 1.6, partials=bell, rng=rng, hit=0.2), 0.5)
    return m.done(0.2)


def v5_two_coins_clink(rng):
    m = Mix(0.7)
    m.add(0.0, ring(4200, 0.12, 0.6, rng=rng, hit=0.6), 0.4)
    m.add(0.085, ring(3700, 0.1, 0.6, rng=rng, hit=0.5), 0.6, 0.8)
    return m.done()


def v6_pour_into_chest(rng):
    m = Mix(1.2)
    for i in range(26):
        s = 0.02 + (i / 26) ** 1.4 * 0.75 + rng.uniform(-0.015, 0.015)
        m.add(s, ring(rng.uniform(2000, 3600), rng.uniform(0.03, 0.06), 0.25, rng=rng, hit=0.5), rng.uniform(0.3, 0.7), 1.0 - 0.6 * i / 26)
    m.add(0.82, thud(110, 0.12, 0.35, 0.8, rng), 0.5, 1.4)
    return m.done()


def v7_soft_chink(rng):
    m = Mix(0.35)
    m.add(0.0, band(ring(2600, 0.04, 0.3, rng=rng, hit=0.3), 200, 5000), 0.5)
    m.add(0.035, band(ring(2900, 0.03, 0.3, rng=rng, hit=0.2), 200, 5000), 0.5, 0.5)
    return m.done(0.05)


def v8_wood_and_coin(rng):
    m = Mix(0.8)
    m.add(0.0, wood(rng, 750, 0.02, 0.15), 0.5, 1.2)
    m.add(0.12, ring(3100, 0.11, 0.6, rng=rng, hit=0.6), 0.55, 0.9)
    return m.done()


def v9_two_note_chime(rng):
    m = Mix(1.4)
    bell = ((1.0, 1.0), (2.0, 0.35), (3.0, 0.2), (4.1, 0.1))
    m.add(0.0, ring(659, 0.5, 1.2, partials=bell, rng=rng, hit=0.1), 0.45)
    m.add(0.16, ring(988, 0.6, 1.2, partials=bell, rng=rng, hit=0.1), 0.55, 0.9)
    return m.done(0.2)


def v10_purse_drop(rng):
    m = Mix(0.6)
    m.add(0.0, thud(120, 0.06, 0.3, 1.0, rng), 0.5, 1.3)
    for i in range(7):
        s = rng.uniform(0.0, 0.08)
        m.add(s, band(ring(rng.uniform(1600, 2400), 0.02, 0.12, rng=rng, hit=0.2), 200, 2500), rng.uniform(0.4, 0.6), 0.5)
    return m.done()


VARIANT_LIST = [v1_single_coin_on_table, v2_purse_shake, v3_coin_stack, v4_trade_bell, v5_two_coins_clink,
                v6_pour_into_chest, v7_soft_chink, v8_wood_and_coin, v9_two_note_chime, v10_purse_drop]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pick = int(sys.argv[1])
        left, right = VARIANT_LIST[pick - 1](np.random.default_rng(1347 + pick))
        save(os.path.join(OUT, "coins.wav"), left, right)
    else:
        os.makedirs(VARIANTS, exist_ok=True)
        for i, fn in enumerate(VARIANT_LIST, 1):
            left, right = fn(np.random.default_rng(1347 + i))
            save(os.path.join(VARIANTS, f"coins_{i:02d}.wav"), left, right)
