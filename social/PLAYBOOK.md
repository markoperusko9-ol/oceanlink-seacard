# Ocean Link reach playbook (researched 30 Oct 2026)

Every post follows these rules. They come from official platform statements where they exist
(Instagram/Meta, TikTok, YouTube, LinkedIn) and large 2025–26 studies (Socialinsider, Buffer, Sprout, Emplifi, AuthoredUp).
Re-check this file against the account's own Metricool analytics every Monday (see README step 7).

## 1. Hooks (all platforms)
- **Frame 0 / slide 1 must already show the hook.** No blank, black or fading-in opening — Instagram measures "skip rate" in the first 3 s, Shorts counts "stayed to watch", TikTok uses frame 0 as the default cover. (The template now renders the first slide fully visible at frame 0.)
- Hook ≤ 10 words. State an outcome or a tension, never a topic label ("Your radar is not the look-out" ✔, "COLREG Rule 5" ✘).
- **Slide 2 must also work as a hook on its own** — Instagram re-serves carousels from slide 2 and TikTok viewers often land there.
- Hook styles that test best: story (founder/sea life), contrarian ("X is not Y"), myth vs reality, mistakes, numbered list, POV, and "How to know if [someone] is [doing X to you]" (see "Strategy: macro out" in content/plan.md). Rotate them; don't repeat the same opener two days running.
- Series beat one-offs (feeds now push recurring themes): name them consistently, e.g. "COLREGs in 30 seconds · Rule 5", "Sign-off week", "Certificate check".

## 2. On-screen text and video
- 9:16 safe zone (Reels + TikTok + Shorts combined): all text inside x 120–888, y 288–1248 at 1080×1920. The template enforces this.
- Reading speed: max ~5–10 words per second on screen → titles ≤ 8 words, bodies ≤ 25 words per 4.8 s slide.
- Length 20–35 s; the last slide (CTA) leads straight back into the hook so it loops (replays count as Shorts views).
- Never publish the same render twice; rotate the template `variant` (0/1/2) — the spec's `variant` = day of year % 3.
- Our format is text + music only. Emplifi's 2026 Facebook study: speech in the first 3 s gives ~25% better retention. Real ship footage and (later) a voice line are the biggest upgrades — use footage posts when Marko provides clips.
- Music: only the original music baked in by `social/music.py`; TikTok carousels use `autoAddMusic true` (TikTok's commercial-safe library). Never add commercial tracks.

- Every Reel gets a custom cover image (the hook frame) so the profile grid never shows a blank tile; keep the cover text inside the central 1080×1440 (the grid crops to 3:4).
- Every post is also shared to Instagram and Facebook Stories 30 min after it goes live (Stories reach followers who don't see the feed post).

## 3. Captions and links
| Network | Structure | Links | Hashtags |
|---|---|---|---|
| Instagram | Line 1 = plain keyword headline in sentence case (searchable, e.g. "COLREG Rule 5 look-out explained for deck officers"), then hook, 3–5 short value lines, save/send prompt, "link in bio", one open question | Never a URL (not clickable) — "link in bio" | 3–5, specific, at the end (hard cap 5) |
| Facebook | Same as Instagram, slightly shorter | **No URL in the caption** (Meta: best captions have no links; link-post limit test for Pages). Put `Free on Google Play: oceanlinkai.com` in `firstCommentText` | 2–3 (max 5) |
| TikTok | Photo `title` ≤ 90 chars, keyword first; caption ≤ ~150 chars: keyword phrase + question + hashtags | "link in bio" only, soft — no "download now" (TikTok limits off-platform selling pushes in the Philippines) | 3–5 (hard cap 5) |
| LinkedIn | Line 1 < 40 chars; the hook must land inside the first ~140 chars (before "…see more"); 700–900 chars total; one concrete maritime fact, rule or real example (LinkedIn's 2026 "AI slop" classifier cuts posts with no point of view or substance); 3–5 short value lines; one specific question about real experience | **No URL in the post and no automatic first comment** (link penalty disputed; automated comments are against LinkedIn's 2026 rules). Mention "Ocean Link (free on Google Play)" in plain text; the link lives on the Page button | 2–3 niche, at the end |
| YouTube Shorts | `title` ≤ 100 chars, keyword first, no clickbait; description 2–4 keyword-rich lines, then 3 hashtags (the first 3 show above the title) | No URL (not clickable in Shorts) — "Search Ocean Link on Google Play" | 3 in the description, never more than 15 |

- Comment prompts ask for real experience ("Which certificate always catches you out?"). **Banned:** "comment YES", "comment X to get…", "tag someone", "like if", "agree?", "share if" — Meta and LinkedIn demote engagement bait.
- Send/save prompts are encouraged (sends are one of Instagram's top three signals): "Save this for your next fog watch", "Send this to a shipmate joining next month".
- Every caption is written for its network — never paste one caption everywhere.
- Set `mediaAltText` on every carousel image (one short sentence per slide). Google now indexes public Instagram posts from professional accounts using captions and alt text.

## 4. Formats per network
- Instagram: carousels currently get the most views per post for accounts our size (Socialinsider 2026); Reels for reach to non-followers. Up to 20 slides; we use 6–9.
- Facebook: multi-photo posts outperform Reels for small Pages (Socialinsider); keep both.
- TikTok: photo carousels ≈ video reach with +81% engagement but fewer shares (Fanpage Karma 2025). Mainly a Philippines audience (TikTok is banned in India).
- LinkedIn: multi-image and document posts lead engagement for Pages; video views on Pages fell in 2026. **The founder resharing a post from his personal profile in his own words is the biggest lever (personal posts get many times the engagement of Page posts).**
- YouTube: Shorts are the only YouTube format here; a playlist per series helps binge-watching.

## 5. Timing (Asia/Tomsk; IST = Tomsk − 1:30, PHT = Tomsk + 1)
- Carousels: TikTok 10:00 · LinkedIn 11:00 (09:30 IST) · Facebook 12:00 · Instagram 13:00 (11:30 IST / 14:00 PHT).
- Videos: LinkedIn 15:30 (14:00 IST) · Facebook Reel 20:00 · TikTok 20:00 (21:00 PHT) · YouTube 20:00 (18:30 IST) · Instagram Reel 21:00 (19:30 IST / 22:00 PHT).
- No study covers Indian/Filipino seafarers specifically, and seafarers at sea keep odd hours — after 30 days, move each slot to the account's own best hours from Metricool.

## 6. Hard limits
- Originality: our own templates and footage only; no third-party clips, watermarks or reposts.
- Facts: every regulation/certificate line is checked against an official source before posting.
- No job vacancies, invented numbers, testimonials, faces, ship or company names.

## Key sources
- Instagram Reels tips (Sep 2026): socialmediatoday.com/news/instagram-shares-reels-creation-tips-in-new-guide/831551
- Mosseri — top signals are watch time, likes, sends (Jan 2025): socialmediatoday.com/news/instagram-shares-algorithm-2025/738034
- Instagram 5-hashtag cap (Dec 2025): socialmediatoday.com …/808309
- Meta unoriginal-content rules (Jul 2025): creators.facebook.com/blog/combating-unoriginal-content
- Facebook link-post limit test (Dec 2025): techcrunch.com/2025/12/17
- TikTok creative best practices / search creative: ads.tiktok.com/help/article/creative-best-practices, …/search-ads-creative
- TikTok For You eligibility: tiktok.com/community-guidelines/en/fyf-standards
- TikTok 5-hashtag limit (Aug 2025): socialmediatoday.com/news/tiktok-implements-five-hashtag-limit-per-post/757857
- YouTube Shorts views and engaged views: support.google.com/youtube/answer/10059070, /12220281
- YouTube inauthentic-content policy (Jul 2025): support.google.com/youtube/answer/1311392
- LinkedIn feed engineering (Mar 2026): linkedin.com/blog/engineering/feed/engineering-the-next-generation-of-linkedins-feed
- LinkedIn on AI slop (Sep 2026): news.linkedin.com/2026/how-linkedin-is-tackling-ai-slop
- LinkedIn benchmarks (Mar 2026): socialinsider.io/blog/linkedin-benchmark
- Socialinsider Instagram/Facebook benchmarks 2026; Fanpage Karma carousel vs video (Jun 2025); Emplifi Facebook Reels study (Mar 2026); Buffer best times/frequency (2025–26).
