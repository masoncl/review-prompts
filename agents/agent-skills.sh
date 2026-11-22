#!/bin/bash
#
# Agent setup script for the generic Agent Skills standard
# (https://agentskills.io), supported by agents such as pi.dev, goose,
# and other ~/.agents/skills compatible tools.
#
# Sourced by setup.sh to configure where skills and slash commands are
# installed. Exports the install paths and skill filename expected by the
# standard; additional per-agent setup steps (if any) can be added here.
#
# Compatible agents discover global skills as ~/.agents/skills/<name>/SKILL.md.
# Because the standard does not define a separate slash-command directory,
# slash commands are installed as skills too via COMMANDS_AS_SKILLS.  How
# they are invoked depends on the agent (e.g. /skill:<name> in pi.dev,
# /<name> in goose).

export SKILL_BASE_DIR="$HOME/.agents/skills"
export COMMANDS_DIR="$HOME/.agents/skills"
export SKILL_FILE_NAME="SKILL.md"
export COMMANDS_AS_SKILLS=1
export AGENT_POST_INSTALL_NOTE="Commands were installed as skills in $COMMANDS_DIR; invoke them using your agent's skill syntax (e.g. /skill:<name> in pi.dev)."
