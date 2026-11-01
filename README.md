# reel-skills

Claude Code skills for editing Instagram Reels, TikToks and YouTube Shorts.
52 skills: 50 collected from nineteen open-source GitHub repositories plus two custom skills, history-explainer and upsc-trend-brief, installed under `.claude/skills/`.

## Use in Claude Code cloud sessions
Start a session from this repository. The skills load automatically.

## Use on your own computer
Copy the skills into your user skills folder once:

```bash
git clone https://github.com/drishtikalra1-a11y/reel-skills
cp -r reel-skills/.claude/skills/* ~/.claude/skills/
```

Or reinstall fresh from the upstream repos:

```bash
bash install-reel-skills.sh
```

Most editing skills need `ffmpeg`; several also need Node 22+, Python 3.10+ or `uv`.

## What is included
| Area | Skills |
|---|---|
| Cut and caption footage | videoediting, reel-editor, ffmpeg-skill, video-editing-bash, video-edit-folder, ghost-editor, favstash-edit-video, melvynx-short-editing, melvynx-clips |
| Captions and overlays | caption-animation, lower-thirds, countdown-video |
| Visual styles | favstash-adaptive-glass, favstash-paper-grid, favstash-breakout-card, favstash-motion-effects, favstash-product-motion-ads, favstash-text-over-footage |
| Ideas and scripts | short-form-video, favstash-find-ideas, favstash-write-script, melvynx-studio-script, melvynx-outliers, melvynx-steal, melvynx-insta-audit |
| Reference analysis | watch-video |
| History explainers | **history-explainer** (custom: Study IQ style, real archival images, Ken Burns, maps, timelines, Hindi lower-thirds), vox-explainer, explainer-video, data-story, video-explainer, reference-to-motion, animated-chart, reel-export |
| Added later | vertical-video-editing (style presets, b-roll, transitions), talking-head-reel, reel-studio (AI B-roll + Remotion captions), ultimate-video-editor (colour grading, animated captions), app-promo-reel and product-film (beat-synced cuts), remotion-motion-graphics |
| Motion graphics | motion-director, motionmaxxing, cinetic, melvynx-vox |
| Studio and publishing | melvynx-studio-setup, melvynx-editing, melvynx-broll, melvynx-short-translate, melvynx-publish, favstash-publish-and-analyze |

## Sources
- https://github.com/blazerior/videoediting-claude-skill
- https://github.com/jdjf39/video-creator-skills
- https://github.com/kajisho5/ffmpeg-skill
- https://github.com/6missedcalls/video-editing-skill
- https://github.com/tenfoldmarc/video-edit-skill
- https://github.com/kurbaitaev/ghost-editor
- https://github.com/iart-ai/tiktok-video-skills
- https://github.com/Melvynx/video-agent-skills
- https://github.com/alisadiq-ai/favstash-ai-video-editing-skills
- https://github.com/nopefallacy/vertical-video-editing-skills
- https://github.com/mariagorskikh/talking-head-reel
- https://github.com/harper-carroll/reel-studio-skill
- https://github.com/Rajbharti06/Ultimate-Video-Editing-Skills
- https://github.com/hamen/app-promo-reel
- https://github.com/Rieranthony/product-film-skill
- https://github.com/haidrrrry/claude-remotion-skill
- https://github.com/charlie947/motion-graphics-skills
- https://github.com/Neelshah1810/Claude-Video-Skills
- https://github.com/runesleo/claude-video-kit

Each skill keeps its original license; see the LICENSE file inside each folder where present.

## Load in every cloud session automatically
In claude.ai/code open the cloud environment menu in the session title bar, choose Edit,
and paste this under Setup script:

```bash
curl -fsSL https://raw.githubusercontent.com/drishtikalra1-a11y/reel-skills/main/setup-cloud.sh | bash
```

This needs the repository to be public, or added under Repositories in that same environment settings page.
