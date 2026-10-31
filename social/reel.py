"""Dynamic real-footage reel: beat-synced fast cuts, zoom punches, shake, whip transitions, flashes,
kinetic word-by-word captions, ticking counters, timestamps, original music + hit/whoosh sounds.

  python3 social/reel.py SPEC.json OUTDIR

SPEC (one beat = 0.4 s, the music grid):
{"id": "...", "seed": 2,
 "cuts": [ {"clip": "16359654", "start": 3.0, "beats": 2, "speed": 1.0, "x": 0.5, "y": 0.5,
            "fx": ["punch", "push", "shake", "flash", "whip", "slow"]}, ... ],
 "caps": [ {"from": 0, "to": 8, "style": "hook|stamp|count|tag", "text": "POV: *night watch*", "y": 820, "size": 100,
            "instant": true, "karaoke": false, "time": "03:00", "from_v": 0, "to_v": 75, "suf": "%", "dec": 0, "dur": 1.0} ],
 "end": {"beats": 8, "clip": "...", "start": 0, "line": "Built at sea, *for seafarers.*"}}

cuts play back to back; caps are timed in beats from the start, independent of cuts (text holds while footage cuts).
" / " in caption text forces a line break; *word* = cyan. The first caption should use "instant": true (hook visible at frame 0).
Outputs OUTDIR/video.mp4 (1080x1920, 30 fps, -14 LUFS), cover.jpg, contact.jpg. Exit 2 if a caption leaves the safe zone.
"""
import json, os, sys, glob, subprocess, shutil
import numpy as np, cv2
from scipy.io import wavfile
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from music import make_bed

BEAT, FPS, W, H = 0.4, 30, 1080, 1920
MW, MH = 1188, 2112                      # 10 % margin for zoom and shake
DIRS = [d for d in os.environ.get('FOOTAGE_DIRS', '/mnt/user-data/uploads/Vessel Videos/Stock:/home/claude/work/own:/mnt/user-data/uploads/Vessel Videos').split(':') if d]
spec_path, out = sys.argv[1], sys.argv[2]
spec = json.load(open(spec_path))
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(int(spec.get('seed', 1)))


def find(clip):
    for d in DIRS:
        p = os.path.join(d, clip)
        if os.path.exists(p): return p
        hits = sorted(f for f in glob.glob(os.path.join(d, '*')) if os.path.basename(f).split('_')[0].split('-')[0] == clip
                      or os.path.basename(f).startswith(clip))
        if hits: return hits[0]
    sys.exit(f'clip not found: {clip}')


def frames_of(cut, n):
    """n frames of the cut, scaled to cover MWxMH, graded, as uint8 RGB arrays."""
    src = find(cut['clip']); sp = float(cut.get('speed', 1.0))
    x, y = cut.get('x', 0.5), cut.get('y', 0.5)
    need = n / FPS * sp + 0.2
    vf = (f"setpts=PTS/{sp},fps={FPS},scale=w='if(gt(a,{MW}/{MH}),-2,{MW})':h='if(gt(a,{MW}/{MH}),{MH},-2)',"
          f"crop={MW}:{MH}:(iw-{MW})*{x}:(ih-{MH})*{y},eq=contrast=1.07:saturation=1.15:brightness=-0.015:gamma={cut.get('gamma', 1.0)},format=rgb24")
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(cut.get('start', 0)), '-t', f'{need:.3f}', '-i', src,
                          '-vf', vf, '-f', 'rawvideo', '-'], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8)
    k = len(fr) // (MW * MH * 3)
    if k == 0: sys.exit(f'no frames from {src} at {cut.get("start", 0)}')
    fr = fr[:k * MW * MH * 3].reshape(k, MH, MW, 3)
    idx = [min(i, k - 1) for i in range(n)]
    return [fr[i] for i in idx]


def fx_frame(img, cut, i, n, nxt_whip):
    fx = cut.get('fx', [])
    t = i / FPS; dur = n / FPS
    z = 1.0
    if 'push' in fx: z *= 1.0 + 0.07 * (t / max(dur, 0.01))
    if 'punch' in fx: z *= 1.0 + 0.16 * (1 - min(1, t / 0.22)) ** 3
    dx = dy = 0.0
    if 'shake' in fx and t < 0.35:
        a = 22 * (1 - t / 0.35); dx, dy = rng.uniform(-a, a), rng.uniform(-a, a)
    M = np.float32([[z, 0, (1 - z) * MW / 2 + dx - (MW - W) / 2], [0, z, (1 - z) * MH / 2 + dy - (MH - H) / 2]])
    o = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    whip = ('whip' in fx and i < 3) or (nxt_whip and i >= n - 3)
    if whip:
        k = 61; ker = np.zeros((1, k), np.float32); ker[0, :] = 1.0 / k
        o = cv2.filter2D(o, -1, ker)
        o = np.roll(o, (-60 if i >= n - 3 else 60), axis=1)
    if 'flash' in fx and i < 3:
        a = [0.75, 0.4, 0.15][i]
        o = (o.astype(np.float32) * (1 - a) + 255 * a).astype(np.uint8)
    return o


cuts = spec['cuts']
end = spec.get('end')
segs = list(cuts) + ([dict(end, fx=end.get('fx', ['push']))] if end else [])
nframes = [int(round(float(c['beats']) * BEAT * FPS)) for c in segs]
total_frames = sum(nframes); total = total_frames / FPS
end_t0 = sum(nframes[:-1]) / FPS if end else None

# caption list in seconds
caps = []
for c in spec.get('caps', []):
    d = dict(c); d['t0'] = c['from'] * BEAT; d['t1'] = c['to'] * BEAT
    if c.get('style') == 'count': d['from'] = c['from_v']; d['to'] = c['to_v']
    caps.append(d)
endcfg = dict(t0=end_t0, line=end.get('line'), cta=end.get('cta')) if end else None

enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', '-g', '60',
                        os.path.join(out, 'v.mp4')], stdin=subprocess.PIPE)
bad = []
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': W, 'height': H})
    pg.goto('file://' + os.path.join(HERE, 'reel.html')); pg.wait_for_timeout(200)
    pg.evaluate('([c,e])=>setup(c,e)', [caps, endcfg])
    bad = pg.evaluate('check()')
    last_sig, ov = None, None
    f_abs = 0
    for si, (c, n) in enumerate(zip(segs, nframes)):
        imgs = frames_of(c, n)
        nxt_whip = si + 1 < len(segs) and 'whip' in segs[si + 1].get('fx', [])
        for i in range(n):
            t = f_abs / FPS
            sig = pg.evaluate(f'drawAt({t})')
            if sig != last_sig:
                png = pg.screenshot(omit_background=True, type='png')
                arr = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_UNCHANGED)   # BGRA
                ov = (arr[:, :, [2, 1, 0]].astype(np.float32), arr[:, :, 3:4].astype(np.float32) / 255.0) if arr is not None and arr.shape[2] == 4 else None
                last_sig = sig
            frame = fx_frame(imgs[i], c, i, n, nxt_whip).astype(np.float32)
            if ov is not None and sig:
                frame = frame * (1 - ov[1]) + ov[0] * ov[1]
            enc.stdin.write(frame.clip(0, 255).astype(np.uint8).tobytes())
            f_abs += 1
    b.close()
enc.stdin.close(); enc.wait()

# audio: original bed (beat from frame 0), hits on punch/flash cuts, whooshes on whips
cut_times, t = [], 0.0
hits, whooshes = [], []
for c, n in zip(segs, nframes):
    fx = c.get('fx', [])
    if t > 0: cut_times.append(round(t, 3))
    if 'punch' in fx or 'flash' in fx: hits.append(t)
    if 'whip' in fx: whooshes.append(t)
    t += n / FPS
bed_cuts = [0.0] + [c for c in cut_times if c in [round(h, 3) for h in hits]] + ([round(end_t0, 3)] if end else [])
bed_cuts = sorted(set(bed_cuts))
make_bed(total, bed_cuts, os.path.join(out, 'm.wav'), seed=int(spec.get('seed', 2)))
sr, m = wavfile.read(os.path.join(out, 'm.wav')); m = m.astype(np.float64)
r2 = np.random.default_rng(7)
def add(sig, t0, g):
    i = int(t0 * sr); j = min(len(m), i + len(sig))
    if 0 <= i < len(m): m[i:j] += g * sig[:j - i, None]
from scipy.signal import butter, sosfilt
for tw in whooshes:          # band-passed noise sweep centred on the cut
    n = int(0.36 * sr); tt = np.arange(n) / sr
    env = np.sin(np.pi * tt / 0.36) ** 2
    s = sosfilt(butter(2, [600, 5000], btype='band', fs=sr, output='sos'), r2.standard_normal(n)) * env
    add(s / (np.abs(s).max() + 1e-9), tw - 0.18, 0.35)
for th in hits:              # sub hit
    n = int(0.5 * sr); tt = np.arange(n) / sr
    f = 40 + 70 * np.exp(-tt * 30)
    s = np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-tt * 6)
    add(s, th, 0.45)
m /= np.abs(m).max() * 1.05
wavfile.write(os.path.join(out, 'm2.wav'), sr, m.astype(np.float32))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(out, 'm2.wav'), '-af', 'loudnorm=I=-14:TP=-1.5:LRA=9', '-ar', '48000',
                os.path.join(out, 'mn.wav')], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(out, 'v.mp4'), '-i', os.path.join(out, 'mn.wav'), '-map', '0:v', '-map', '1:a',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', os.path.join(out, 'video.mp4')], check=True)
for f in ('v.mp4', 'm.wav', 'm2.wav', 'mn.wav'): os.remove(os.path.join(out, f))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '0.15', '-i', os.path.join(out, 'video.mp4'), '-frames:v', '1', '-q:v', '2',
                os.path.join(out, 'cover.jpg')], check=True)
# contact sheet: 10 evenly spaced frames
from PIL import Image
ims = []
for k in range(10):
    fp = os.path.join(out, f'_c{k}.jpg')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{total * (k + 0.5) / 10:.2f}', '-i', os.path.join(out, 'video.mp4'), '-frames:v', '1', '-vf', 'scale=216:384', fp])
    ims.append(Image.open(fp))
sheet = Image.new('RGB', (226 * 10, 384), '#222')
for k, im in enumerate(ims): sheet.paste(im, (226 * k, 0))
sheet.save(os.path.join(out, 'contact.jpg'), quality=85)
for k in range(10): os.remove(os.path.join(out, f'_c{k}.jpg'))
print(f'video.mp4 {total:.1f}s, {len(segs)} cuts -> {out}')
if bad:
    print('CAPTIONS OUTSIDE SAFE ZONE:', bad); sys.exit(2)
