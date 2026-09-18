#!/bin/bash
#
# Agent setup script for Muse Code (muse).
#
# Sourced by setup.sh to configure where skills and slash commands are
# installed. Exports the install paths and skill filename expected by the
# agent; additional per-agent setup steps (if any) can be added here.
#
# muse discovers personal skills as $CONFIG_DIR/skills/<name>/SKILL.md,
# where $CONFIG_DIR is $XDG_CONFIG_HOME/muse, else $HOME/.config/muse
# (verify with 'muse skills list').  It also reads ~/.claude/skills as an
# import-only source, but installs go to the native root so the managed
# skills store sees them.  muse has no standalone slash-command files:
# every installed skill is exposed as a slash command, so the commands
# are installed as skills too via COMMANDS_AS_SKILLS.
#

_MUSE_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/muse"

export SKILL_BASE_DIR="$_MUSE_CONFIG_DIR/skills"
export COMMANDS_DIR="$_MUSE_CONFIG_DIR/skills"
export SKILL_FILE_NAME="SKILL.md"
export COMMANDS_AS_SKILLS=1
