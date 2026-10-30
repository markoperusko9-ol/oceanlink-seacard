"""Render an Ocean Link post from a JSON spec.

  python3 social/render.py SPEC.json OUTDIR            -> carousel stills
  python3 social/render.py SPEC.json OUTDIR --video    -> stills + 9:16 video.mp4 with music

Outputs in OUTDIR:
  feed_01.jpg ...   1080x1350  (Instagram / Facebook / LinkedIn carousel)
  story_01.jpg ...  1080x1920  (TikTok photo carousel)
  video.mp4         1080x1920, 30 fps, AAC, -14 LUFS (Reels / TikTok / Shorts / LinkedIn video)
  contact.jpg       all feed slides side by side, for checking
Exit code 2 if any slide's text does not fit (shorten it and render again).
"""
import json, os, sys, subprocess, shutil
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from music import make_bed

spec_path, out = sys.argv[1], sys.argv[2]
want_video = '--video' in sys.argv
spec = json.load(open(spec_path))
slides = spec['slides']
os.makedirs(out, exist_ok=True)
overflow = []

VARIANT = int(spec.get('variant', spec.get('seed', 0))) % 3

def shot(pg, slide, i, n, w, h, mode, t, path):
    ok = pg.evaluate("([s,i,n,o])=>{build(s,i,n,o);return fit()}", [slide, i, n, {"w": w, "h": h, "mode": mode, "variant": VARIANT}])
    pg.set_viewport_size({"width": w, "height": h})
    pg.evaluate(f"render({t})")
    pg.screenshot(path=path, type='jpeg', quality=92, clip={"x": 0, "y": 0, "width": w, "height": h})
    return ok

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto('file://' + os.path.join(HERE, 'slide.html')); pg.wait_for_timeout(300)
    for i, s in enumerate(slides):
        for kind, (w, h) in (('feed', (1080, 1350)), ('story', (1080, 1920))):
            ok = shot(pg, s, i, len(slides), w, h, 'still', 99, f"{out}/{kind}_{i+1:02d}.jpg")
            if not ok: overflow.append(f"{kind} slide {i+1}")
    if want_video:
        tmp = f"{out}/_v"; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
        scenes, cuts, t = [], [], 0.0
        for i, s in enumerate(slides):
            dur = float(s.get('dur', 3.2))
            fr = f"{tmp}/s{i:02d}"; os.makedirs(fr)
            pg.evaluate("([s,i,n,o])=>{build(s,i,n,o);return fit()}", [s, i, len(slides), {"w": 1080, "h": 1920, "mode": "video", "variant": VARIANT}])
            pg.set_viewport_size({"width": 1080, "height": 1920})
            nf = int(round(dur * 30))
            inst = 'true' if i == 0 else 'false'
            for f in range(nf):
                pg.evaluate(f"render({f/30},{inst})")
                pg.screenshot(path=f"{fr}/{f:04d}.jpg", type='jpeg', quality=92)
            sc = f"{tmp}/scene{i:02d}.mp4"
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-i", f"{fr}/%04d.jpg",
                                "-vf", "format=yuv420p",
                                "-frames:v", str(int(round(dur * 30))), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                                "-pix_fmt", "yuv420p", "-r", "30", "-g", "60", "-video_track_timescale", "15360",
                                f"{sc[:-4]}.tmp.mp4"])
            if r.returncode: sys.exit("scene encode failed")
            os.replace(f"{sc[:-4]}.tmp.mp4", sc); scenes.append(sc)
            if i > 0: cuts.append(round(t, 3))
            t += dur
    b.close()

# contact sheet of the feed slides
from PIL import Image
ims = [Image.open(f"{out}/feed_{i+1:02d}.jpg").resize((360, 450)) for i in range(len(slides))]
sheet = Image.new('RGB', (370 * len(ims), 450), '#222')
for k, im in enumerate(ims): sheet.paste(im, (370 * k, 0))
sheet.save(f"{out}/contact.jpg", quality=85)

if want_video:
    lst = f"{tmp}/list.txt"
    open(lst, 'w').write(''.join(f"file '{s}'\n" for s in scenes))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", f"{tmp}/v.mp4"], check=True)
    make_bed(t, cuts, f"{tmp}/m.wav", seed=int(spec.get('seed', len(spec.get('id', 'x')))))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/m.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000", f"{tmp}/mn.wav"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/mn.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", f"{out}/video.tmp.mp4"], check=True)
    os.replace(f"{out}/video.tmp.mp4", f"{out}/video.mp4")
    # cover.jpg: the hook frame, used as the Reel cover (Instagram/Facebook/LinkedIn videoThumbnailUrl)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "0.3", "-i", f"{out}/video.mp4", "-frames:v", "1", "-q:v", "2", f"{out}/cover.jpg"], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"video.mp4 {t:.1f}s")

print(f"rendered {len(slides)} slides -> {out}")
if overflow:
    print("TEXT TOO LONG, shorten:", ", ".join(overflow)); sys.exit(2)
