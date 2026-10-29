# Ocean Link daily posting — how a run works

Everything needed to make and schedule the day's posts lives in this repo:

- **`social/PLAYBOOK.md` — reach rules per platform (hooks, captions, links, hashtags, timing). Read it every run; it overrides anything below that disagrees.**

- `content/plan.md` — slots, pillars, hard rules, backlog and log. Read it first, follow it exactly.
- `content/posts/*.json` — one spec per post (kept as a record).
- `social/slide.html` + `social/render.py` — the only template. Brand: abyss-dark, Inter, flat, no shadows.
- `media/<YYYY-MM-DD>-am|pm/` — rendered files, served publicly by GitHub Pages at `https://card.oceanlinkai.com/media/...` so Metricool can fetch them.

## 1. Pick what to make
1. Today's date in Asia/Tomsk. Target = the earliest day from tomorrow up to 3 days ahead whose AM or PM slot is missing.
   Check `getScheduledPosts` (brandId 7716383, timezone Asia/Tomsk) for that day as well as the log, so nothing is doubled.
2. Take the next unticked backlog items. AM and PM on the same day must be different pillars.
3. Fact-check every regulation/certificate claim with a web search against an official or reputable source. If it can't be confirmed, cut it.

## 2. Write the spec — `content/posts/<date>-<am|pm>-<slug>.json`
```json
{"id":"2026-11-01-am-colreg-rule5","seed":4,"slides":[
  {"type":"cover","kicker":"COLREG · Rule 5","title":"Your phone is *not* a look-out.","sub":"What Rule 5 actually asks for.","dur":3.2},
  {"type":"point","n":1,"title":"Sight and hearing","body":"…","chip":"Rule 5","tone":"accent","dur":4.8},
  {"type":"list","kicker":"…","title":"…","items":[{"t":"…","tone":"valid"},{"t":"…","tone":"warning"},{"t":"…","tone":"critical"}],"dur":4.8},
  {"type":"vs","kicker":"Myth vs reality","a_label":"Myth","a":"…","b_label":"Reality","b":"…","dur":4.8},
  {"type":"cta","question":"…? (comment prompt)","line":"…","dur":3.2}
]}
```
- 5–9 slides. Slide 1 is the hook (outcome or tension, ≤ 10 words); slide 2 must also hook on its own; last slide is always `cta` with a real-experience question.
- Set `"variant"` to the day of year % 3 so consecutive posts don't look identical.
- `*word*` in titles = cyan accent. Keep titles short (≤ 8 words), bodies ≤ 25 words.
- Durations must be multiples of 1.6 s (music bars): cover/cta 3.2, text slides 4.8.
- Tones: valid (cyan #00B0D2), warning, critical, neutral, accent.

## 3. Render and check
```
python3 social/render.py content/posts/<id>.json /tmp/<id>            # AM: stills
python3 social/render.py content/posts/<id>.json /tmp/<id> --video    # PM: stills + video.mp4
```
Exit code 2 = text too long → shorten and render again. Open `contact.jpg`, one `story_*.jpg` and two frames of `video.mp4` with the Read tool and look at them before publishing.

## 4. Publish media
Copy outputs to `media/<date>-<am|pm>/` (+ a `ready.txt` containing `ok`), commit (end the message with the Co-Authored-By / Claude-Session lines), `git fetch origin main`, push to `main`.
GitHub Pages takes ~1–3 minutes: WebFetch `https://card.oceanlinkai.com/media/<folder>/ready.txt?v=<n>` (new `v` each try, ~60 s apart) until it returns `ok`.

## 5. Schedule in Metricool (`createScheduledPost`, blogId 7716383, timezone Asia/Tomsk)
Separate post per network; captions follow the table in `social/PLAYBOOK.md` §3 exactly (structure, links, hashtag counts). Times per `content/plan.md`. Media = the card.oceanlinkai.com URLs.
- **Instagram**: carousel `instagramData.type "POST"` with feed_*.jpg; video `"REEL"` + `showReelOnFeed true`. No URL ("link in bio"). Max 5 hashtags.
- **Facebook**: carousel `facebookData.type "POST"` with feed_*.jpg; video `"REEL"`. No URL in `text`; `firstCommentText`: `Free on Google Play: oceanlinkai.com`.
- **TikTok**: carousel = story_*.jpg, `tiktokData.title` REQUIRED (≤ 90 chars, keyword first), `autoAddMusic true`; video: `title` required (use the caption). `privacyOption PUBLIC_TO_EVERYONE`, `commercialContentOwnBrand true`, `isAigc false`. Max 5 hashtags.
- **LinkedIn** (company page): `linkedinData {"type":"post"}`. No URL anywhere and **no `firstCommentText`**. Mention "Ocean Link (free on Google Play)" in plain text.
- **YouTube**: video only, `youtubeData {"title", "type":"short", "privacy":"public", "madeForKids":false, "category":"EDUCATION" or "PEOPLE_BLOGS", "isAiGeneratedContent":false}`. No URL in the description; 3 hashtags at its end.
- Carousels: `mediaAltText` = one short sentence per image, same order as `media`.
- Video posts: `videoCoverMilliseconds` 300 (the hook is fully drawn at frame 0).
- Before creating, re-read every caption against the banned list in PLAYBOOK §3 ("comment YES", "tag someone", "like if", "agree?", "share if").
Metricool copies the media at creation (response shows static.metricool.com URLs) — check every response has them.

## 6. Close out
- Tick the backlog item and add a log line with the planner links; commit + push.
- Delete the `media/` folders of every post you created this run once each Metricool response shows static.metricool.com copies (Metricool keeps its own copy, so the public files are no longer needed); commit + push.
- If fewer than 10 backlog items remain, add 15 new ones that follow the pillars and hard rules.
- Finish with a short summary for Marko: what was scheduled, when, and the planner links. Add one "Reshare on your personal LinkedIn" suggestion: the strongest post of the day plus 2–3 lines he could post in his own words (he posts it himself; never post as him).

## 7. Weekly review (Mondays only)
1. Load `getAnalyticsAvailableMetrics` / `getAnalyticsDataByMetrics` and pull the last 7 days for Instagram, Facebook, TikTok, LinkedIn and YouTube.
2. Rank posts by saves + shares/sends per reach (Instagram/TikTok), average watch time (videos), comments and impressions (LinkedIn).
3. Add a dated "Learnings" entry to `content/plan.md`: top 2 and bottom 2 posts with the likely reason (hook style, topic, format), and move similar backlog items up or down. After 30 days of data, adjust slot times to the account's own best hours.
