# iproute2 Skill

## Description

AI-assisted code review for iproute2, the Linux networking userspace utilities.

## Activation

This skill activates when working in an iproute2 source tree, detected by:
- Presence of `ip/`, `tc/`, `bridge/` directories
- Presence of `include/libnetlink.h`
- Presence of `lib/libnetlink.c`

## Context Files

When this skill is active, load context from:
- `review-core.md` - Core review checklist
- `coding-style.md` - Coding style guidelines
- `json-output.md` - JSON output requirements
- `argument-parsing.md` - CLI argument parsing
- `kernel-compat.md` - Kernel compatibility
- `patch-submission.md` - Patch submission guidelines

## Key Differences from Linux Kernel

iproute2 is userspace code. Key differences:
1. No "Christmas tree" variable declaration ordering required
2. New argument parsing must use `strcmp()`, not `matches()`
3. All output must use JSON-aware `print_XXX()` helpers
4. Error messages must go to stderr to preserve JSON output
5. No kernel docbook documentation format

## Available Commands

- `/ireview` - Deep patch regression analysis
- `/idebug` - Debug iproute2 issues
- `/iverify` - Verify patch correctness
