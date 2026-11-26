---
name: uboot
description: Load anytime the working directory is a U-Boot tree, and always load it when you answer questions inside the U-Boot tree.  U-Boot knowledge, analysis and review protocols.  Read this anytime you're in the U-Boot tree
invocation_policy: automatic
---

## ALWAYS READ
1. Load `{{UBOOT_REVIEW_PROMPTS_DIR}}/technical-patterns.md`

You consistently skip reading additional prompt files.  These files are
MANDATORY.  This skill exists as a framework for loading additional U-Boot
prompts.

## Configuration

The review prompts directory is configured during installation:
- **UBOOT_REVIEW_PROMPTS_DIR**: {{UBOOT_REVIEW_PROMPTS_DIR}}

This variable is set by the installation script when the skill is installed.

## Capabilities

### Patch Review
When asked to review a U-Boot patch, commit, or series of commits:
1. Load `{{UBOOT_REVIEW_PROMPTS_DIR}}/review-core.md`
2. Follow the complete review protocol defined there

## Semcode Integration

When available, use semcode MCP tools for efficient code navigation:
- `find_function` / `find_type`: Get definitions
- `find_callchain`: Trace call relationships
- `find_callers` / `find_calls`: Explore call graphs
- `grep_functions`: Search function bodies
- `diff_functions`: Identify changed functions in patches

## Output

- Patch reviews produce `review-inline.txt` when regressions are found
- The output is formatted for the U-Boot mailing list (plain text, 78 char wrap)
