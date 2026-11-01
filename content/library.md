# Ocean Link video library (PM slot source)

Every PM slot is a **real finished video** from this library: never a text-template video (Marko, 31 Oct 2026: "too many posts that are basic text on screen"). The AM slot stays the macro-out carousel/video from `content/plan.md`.

All files live in Marko's Google Drive. Get them with the Google Drive connector:
`search_files` (query below) → `download_file_content(fileId)` → the result is saved as JSON with a base64 `content` field → decode it to an .mp4 with Python. The connector refuses files over 10 MB.

## Rotation

**Every 📚 Learn slot in `content/plan.md` is a full COLREG lesson from §2, never a quiz** (Marko, 1 Nov 2026: the lessons were cut under 3 minutes so they can go on every network; posting the short quizzes instead of them is wrong). Take the next unused lesson in §2's order. Quizzes (§3) are not posted while any lesson is unused; when every lesson has run, tell Marko in the run summary before using a quiz. Never repost a file listed as used unless 60 days have passed.

## 1. Promos (Drive folder `1G0WHBeFH-A3PRsxkuy60zLozpVAvFvHw`)

| File | Drive id | Size | What it is | Status |
|---|---|---|---|---|
| ocean-link-sea-card-reel-final.mp4 | 19zXAlF9FjXw8m54f_08vFzmK6OctDsmL | 3.3 MB, 42 s | "How many days have you spent at sea?" Sea Card demo | Posted 1 Nov PM |
| ocean-link-crew-promo-voice.mp4 | 1iIgAbfmXIY9IuYD_pD4lP8KIwCy20I98 | 1.6 MB, 28 s | "Remember the crew from your last ship?" Crew tab in SeaFeed. Drive file has voice only, no music: add a bed before any reuse | Scheduled 2 Nov PM (with music added) |
| ocean_link_supercharged_vo.mp4 | 10NEt5jv_un6uDAtcb876LcLpJTqN_nIz | 13 MB | "LinkedIn for seafarers. But supercharged." 5 power-ups, voiceover | Scheduled 6 Nov PM |
| ocean_link_network_vo.mp4 | 10IJ-fvzDfDzHuvTbGznUHupwxMbtWdb3 | 13.9 MB, 33.5 s | "You've missed birthdays for this job… Your career. Finally seen." voiceover | Unused, link-shared (not yet frame-checked) |
| ocean_link_promo-2.mp4 | 1fACeNH7O6mE9ofLyHv2dvi0QZd_5OYwG | 23.4 MB, ~40 s | Full feature tour with voiceover: snap a certificate, sea time, jobs for your rank, CV, COLREG quizzes, Sea Feed, chat, licensed agencies | Scheduled 8 Nov PM |
| OceanLink_Reel_9x16.mp4 | 1z-RPVmBqfbU1eZLESYXSy5gbZaaaFoMT | 21.7 MB, 24 s | Music-only motion promo: six modules fold into the six logo squares | Posted 4 Nov PM from the laptop copy, with the agency name on the job card and the vessel names blurred |

Skip: `ocean_link_network.mp4` (music-only twin of network_vo), `ocean_link_supercharged_vo-1.mp4` (duplicate). Already posted 30 Oct: POV "120 days at sea" and the free CV "Them/Me" promo.

**Promos over 10 MB** can't be downloaded here. Metricool can't read private Drive files from a link, even with Drive connected in its UI. The promos above are set to "anyone with the link" (Marko, 2 Nov 2026), so the built-in browser on his laptop can download them (drive.usercontent.google.com/download?id=<id>&export=download) and they get staged, frame-checked for agency/ship/company names, and published from GitHub Pages like every other video. Metricool fetches them itself only if Google Drive is connected in Metricool (Planning → multimedia icon → Drive → Connect). Use the Drive link `https://drive.google.com/file/d/<id>/view` as `media`. If Metricool answers `Failed to normalize media`, Drive isn't connected yet: use the next quiz or lesson for that slot, keep the promo for later, and tell Marko in the run summary. Covers for these are already rendered at `media/showcase/super|network|promo2/cover.jpg`.

## 2. COLREG lessons (Drive folder `1DlEr7rwIyp_uQJJIity2Z8pUgYh9yfPK`, query `title contains '_social'`)

Animated lessons from the Learn tab, 4–6 MB, 1:48–2:23 (all under 3 min). Download from Drive (under 10 MB), then:
- **Add music:** the Drive files are voice-only. Run `python3 social/lesson_mix.py <in>.mp4 video.mp4 <seed>` (bed ~19 dB under the voice, −14 LUFS).
- **Cover:** one `cover` slide through `social/render.py`, `story_01.jpg` → `cover.jpg`.
- **Per network:** Instagram Reel, TikTok, YouTube Short and LinkedIn take the full video. Facebook: `facebookData.type "POST"` with a `title` (over 90 s, not a Reel). Story: `cover.jpg` (over 60 s).
- Host at `media/showcase/<lesson>/` like every other video.

Used: l13 Rule 19 (5 Nov PM) · l07 Rule 13 (2 Nov AM) · l03 Rule 8 (3 Nov PM) · l09 Rules 15–16 (4 Nov AM) · l11 Rule 18 (6 Nov AM) · l08 Rule 14 (7 Nov PM) · l02 Rule 7 (8 Nov AM).
Next, in this order: l01 Rules 5–6 · l04 Rule 9 · l05 Rule 10 TSS · l06 Rule 10 impede · l10 Rule 17 · l12 Rule 12.

## 3. COLREG quick-check quizzes (Drive folder `1xFIJGaqIxqYa0xZ8YSRwu8DriyyNikul`, query `title contains 's2_l'`)

`s2_lNN_qK.mp4`, about 1.2 MB, 32–37 s: question, four options, answer reveal with the rule reference. **Not used in Learn slots** (see Rotation). The six week-1 quiz slots (2, 3, 4, 6, 7, 8 Nov) were switched to lessons on 1 Nov 2026, so no quiz has been posted yet.

## Per-video checks (every time)

1. Contact sheet of 8 frames (ffmpeg `fps=8/duration,scale=270:480,tile=8x1`) and look at it.
2. Fact-check the rule shown against the COLREG text; promos only show real app features.
3. Cover: render a cover slide with `social/render.py` (one `cover` slide: kicker, title with `*accent*`, sub) and use `story_01.jpg` as `cover.jpg`. For promos whose 2-second frame already shows the hook, a frame grab is fine.
4. Length limits: Facebook Reel ≤ 90 s (longer → `facebookData.type "POST"`); YouTube Short ≤ 180 s; Story video ≤ 60 s (longer → Story uses `cover.jpg`).
5. TikTok: `videoCoverMilliseconds` at a frame where the hook is fully drawn (1000–2000).
6. Sound: every video needs music. If a file has voice but no music (gaps that drop below −50 dB), add a bed with `social/music.py` (`make_bed(duration, scene_cuts, wav, seed)`), keep it about 19 dB under the voice and dip it 6 dB more while the voice speaks, then `loudnorm=I=-14:TP=-1.5`. The crew promo needed this (31 Oct 2026); its fixed version is what Metricool now holds.
7. Quiz captions say "Answer before the reveal" / "What would you do on watch?". Never "comment A/B/C" (vote bait).
