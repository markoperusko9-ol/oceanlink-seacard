Post media for Ocean Link social posts (fetched by Metricool when scheduling).

news/ — 48 topic photos for Ocean Link news posts (6 each: safety, incident, regulation,
crew-welfare, careers, industry, technology, environment; <topic>-<1..6>.jpg, 1280x720).
Stills cut from Marko's own ship clips and from the free stock clips in D:\Vessel Videos\Stock.
catalog.json describes each photo; Claude picks the best match for each story (prompt: ocean-link-bubble prompts/News_brief_body_claude_v2.json).

news/ai/ — AI illustrations for single news stories (<story-slug>.jpg, 1280x720, tagged
"AI illustration" in the corner). Made by Marko's ChatGPT agent from prompts the
"Ocean Link news images" scheduled task writes to Drive (News images/prompts → images),
then cropped, tagged and published by scripts/news_ai_images.py. index.json lists
source_url → image; Bubble uses it when it creates a news post, otherwise the post keeps
the library photo from news/.
