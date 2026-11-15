# Incident videos drawn in HTML (HyperFrames)

First used for Incident Learnings 07, Exxon Valdez (15 Nov 2026). Every picture, caption and label is drawn in code on one canvas; nothing comes from the footage library. Marko asked for this style for navigation incidents.

## Files
- `index.html` — HyperFrames composition (1080×1920, 30 fps). The canvas is registered as a frame source; `assets/film.js` exposes `draw(t)`.
- `assets/lib.js` — drawing kit: sky, sea, tanker (bow-on and from above), night palette with navigation lights, outlined caption text, pills, Ocean Link mark.
- `assets/film.js` — this episode: chart (coastline, lanes, ice, reef, track), bridge view, overlays (hook, pinned question, running captions), the scenes and their timing.
- `assets/timing.js` — narration word timings (from `scripts/tts.py`); every scene is keyed to it.
- `assets/geo.js` — coastline clipped from Natural Earth 1:10m (`scripts/geo.py`).
- `quiz.html` — quiz pictures (960×600), lesson thumbnail (352×264) and cover, drawn with the same code: `quiz.html?q=1|2|3|thumb|cover`, screenshot with headless Chrome.
- `scripts/tts.py` — narration with Kokoro-82M (Apache-2.0, voice am_michael) + word timings (faster-whisper).
- `scripts/bed.py` — synthesised sound bed and the final mix (no invented alarms, radio or crash sounds).

## Build
1. `pip install kokoro-onnx soundfile faster-whisper`; download `kokoro-v1.0.onnx` and `voices-v1.0.bin` from the kokoro-onnx GitHub release.
2. `python3 scripts/tts.py <models> <voice_dir>` → `narration.wav`, `timing.json`; write `assets/timing.js` as `window.NARR=<timing.json>;`.
3. `python3 scripts/bed.py timing.json narration.wav mix_raw.wav <seconds>`, then `ffmpeg -af loudnorm=I=-14:TP=-1.5:LRA=11` → `assets/mix.wav`.
4. `npx hyperframes snapshot --at <times>` for style frames, then `npx hyperframes render --sdr -q delivery -o out.mp4` (about 7.5 min for 98 s on 2 CPUs).
5. Replace the audio with the mix (`-map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k`): the render lowers the level by about 2 dB.

A new episode changes `scripts/tts.py` (script lines), the chart data and scene list in `assets/film.js`, and the durations in `index.html`.
