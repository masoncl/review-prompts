# U-Boot Review Prompts for AI-Assisted Code Review

AI-assisted code review prompts optimized for the U-Boot codebase.

## Installation

Run the setup script from the root of this repository to install the skill and slash commands:

```bash
./setup.sh <agent> <project>
```

Where `<agent>` is one of available agents and `<project>` is one of available
projects that are explicitly stated in the usage message when the script is
executed with `-h|--help` option.

This will install:
- The `U-Boot` skill to the agent's specific skill directory
- Slash commands to the agent's command directory

## Usage

The U-Boot skill loads automatically when working in a U-Boot tree.

### Slash Commands

- `/ureview` - Review commits for regressions and issues
- `/useries` - Review an entire patch series (git range) commit-by-commit
- `/uverify` - Verify findings against false positive patterns

### Manual Loading

If the skill doesn't auto-load, you can manually trigger it by asking
about U-Boot specific topics or requesting a review.

## File Structure

```
review-prompts/
├── README.md                 # This file
├── technical-patterns.md     # Core patterns (always loaded)
├── review-core.md            # Main review protocol
├── skills/                   # Skill template
├── slash-commands/           # Slash command definitions
├── false-positive-guide.md   # False positive checklist
├── lore-thread.md            # Process lore threads
├── callstack.md              # Regressions within the callstack
├── missing-fixes-tag.md      # Missing Fixes: tags rules
└── inline-template.md        # Report template
```
