"""Original background music for Ocean Link social videos (synthesised, no licensing issues).

make_bed(duration, cuts, out_wav, seed): 150 BPM half-time bed, one bar = 1.6 s.
Cuts (slide changes) should land on bar lines; the beat drops in at the first cut,
the last cut gets a chime for the logo end card, and the track fades out at the end.
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 48000
BAR = 1.6
N_ = {'A1': 55.0, 'C2': 65.41, 'D2': 73.42, 'E2': 82.41, 'F2': 87.31, 'G2': 98.0, 'A2': 110.0,
      'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61, 'G3': 196.0, 'A3': 220.0, 'B3': 246.94,
      'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.0, 'A4': 440.0, 'B4': 493.88,
      'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46, 'G5': 783.99, 'A5': 880.0, 'C6': 1046.5,
      'E6': 1318.5, 'G6': 1568.0}
CH = {'Am': (['A3', 'C4', 'E4'], 'A2', ['A4', 'C5', 'E5', 'A4']),
      'F': (['F3', 'A3', 'C4', 'E4'], 'F2', ['F4', 'A4', 'C5', 'A4']),
      'C': (['C4', 'E4', 'G4'], 'C3', ['C5', 'E5', 'G5', 'E5']),
      'G': (['G3', 'B3', 'D4'], 'G2', ['G4', 'B4', 'D5', 'B4']),
      'Dm': (['D4', 'F4', 'A4'], 'D3', ['D5', 'F5', 'A5', 'F5']),
      'Em': (['E3', 'G3', 'B3'], 'E2', ['E4', 'G4', 'B4', 'G4'])}
PROGS = [['Am', 'F', 'C', 'G'], ['F', 'G', 'Am', 'C'], ['C', 'G', 'Am', 'F'], ['Am', 'Dm', 'F', 'G'], ['Dm', 'F', 'C', 'G']]


def make_bed(duration, cuts, out_wav, seed=1):
    rng = np.random.default_rng(seed)
    n_total = int(SR * duration)
    lp = lambda x, fc: sosfilt(butter(2, fc, fs=SR, output='sos'), x)
    hp = lambda x, fc: sosfilt(butter(2, fc, fs=SR, btype='high', output='sos'), x)
    bp = lambda x, lo, hi: sosfilt(butter(2, [lo, hi], fs=SR, btype='band', output='sos'), x)

    def add(buf, sig, t0, g=1.0):
        i = int(round(t0 * SR))
        if i >= len(buf) or i < 0:
            return
        j = min(len(buf), i + len(sig))
        buf[i:j] += g * sig[:j - i]

    def env(n, att, rel):
        e = np.ones(n); a = int(att * SR); r = int(rel * SR)
        if a: e[:a] = np.linspace(0, 1, a)
        if r: e[-r:] *= np.linspace(1, 0, r)
        return e

    def saw(f, dur):
        t = np.arange(int(dur * SR)) / SR; s = 0
        for d in (-0.004, 0, 0.004):
            ph = rng.uniform(0, 2 * np.pi)
            for h in range(1, 11):
                if f * h > 9000: break
                s = s + np.sin(2 * np.pi * f * (1 + d) * h * t + ph * h) / h
        return s / 3

    cache = {}
    def pluck(f):
        if f in cache: return cache[f]
        n = int(0.9 * SR); p = int(SR / f); buf = rng.uniform(-1, 1, p); out = np.zeros(n)
        for i in range(n):
            out[i] = buf[i % p]; buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
        cache[f] = out * np.exp(-np.arange(n) / SR * 3.0)
        return cache[f]

    def kick(g=1.0):
        n = int(0.45 * SR); t = np.arange(n) / SR
        f = 46 + 90 * np.exp(-t * 28)
        return g * (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5) + 0.25 * np.exp(-t * 200) * rng.uniform(-1, 1, n))

    def snare():
        n = int(0.25 * SR); t = np.arange(n) / SR
        return 0.55 * bp(rng.standard_normal(n), 900, 7000) * np.exp(-t * 18) + 0.35 * np.sin(2 * np.pi * 185 * t) * np.exp(-t * 30)

    def hat(op=False):
        n = int((0.22 if op else 0.05) * SR); t = np.arange(n) / SR
        return hp(rng.standard_normal(n), 7000) * np.exp(-t * (14 if op else 70))

    def bass(f, dur):
        n = int(dur * SR); t = np.arange(n) / SR
        return np.tanh(1.6 * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t))) * env(n, 0.01, 0.12)

    prog = PROGS[seed % len(PROGS)]
    mus = np.zeros(n_total); fx = np.zeros(n_total)
    drop = cuts[0] if cuts else BAR * 2
    end_start = cuts[-1] if cuts else duration - BAR * 2
    nbars = int(np.ceil(duration / BAR))
    for b in range(nbars):
        t0 = b * BAR
        if t0 >= duration: break
        name = prog[b % 4] if t0 < end_start - 1e-6 else 'C' if prog[0] != 'Dm' else 'F'
        notes, root, ap = CH[name]
        last = t0 >= end_start - 1e-6
        dur = BAR if not last else duration - t0
        for nn in notes:
            add(mus, saw(N_[nn], dur + 0.3) * env(int((dur + 0.3) * SR), 0.06, 0.35), t0, 0.2)
        if t0 >= drop - 1e-6 and not last:
            for k in range(8):
                add(mus, pluck(N_[ap[k % 4]]), t0 + k * 0.2, 0.3 * (1.0 if k % 2 == 0 else 0.7))
            add(mus, bass(N_[root], 0.7), t0, 0.5); add(mus, bass(N_[root], 0.3), t0 + 1.2, 0.35)
            add(mus, kick(), t0, 0.95); add(mus, kick(0.7), t0 + 0.6, 0.8); add(mus, snare(), t0 + 0.8, 0.75)
            for k in range(8):
                add(mus, hat(k == 7), t0 + k * 0.2, 0.16 if k % 2 == 0 else 0.10)
        elif not last:  # intro: soft arp fading in
            for k in range(8):
                add(mus, pluck(N_[ap[k % 4]]), t0 + k * 0.2, 0.06 + 0.02 * k)
        else:
            add(mus, bass(N_[root], min(dur, 2.0)), t0, 0.45); add(mus, kick(), t0, 0.9)
    # riser into the drop, impact on every cut
    n = int(1.0 * SR); t = np.arange(n) / SR
    add(fx, hp(rng.standard_normal(n), 1500) * (t / 1.0) ** 2, drop - 1.0, 0.09)
    for c in cuts:
        n = int(1.0 * SR); t = np.arange(n) / SR
        add(fx, lp(rng.standard_normal(n), 6000) * np.exp(-t * 5), c, 0.16 if c == drop else 0.07)
    for k, nn in enumerate(['C5', 'E5', 'G5', 'C6', 'E6', 'G6']):
        add(fx, pluck(N_[nn]), end_start + 0.2 + 0.06 * k, 0.2)
    mix = mus + fx
    fade = np.ones(n_total); i0 = int(max(0, duration - 1.1) * SR); fade[i0:] = np.linspace(1, 0, n_total - i0) ** 1.5
    mix = lp(mix * fade, 15000)
    st = np.stack([mix, np.roll(mix, int(0.009 * SR)) * 0.97], 1)
    st /= np.max(np.abs(st)) * 1.05
    wavfile.write(out_wav, SR, st.astype(np.float32))
    return out_wav
