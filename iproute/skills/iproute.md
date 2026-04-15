---
name: iproute
description: AI-assisted code review for iproute2, the Linux networking userspace utilities.
invocation_policy: automatic
---

# iproute Skill

> **IMPORTANT NOTE**: The names **"iproute"** and **"iproute2"** are used
> entirely interchangeably throughout this project and refer to the exact same
> repository and tools. If an instruction, command, or folder refers to
> "iproute", it applies directly to "iproute2" and vice-versa. Do not get
> confused by this naming discrepancy.

## Description

AI-assisted code review for iproute2, the Linux networking userspace utilities.

## Activation

This skill activates when working in an iproute2 source tree, detected by:
- Presence of `ip/`, `tc/`, `bridge/` directories
- Presence of `include/libnetlink.h`
- Presence of `lib/libnetlink.c`

## Context Files

When this skill is active, load context from:
- `{{IPROUTE_REVIEW_PROMPTS_DIR}}/review-core.md` - Core review checklist
- `{{IPROUTE_REVIEW_PROMPTS_DIR}}/coding-style.md` - Coding style guidelines
- `{{IPROUTE_REVIEW_PROMPTS_DIR}}/json-output.md` - JSON output requirements
- `{{IPROUTE_REVIEW_PROMPTS_DIR}}/argument-parsing.md` - CLI argument parsing
- `{{IPROUTE_REVIEW_PROMPTS_DIR}}/kernel-compat.md` - Kernel compatibility
- `{{IPROUTE_REVIEW_PROMPTS_DIR}}/patch-submission.md` - Patch submission guidelines

## Key Differences from Linux Kernel

iproute2 is userspace code. Key differences:
1. No "Christmas tree" variable declaration ordering required
2. New argument parsing must use `strcmp()`, not `matches()`
3. All output must use JSON-aware `print_XXX()` helpers
4. Error messages must go to stderr to preserve JSON output
5. No kernel docbook documentation format

## Available Commands

- `/iproute-review` - Deep patch regression analysis
- `/iproute-debug` - Debug iproute2 issues
- `/iproute-verify` - Verify patch correctness
