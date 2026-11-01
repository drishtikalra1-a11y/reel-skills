#!/usr/bin/env bash
# Environment setup script for Claude Code cloud sessions.
# Installs the reel-skills into ~/.claude/skills so they load in EVERY session,
# whatever repository the session was started from.
set -e
SRC=/tmp/reel-skills-src
rm -rf "$SRC"
git clone -q --depth 1 https://github.com/drishtikalra1-a11y/reel-skills "$SRC"
mkdir -p ~/.claude/skills
cp -r "$SRC"/.claude/skills/* ~/.claude/skills/
rm -rf "$SRC"
echo "reel-skills: $(ls ~/.claude/skills | wc -l) skills installed"
