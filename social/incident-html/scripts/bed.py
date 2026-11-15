"""Sound bed + final mix for the Exxon Valdez film. Everything is synthesised; cues follow timing.json.
No invented alarms, radio or crash sounds: drone, air, tension pulse, a swell at contact, pads and interface ticks.
Usage: python3 bed.py <timing.json> <narration.wav> <out_mix.wav> <film_seconds>"""
import json
import re
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, resample_poly, sosfilt

TIMING, NARR, OUT, DUR = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
SR = 48000
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(11)
T = json.load(open(TIMING))
LN = T["lines"]
ls = lambda i: LN[i - 1]["start"]
cut = lambda i: 0.0 if i <= 1 else ls(i) - 0.2
key = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())


def tok(line, word, nth=0):
    c = 0
    for k in LN[line - 1]["tokens"]:
        if key(k["w"]) == word:
            if c == nth:
                return k["s"]
            c += 1
    return ls(line)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def norm(x):
    return x / (np.max(np.abs(x)) + 1e-9)


def add(buf, sig, t0):
    i = int(round(t0 * SR))
    if i < 0:
        sig, i = sig[-i:], 0
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[: j - i]


def ramp(a, b):
    """0 before a, 1 after b"""
    return np.clip((t - a) / max(1e-6, b - a), 0, 1)


def whoosh(d=0.5, a=0.2):
    n = int(d * SR)
    x = rng.standard_normal(n)
    tt = np.arange(n) / SR
    k = tt / d
    return a * norm((bp(x, 300, 1200) * (1 - k) + bp(x, 1500, 6000) * k) * np.sin(np.pi * k) ** 2)


def thud(a=0.5, f0=95, f1=46, dec=4.0, d=1.0):
    tt = np.arange(int(d * SR)) / SR
    f = (f0 - f1) * np.exp(-tt * 9) + f1
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * dec)
    click = norm(bp(rng.standard_normal(len(tt)), 200, 2500)) * np.exp(-tt * 30)
    return a * (body + 0.45 * click)


def tick(a=0.16, f=1900, dec=80):
    tt = np.arange(int(0.06 * SR)) / SR
    return a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * dec)


def blip(a=0.16, f=880.0, d=0.22):
    tt = np.arange(int(d * SR)) / SR
    return a * (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * 2 * f * tt)) * np.exp(-tt * 14) * np.minimum(1, tt / 0.004)


def bell(a=0.2, f=1174.66, d=0.9):
    tt = np.arange(int(d * SR)) / SR
    return a * (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * 2 * f * tt) + 0.2 * np.sin(2 * np.pi * 3.01 * f * tt)) * np.exp(-tt * 6) * np.minimum(1, tt / 0.003)


HIT = tok(11, "reef")
bed = np.zeros(N)

# sea and air, the whole film; quieter inside the bridge
air = norm(lp(hp(rng.standard_normal(N), 120), 1500)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.19 * t + 1) * np.sin(2 * np.pi * 0.11 * t))
inside = np.zeros(N)
for a, b in ((cut(6), cut(8)), (cut(9), cut(10))):
    inside += ramp(a, a + 0.2) * (1 - ramp(b - 0.2, b))
bed += 0.085 * air * (1 - 0.6 * inside)
# hull wash while she is moving
wash = norm(bp(rng.standard_normal(N), 1800, 6000)) * (0.8 + 0.2 * np.sin(2 * np.pi * 3.1 * t))
moving = (1 - ramp(HIT, HIT + 0.8)) + ramp(cut(15), cut(15) + 0.5) * 0.6
bed += 0.035 * wash * np.clip(moving, 0, 1) * (1 - 0.7 * inside)
# engine hum until she stops
ph = 2 * np.pi * 46.0 * t
eng = (np.sin(ph) + 0.6 * np.sin(2 * ph + 0.3) + 0.4 * np.sin(3 * ph + 1) + 0.25 * np.sin(4 * ph)) * (0.6 + 0.4 * np.maximum(0, np.sin(2 * np.pi * 7.8 * t)) ** 2)
bed += 0.07 * eng * (1 - ramp(HIT, HIT + 1.2)) * (1 - ramp(cut(13), cut(13) + 0.1))
# drone, darker toward the grounding
drone = (np.sin(2 * np.pi * 73.42 * t) + 0.7 * np.sin(2 * np.pi * 110.0 * t) + 0.45 * np.sin(2 * np.pi * 146.83 * t) + 0.3 * np.sin(2 * np.pi * 220.0 * t)) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.5 * t))
denv = 0.35 * ramp(cut(2), cut(2) + 2) + 0.35 * ramp(cut(5), cut(6)) + 0.3 * ramp(cut(8), HIT)
denv *= 1 - ramp(cut(15) - 0.3, cut(15) + 0.5)
bed += 0.075 * drone * denv
minor = (np.sin(2 * np.pi * 174.61 * t) + 0.6 * np.sin(2 * np.pi * 349.23 * t)) * ramp(cut(8), HIT) * (1 - ramp(cut(15) - 0.3, cut(15) + 0.5))
bed += 0.03 * minor
# tension pulse: from the lone watch to the grounding, quickening
tp = cut(7)
rate = 1.0
while tp < HIT - 0.2:
    prog = (tp - cut(7)) / (HIT - cut(7))
    add(bed, thud(0.22 + 0.2 * prog, 70, 44, 7.0, 0.5), tp)
    add(bed, thud(0.12 + 0.12 * prog, 62, 42, 9.0, 0.4), tp + 0.16)
    tp += 1.05 - 0.5 * prog
# riser into the grounding, then the swell
rn = int(1.6 * SR)
rt = np.arange(rn) / SR
riser = norm(bp(rng.standard_normal(rn), 400, 5000)) * (rt / 1.6) ** 2.5
add(bed, 0.22 * riser, HIT - 1.6)
st = np.arange(int(3.2 * SR)) / SR
swell = np.sin(2 * np.pi * np.cumsum(38 + 30 * np.exp(-st * 2.2)) / SR) * np.exp(-st * 1.1) + 0.5 * norm(lp(rng.standard_normal(len(st)), 500)) * np.exp(-st * 1.6)
add(bed, 0.75 * swell, HIT)
# dark wash while the oil spreads
oil = norm(lp(rng.standard_normal(N), 260)) * ramp(cut(12), cut(12) + 1.0) * (1 - ramp(cut(13), cut(13) + 0.6))
bed += 0.2 * oil
# resolved pad for the lessons and the close
pad = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate((146.83, 220.0, 293.66, 369.99, 440.0))) / 5
bed += 0.13 * pad * ramp(cut(15), cut(15) + 0.8) * (1 - ramp(DUR - 0.9, DUR - 0.1))

# one-shots
add(bed, thud(0.6, 110, 46, 3.0, 1.4), 0.0)                              # hook
for i in range(2, 17):
    add(bed, whoosh(0.5, 0.16 if i not in (6, 9, 12) else 0.2), cut(i) - 0.3)
for at in (tok(2, "loaded") - 0.1, tok(4, "leaves"), tok(4, "steers"), tok(4, "autopilot") - 0.25, tok(5, "less") - 0.15, tok(6, "instruction") - 0.15,
           tok(7, "tired") - 0.1, tok(7, "alone") - 0.1, tok(7, "needed") - 0.3, tok(8, "abeam"), tok(8, "fix") - 0.1, tok(9, "starboard") - 0.2, tok(9, "it") - 0.05):
    add(bed, blip(0.13), at)
add(bed, thud(0.4, 90, 50, 6.0, 0.7), tok(6, "leaves"))                  # he leaves the bridge
add(bed, thud(0.4, 90, 50, 6.0, 0.7), tok(8, "late") - 0.25)
for at in (tok(10, "right", 0), tok(10, "right", 1), tok(10, "hard")):
    add(bed, blip(0.17, 660.0), at - 0.05)
add(bed, thud(0.5, 100, 48, 5.0, 0.8), tok(10, "too") - 0.05)
c1 = tok(12, "8") - 0.1
for i in range(8):
    add(bed, tick(0.15, 1500 + 60 * i), c1 + 0.25 + i * 0.12)
c2, c3 = tok(12, "nearly") - 0.1, tok(12, "gallons") + 0.3
for x in np.linspace(0, 1, 26):
    add(bed, tick(0.09, 2200, 120), c2 + (c3 - c2) * (1 - (1 - x) ** 3) * 0.999)
add(bed, thud(0.55, 100, 44, 3.5, 1.2), ls(13))
for w in ("third", "master", "company", "traffic", "pilotage"):
    add(bed, thud(0.38, 85, 50, 7.0, 0.6), tok(14, w) - 0.35)
for i, w in enumerate(("rest", "put", "and")):
    add(bed, bell(0.16, (1174.66, 1318.51, 1567.98)[i]), tok(15, w) - 0.2)
add(bed, thud(0.6, 110, 44, 3.0, 1.4), tok(16, "system") - 0.05)
add(bed, bell(0.13, 1174.66, 1.2), T["voice_end"] + 0.25)

# voice
v, vsr = sf.read(NARR)
v = resample_poly(v.astype(np.float64), SR, vsr)
voice = np.zeros(N)
voice[: min(N, len(v))] = v[:N]
voice = hp(voice, 70)
voice = np.tanh(voice / (np.percentile(np.abs(voice[voice != 0]), 99.5) + 1e-9) * 1.25) * 0.8
# duck the bed under speech, then check the 300 Hz – 4 kHz margin
env = lp(np.abs(voice), 8, 1)
speaking = np.clip(env / (0.25 * np.max(env)), 0, 1)
duck = 1 - 0.45 * lp(speaking, 4, 1)
bed = np.tanh(bed * 1.3) * 0.75 * duck
sp = speaking > 0.5
vb, bb = bp(voice, 300, 4000), bp(bed, 300, 4000)
margin = 20 * np.log10(np.sqrt(np.mean(vb[sp] ** 2)) / (np.sqrt(np.mean(bb[sp] ** 2)) + 1e-9))
gain = 1.0
if margin < 14:
    gain = 10 ** ((margin - 14) / 20)
    bed *= gain
    bb *= gain
    margin = 20 * np.log10(np.sqrt(np.mean(vb[sp] ** 2)) / (np.sqrt(np.mean(bb[sp] ** 2)) + 1e-9))
mix = voice + bed
mix *= np.clip(t / 0.01, 0, 1) * np.clip((DUR - t) / 0.15, 0, 1)
mix = 0.9 * norm(np.tanh(mix * 1.1))
side = 0.03 * norm(lp(hp(rng.standard_normal(N), 300), 3000)) * (0.3 + 0.7 * (1 - speaking))
sf.write(OUT, np.stack([mix + side, mix - side], axis=1), SR, subtype="PCM_16")
print(f"voice over bed, 300 Hz-4 kHz while speaking: {margin:.1f} dB (bed gain {gain:.2f}); grounding cue at {HIT:.2f}s")
