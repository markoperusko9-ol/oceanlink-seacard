"""Narration for the Exxon Valdez episode with an open-source voice (Kokoro-82M, Apache-2.0).
Usage: python3 tts.py <models_dir> <out_dir>
Writes line_XX.wav, narration.wav (24 kHz mono) and timing.json (per-token times on the film clock)."""
import json
import re
import sys
from difflib import SequenceMatcher

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from scipy.signal import resample_poly

MODELS, OUT = sys.argv[1], sys.argv[2]
VOICE, SPEED, SR = "am_michael", 1.13, 24000
LEAD = 0.30  # film starts with the hook already on screen; voice comes in right away

# {shown|spoken}; gap = pause after the line (s)
LINES = [
    ("Everyone blames the captain of the Exxon Valdez. But when she hit the reef, he wasn't even on the bridge.", 0.45),
    ("March {1989,|nineteen eighty-nine,} Alaska. A loaded supertanker leaves Valdez, carrying {200,000|two hundred thousand} tons of crude oil.", 0.25),
    ("Glacier ice is drifting across the shipping lanes.", 0.22),
    ("So the master leaves the lanes, steers due south, and has her put on autopilot.", 0.28),
    ("Dead ahead lies {Bligh|Bly} Reef. The gap between the ice and the reef? Less than a mile.", 0.35),
    ("Just before midnight, the master gives one instruction: turn back when Busby Island light is abeam. Then he leaves the bridge.", 0.35),
    ("One officer is left. The third mate. Tired, and alone, in water that needed two.", 0.35),
    ("Three minutes later, the light is abeam. He plots the fix. But the turn starts late.", 0.28),
    ("The lookout reports a red light on the starboard bow. It should be to port.", 0.28),
    ("Right {10.|ten.} Right {20.|twenty.} Hard right. Too late.", 0.40),
    ("Just after midnight, at {12|twelve} knots, she drives onto the reef.", 0.55),
    ("{8|Eight} of her {11|eleven} cargo tanks tear open. Nearly {11|eleven} million gallons of oil pour into Prince William Sound.", 0.50),
    ("So who put her there? Investigators did not name one man.", 0.30),
    ("A third mate worn down by fatigue and workload. A master impaired by alcohol. A company that sailed with a tired, thin crew. And a traffic service and pilotage system that fell short.", 0.45),
    ("The lessons? Rest is safety equipment. Put two officers on the bridge when the water gets tight. And when you leave the plan, fix your position, again and again.", 0.45),
    ("One ship hit the reef. A whole system put her there.", 0.0),
]


def parse(line):
    """-> list of (shown_token, [spoken words])"""
    toks = []
    for part in re.findall(r"\{[^}]*\}|\S+", line):
        if part.startswith("{"):
            shown, spoken = part[1:-1].split("|")
            toks.append((shown, spoken.split()))
        else:
            toks.append((part, [part]))
    return toks


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def trim(x, thr=0.012, pad=0.02):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(x), idx[-1] + int(0.06 * SR))
    return x[a:b]


kokoro = Kokoro(f"{MODELS}/kokoro-v1.0.onnx", f"{MODELS}/voices-v1.0.bin")
try:
    from faster_whisper import WhisperModel

    asr = WhisperModel("small.en", device="cpu", compute_type="int8")
except Exception as e:  # timing falls back to proportional
    print("ASR unavailable:", e)
    asr = None

clock = LEAD
track = [np.zeros(int(LEAD * SR), dtype=np.float32)]
out = {"voice": VOICE, "speed": SPEED, "lines": []}
for i, (line, gap) in enumerate(LINES):
    toks = parse(line)
    spoken = [w for _, ws in toks for w in ws]
    audio, sr = kokoro.create(" ".join(spoken), voice=VOICE, speed=SPEED, lang="en-us")
    assert sr == SR
    audio = trim(np.asarray(audio, dtype=np.float32))
    sf.write(f"{OUT}/line_{i + 1:02d}.wav", audio, SR)
    dur = len(audio) / SR

    # word times inside the line
    weights = np.array([max(1, len(norm(w))) + (2 if w[-1] in ".?!:," else 0) for w in spoken], dtype=float)
    cum = np.concatenate([[0], np.cumsum(weights)]) / weights.sum() * dur
    st, en = cum[:-1].copy(), cum[1:].copy()  # proportional fallback
    heard = ""
    if asr is not None:
        a16 = resample_poly(audio, 2, 3).astype(np.float32)  # Whisper expects 16 kHz
        segs, _ = asr.transcribe(a16, language="en", word_timestamps=True, beam_size=5, condition_on_previous_text=False)
        hw = [w for s in segs for w in s.words]
        heard = " ".join(w.word.strip() for w in hw)
        a, b = [norm(w) for w in spoken], [norm(w.word) for w in hw]
        anchors = {}
        for blk in SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
            for k in range(blk.size):
                anchors[blk.a + k] = hw[blk.b + k]
        # anchored words take ASR times; the rest are spread between neighbours
        keys = sorted(anchors)
        for k in keys:
            st[k], en[k] = anchors[k].start, anchors[k].end
        prev_k, prev_t = -1, 0.0
        for k in keys + [len(spoken)]:
            nxt_t = dur if k == len(spoken) else st[k]
            miss = list(range(prev_k + 1, k))
            if miss:
                w = weights[miss]
                c = np.concatenate([[0], np.cumsum(w)]) / w.sum() * max(0.0, nxt_t - prev_t)
                for j, m in enumerate(miss):
                    st[m], en[m] = prev_t + c[j], prev_t + c[j + 1]
            if k < len(spoken):
                prev_k, prev_t = k, en[k]
        matched = len(keys) / len(spoken)
    else:
        matched = 0.0

    tokens, p = [], 0
    for shown, ws in toks:
        tokens.append({"w": shown, "s": round(clock + float(st[p]), 3), "e": round(clock + float(en[p + len(ws) - 1]), 3)})
        p += len(ws)
    out["lines"].append({"i": i + 1, "start": round(clock, 3), "end": round(clock + dur, 3), "tokens": tokens})
    print(f"L{i + 1:02d} {dur:5.2f}s match {matched:4.0%} | {heard}")
    track.append(audio)
    track.append(np.zeros(int(gap * SR), dtype=np.float32))
    clock += dur + gap

out["voice_end"] = round(clock, 3)
sf.write(f"{OUT}/narration.wav", np.concatenate(track), SR)
json.dump(out, open(f"{OUT}/timing.json", "w"), indent=1)
print("voice ends at", out["voice_end"])
