"""Job-board and pinned reels in the big-caption-hook format (social/hook.html).

  python3 social/job_reel.py WEEK.json SPEC_DIR        # writes one reel.py spec per item
  FOOTAGE_DIRS=... python3 social/reel.py SPEC_DIR/<id>.json OUT_DIR

WEEK.json: {"stamp": "Ocean Link job board · 3–9 Nov 2026", "reels": [ITEM, ...]}
ITEM: {"id": "...", "seed": 3,
       "hook": [["How many", 76, 0], ["CHIEF", 190, 1], ["OFFICER", 190, 1], ["jobs in 7 days?", 92, 0]],   # [text, px, key word?]
       "pin": "How many Chief Officer / jobs in 7 days?",
       "a": ["*Bulk carriers*", "*Oil tankers*", "*LPG* and product tankers"],      # three captions, 3-5 words each
       "b": ["*28* licensed agencies", "Licence numbers *shown*", "Never *pay* for a job"],
       "num": 39  or  "word": "FREE",        # the answer, revealed in the last third
       "label": "Chief Officer jobs / posted in 7 days", "stamp": true,
       "end": {"line": "What rank are you *looking for?*", "cta": "Find yours: link in bio"},
       "cuts": [[clip, start, speed, x, gamma], x5]}     # hook, a, b, reveal, end card

Rules baked in (content/plan.md): counts only, never a single vacancy; no agency, ship or company names; no salaries;
every number comes from the live job board and carries the period stamp on screen.
One beat = 0.4 s. Hook 0-7, captions 7-21, reveal 21-29, end card 8 beats: 14.8 s.
"""
import json, os, sys

HOOK, A_END, B_END, REV_END, END_BEATS = 7, 14, 21, 29, 8
FX = [["push"], ["whip", "push"], ["punch", "push"], ["flash", "push"], ["push"]]


def cut(c, beats, fx):
    clip, start, speed, x, gamma = c
    return {"clip": clip, "start": start, "beats": beats, "speed": speed, "x": x, "gamma": gamma, "fx": fx}


def build(item, stamp):
    caps = [{"from": 0, "to": HOOK, "style": "hook", "lines": [{"t": t, "s": s, "k": bool(k)} for t, s, k in item["hook"]]},
            {"from": HOOK, "to": B_END, "style": "pin", "text": item["pin"]}]
    for group, b0, b1 in ((item["a"], HOOK, A_END), (item["b"], A_END, B_END)):
        step = (b1 - b0) / len(group)
        for i, text in enumerate(group):
            caps.append({"from": round(b0 + i * step, 2), "to": round(b0 + (i + 1) * step, 2), "style": "cap", "text": text})
    rev = {"from": B_END, "to": REV_END, "style": "num", "label": item["label"]}
    if "word" in item:
        rev.update(word=item["word"], size=item.get("wsize", 230))
    else:
        rev.update(v0=0, v1=item["num"], dur=1.2)
    caps.append(rev)
    if item.get("stamp"):
        caps.append({"from": B_END + 0.8, "to": REV_END, "style": "cap", "text": item["stamp"] if isinstance(item["stamp"], str) else stamp, "size": 44, "y": 1236})
    c = item["cuts"]
    end = dict(cut(c[4], END_BEATS, FX[4]), line=item["end"]["line"], cta=item["end"]["cta"], scrim=0.5)
    return {"id": item["id"], "seed": item.get("seed", 2), "template": "hook.html",
            "cuts": [cut(c[0], HOOK, FX[0]), cut(c[1], A_END - HOOK, FX[1]), cut(c[2], B_END - A_END, FX[2]), cut(c[3], REV_END - B_END, FX[3])],
            "caps": caps, "end": end}


if __name__ == "__main__":
    week = json.load(open(sys.argv[1])); out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    for item in week["reels"]:
        json.dump(build(item, week.get("stamp", "")), open(os.path.join(out, item["id"] + ".json"), "w"), indent=1, ensure_ascii=False)
        print(item["id"])
