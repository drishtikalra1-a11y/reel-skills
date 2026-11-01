# reel-skills

Claude Code skills for editing Instagram Reels, TikToks and YouTube Shorts.
36 skills collected from nine open-source GitHub repositories, installed under `.claude/skills/`.

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

Each skill keeps its original license; see the LICENSE file inside each folder where present.
