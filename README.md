# Review Prompts for AI-Assisted Code Review

AI-assisted code review prompts for Linux kernel, systemd, iproute,
nfs-utils, and pahole development. Works with Claude Code and other AI tools.

## Quick Start

### Install Prompts

```bash
./setup.sh <agent> <project>
```

Where `<agent>` is one of available agents and `<project>` is one of available
projects that are explicitly stated in the usage message when the script is
executed with `-h|--help` option.

## Available Commands

| Project | Review | Debug | Verify |
|---------|--------|-------|--------|
| Kernel | `/kreview` | `/kdebug` | `/kverify` |
| systemd | `/systemd-review` | `/systemd-debug` | `/systemd-verify` |
| iproute | `/iproute-review` | `/iproute-debug` | `/iproute-verify` |
| nfs-utils | `/nfs-utils-review` | `/nfs-utils-debug` | `/nfs-utils-verify` |
| pahole | `/pahole-review` | `/pahole-debug` | `/pahole-verify` |

The kernel has four more commands: `/kseries`, `/korcreview`, `/kslop` and
`/cocci`. See [kernel/README.md](kernel/README.md).

## Project Documentation

* [Kernel Review Prompts](kernel/README.md) - Linux kernel specific patterns and protocols
* [systemd Review Prompts](systemd/README.md) - systemd specific patterns and protocols
* [iproute Review Prompts](iproute/README.md) - iproute specific patterns and protocols
* [nfs-utils Review Prompts](nfs-utils/README.md) - nfs-utils specific patterns and protocols
* [pahole Review Prompts](pahole/README.md) - pahole specific patterns and protocols

## How It Works

Each project has:
- **Skill file** - Automatically loads context when working in the project tree
- **Slash commands** - Quick access to review, debug, and verify workflows
- **Subsystem files** - Domain-specific knowledge loaded on demand. For the
  kernel these are guides built from a kernel tree, which a review searches
  through an index

The skills detect your working directory and load appropriate context:
- In a kernel tree: kernel skill loads automatically
- In a systemd tree: systemd skill loads automatically
- In an iproute tree: iproute skill loads automatically
- In an nfs-utils tree: nfs-utils skill loads automatically
- In a pahole tree: pahole skill loads automatically

## Structure

```
review-prompts/
├── setup.sh                   # Installs the skill and slash commands of one project for one agent
├── agents/                    # Where each agent keeps skills and commands, for setup.sh
├── AGENTS.md                  # Notes for an agent that works on this repository
│
├── kernel/                    # Linux kernel prompts
│   ├── skills/               # Skill template
│   ├── slash-commands/       # /kreview, /kseries, /korcreview, /kdebug, /kverify, /kslop, /cocci
│   ├── agent/                # Prompts for a review split across several agents, and for building the guides
│   ├── scripts/              # Scripts that run reviews and build the subsystem guides
│   ├── docs/                 # How the guides are built, and how to write prompts here
│   ├── examples/             # Sample output
│   ├── subsystem/            # The questions the subsystem guides are built from, and build/linus/ with the built guides and their index
│   └── *.md                  # Protocol files
│
├── systemd/                   # systemd prompts
│   ├── skills/               # Skill template
│   ├── slash-commands/       # /systemd-review, /systemd-debug, /systemd-verify
│   ├── patterns/             # Bug pattern documentation
│   └── *.md                  # Subsystem and protocol files
│
├── iproute/                  # iproute prompts
│   ├── skills/               # Skill template
│   ├── slash-commands/       # /iproute-review, /iproute-debug, /iproute-verify
│   └── *.md                  # Subsystem and protocol files
│
├── nfs-utils/                # nfs-utils prompts
│   ├── skills/               # Skill template
│   ├── slash-commands/       # /nfs-utils-review, -debug, -verify
│   ├── subsystem/            # Per-component guides + trigger index
│   └── *.md                  # Core protocol files
│
├── pahole/                   # pahole prompts
│   ├── skills/               # Skill template
│   ├── slash-commands/       # /pahole-review, /pahole-debug, /pahole-verify
│   └── *.md                  # Subsystem and protocol files
│
└── README.md                  # This file
```

## Semcode Integration

These prompts work best with [semcode](https://github.com/facebookexperimental/semcode)
for fast code navigation and semantic search.

## License

See [LICENSE](LICENSE) for license information.
