#!/usr/bin/env python3
"""AI images for Ocean Link news posts.

Used by the "Ocean Link news images" scheduled task. Run from the repo root.

  python3 scripts/news_ai_images.py slug <link>
      Prints the story name used for file names (Marine Insight URL slug).

  python3 scripts/news_ai_images.py decode <saved_drive_result> <out.png>
      Writes the image from a saved Google Drive download_file_content result
      (the JSON with a base64 "content" field).

  python3 scripts/news_ai_images.py publish <png> <source_url>
      Crops the image to 16:9, resizes it to 1280x720, adds the small
      "AI illustration" tag, saves media/news/ai/<slug>.jpg and adds the
      story to media/news/ai/index.json (newest first, last 60 kept).

Bubble (process_single_article1) reads index.json when it creates a post:
when the post's source_url is listed, the post gets this image; otherwise it
keeps the library photo Claude picked.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "media" / "news" / "ai"
INDEX = OUT_DIR / "index.json"
FONT = REPO / "scripts" / "fonts" / "Inter-SemiBold.otf"
BASE_URL = "https://card.oceanlinkai.com/media/news/ai/"
KEEP = 60


def clean_url(link: str) -> str:
    """Same as Bubble's source_link: the link without its ?query part."""
    return link.strip().split("?")[0]


def slug(link: str) -> str:
    path = urlsplit(clean_url(link)).path.strip("/")
    name = path.split("/")[-1] if path else ""
    if not name:
        raise SystemExit(f"no story name in link: {link}")
    return name


def load_index() -> dict:
    if INDEX.exists():
        return json.loads(INDEX.read_text())
    return {"updated": "", "items": []}


def tag(img: Image.Image) -> Image.Image:
    """Small 'AI illustration' pill, bottom-left (EU AI Act Art. 50 disclosure)."""
    img = img.convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    font = ImageFont.truetype(str(FONT), 20)
    text = "AI illustration"
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    pad_x, pad_y, margin = 12, 7, 20
    w, h = (r - l) + pad_x * 2, (b - t) + pad_y * 2
    x0, y0 = margin, img.height - margin - h
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=7, fill=(5, 6, 9, 190))
    d.text((x0 + pad_x - l, y0 + pad_y - t), text, font=font, fill=(242, 244, 247, 255))
    return Image.alpha_composite(img, layer).convert("RGB")


def to_16x9(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    w, h = img.size
    target = 16 / 9
    if w / h > target:  # too wide: trim the sides
        nw = round(h * target)
        x = (w - nw) // 2
        img = img.crop((x, 0, x + nw, h))
    else:  # too tall: trim top and bottom equally
        nh = round(w / target)
        y = (h - nh) // 2
        img = img.crop((0, y, w, y + nh))
    return img.resize((1280, 720), Image.LANCZOS)


def publish(png: str, source_url: str) -> None:
    src = clean_url(source_url)
    name = slug(src)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{name}.jpg"
    tag(to_16x9(Image.open(png))).save(out, "JPEG", quality=84, optimize=True, progressive=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    idx = load_index()
    items = [i for i in idx.get("items", []) if i.get("source_url") != src]
    items.insert(0, {"source_url": src, "image": BASE_URL + out.name, "added": now})
    idx = {"updated": now, "items": items[:KEEP]}
    INDEX.write_text(json.dumps(idx, indent=1) + "\n")
    print(f"{out.relative_to(REPO)}  {out.stat().st_size // 1024} KB  -> {BASE_URL + out.name}")


def decode(saved: str, out: str) -> None:
    """Turn a saved Google Drive download_file_content result into the image file."""
    import base64
    d = json.loads(Path(saved).read_text())
    data = base64.b64decode(d["content"])
    Path(out).write_bytes(data)
    print(d.get("title", ""), f"{len(data) // 1024} KB -> {out}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "slug":
        print(slug(sys.argv[2]))
    elif len(sys.argv) >= 4 and sys.argv[1] == "decode":
        decode(sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 4 and sys.argv[1] == "publish":
        publish(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__)
