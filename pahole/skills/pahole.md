---
name: pahole
description: AI-assisted code review for pahole and the dwarves debug-information tools.
invocation_policy: automatic
---

# pahole Skill

## Activation

Use this skill in a pahole/dwarves source tree, identifiable by `dwarves.c`,
`dwarf_loader.c`, `btf_encoder.c`, and `CMakeLists.txt` at the repository root.

## Required Context

Start every review by loading:

- `{{PAHOLE_REVIEW_PROMPTS_DIR}}/review-core.md`
- `{{PAHOLE_REVIEW_PROMPTS_DIR}}/technical-patterns.md`

Then load focused context based on the patch:

- `architecture.md` for readers/writers, the common type/layout model,
  `conf_fprintf` presentation hints, or `pfunct`.
- `dwarf.md` for DWARF loading and common tag/CU graph changes.
- `btf.md` for BTF, ELF output, split BTF, distilled base, or `lib/bpf/`.
- `output-and-cli.md` for `pahole.c`, emitters, reorganizers, and output.
- `build-and-test.md` for CMake, CI, test runner, or test scripts.
- `false-positive-guide.md` before reporting uncertain findings.

## Core Rules

1. Treat a tag ID as scoped to its owning `struct cu`.
2. Validate input-derived debug metadata before using it as an offset, count,
   ID, or allocation size.
3. Preserve BTF type ordering/identity unless the patch proves a compatible
   migration for consumers such as split BTF and deduplication.
4. Require focused semantic tests for behavior changes; compilation alone does
   not validate a debug-information transformation.
5. Treat `lib/bpf/` as an embedded submodule synchronized from upstream.

## Commands

- `/pahole-review` for patch analysis.
- `/pahole-verify` for build/test verification.
- `/pahole-debug` for failure investigation.
