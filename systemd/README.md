# systemd Review Prompts for AI-Assisted Code Review

AI-assisted code review prompts optimized for the systemd codebase.

## Installation

Run the setup script from the root of this repository to install the skill and slash commands:

```bash
./setup.sh <agent> <project>
```

Where `<agent>` is one of available agents and `<project>` is one of available
projects that are explicitly stated in the usage message when the script is
executed with `-h|--help` option.

This will install:
- The `systemd` skill to the agent's specific skill directory
- Slash commands to the agent's command directory

## Usage

The systemd skill loads automatically when working in a systemd tree.

### Slash Commands

- `/systemd-review` - Review commits for regressions and issues
- `/systemd-debug` - Debug crashes, assertions, and stack traces
- `/systemd-verify` - Verify findings against false positive patterns

### Manual Loading

If the skill doesn't auto-load, you can manually trigger it by asking
about systemd-specific topics or requesting a review.

## File Structure

```
review-prompts/
├── README.md                 # This file
├── technical-patterns.md     # Core patterns (always loaded)
├── review-core.md            # Main review protocol
├── debugging.md              # Debugging protocol
├── namespace.md              # Mount namespace patterns
├── core.md                   # PID1/service manager patterns
├── cleanup.md                # Cleanup attribute patterns
├── nspawn.md                 # Container patterns
├── dbus.md                   # D-Bus patterns
├── patterns/                 # Detailed pattern explanations
├── skills/                   # Skill template
├── slash-commands/           # Slash command definitions
├── false-positive-guide.md   # False positive checklist
└── inline-template.md        # Report template
```

## Integration with Kernel Review-Prompts

This setup is designed to coexist with the kernel and iproute review-prompts.
The `./setup.sh <agent> <project>` command will install the prompts for a specific project.

Each skill auto-loads based on the working directory context.
