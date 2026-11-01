#!/usr/bin/env bash
# Installs 36 reel-editing skills for Claude Code from their GitHub sources.
# Works on macOS/Linux for your own machine (~/.claude/skills) or in a repo (.claude/skills).
set -e
DEST="${1:-$HOME/.claude/skills}"
TMP="$(mktemp -d)"
mkdir -p "$DEST"
cd "$TMP"
for r in blazerior/videoediting-claude-skill jdjf39/video-creator-skills kajisho5/ffmpeg-skill \
         6missedcalls/video-editing-skill tenfoldmarc/video-edit-skill kurbaitaev/ghost-editor \
         iart-ai/tiktok-video-skills Melvynx/video-agent-skills alisadiq-ai/favstash-ai-video-editing-skills; do
  git clone -q --depth 1 "https://github.com/$r" "${r#*/}"
done
copy(){ rm -rf "${DEST:?}/${2:?}"; cp -r "$1" "$DEST/$2"; rm -rf "$DEST/$2/.git" "$DEST/$2/.claude"; echo "installed $2"; }
copy videoediting-claude-skill/skill/videoediting videoediting
for s in reel-editor watch-video motion-director motionmaxxing cinetic; do copy video-creator-skills/skills/$s $s; done
copy ffmpeg-skill ffmpeg-skill
copy video-editing-skill video-editing-bash
copy video-edit-skill video-edit-folder
copy ghost-editor ghost-editor
for s in short-form-video caption-animation lower-thirds countdown-video; do copy tiktok-video-skills/skills/$s $s; done
for s in broll clips editing insta-audit outliers publish short-editing short-translate steal studio-script studio-setup vox; do copy video-agent-skills/skills/$s melvynx-$s; done
for p in 1-research/find-ideas 2-scripting/write-script 3-editing-styles/adaptive-glass 3-editing-styles/breakout-card \
         3-editing-styles/motion-effects 3-editing-styles/paper-grid 3-editing-styles/product-motion-ads \
         3-editing-styles/text-over-footage 3-editing/edit-video 4-publish-and-learn/publish-and-analyze; do
  copy favstash-ai-video-editing-skills/skills/$p "favstash-${p##*/}"
done
rm -rf "$TMP"
echo "Done: $(ls "$DEST" | wc -l) skills in $DEST"
