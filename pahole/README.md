# pahole Review Documentation

Review guidance for patches to pahole (the dwarves project), for human
reviewers and AI coding assistants.

Pahole grew from a Linux-kernel structure-layout analyzer into a shared debug
type store and translator for DWARF, CTF, and BTF. Reviews therefore need to
protect both layout-analysis semantics and cross-format type fidelity.

## Quick Start

1. Always load `review-core.md` and `technical-patterns.md`.
2. Load the focused guide for the changed area.
3. Check the patch with a representative input artifact, not just compilation.

| Patch touches | Load |
|---|---|
| Shared readers/writers, type/layout model, formatter hints, or `pfunct` | `architecture.md` |
| DWARF loading or the in-memory type graph | `dwarf.md` |
| BTF loading, encoding, deduplication, split or distilled BTF | `btf.md` |
| CLI display, filters, reorganizers, or pretty-printing | `output-and-cli.md` |
| CMake, dependencies, test scripts, or CI | `build-and-test.md` |
| An uncertain finding or legacy pattern | `false-positive-guide.md` |

## Repository Map

- `dwarves.[ch]`: central compilation-unit/type representation and common APIs.
- `architecture.md`: data flow from debug-format readers through the shared
  model to writers, layout representation/hints, and the `pfunct` consumer.
- `dwarf_loader.c`, `ctf_loader.c`, `btf_loader.c`: readers that populate it.
- `btf_encoder.c`: BTF encoding and related ELF output paths.
- `dwarves_fprintf.c`, `dwarves_emit.c`, `dwarves_reorganize.c`: presentation and
  transformation helpers.
- `gobuffer.[ch]`: append-only byte storage for serialized variable-length
  records; offsets survive growth, direct pointers do not.
- `rbtree.[ch]`: Linux-derived intrusive ordered indexes used for function
  address lookup, string membership, and sorted/deduplicated structures.
- `pahole.c` and small utility programs: command-line front ends.
- `fullcircle`: uses `pfunct --compile`, recompilation, and `codiff` to check a
  single-CU debug-type round trip.
- `tests/*.sh`: regression suite; many tests compile purpose-built fixtures.
- `lib/bpf/`: embedded libbpf submodule. Treat updates as upstream
  synchronization work, not ordinary local edits.

## Critical Review Themes

1. A tag ID is scoped to its compilation unit; do not retain or resolve it
   through the wrong `struct cu`.
2. Preserve ordering and identity where a consumer relies on them, especially
   for BTF types, declaration/type tags, functions, and split BTF.
3. Do not silently turn unsupported or malformed debug metadata into a valid
   but different type graph.
4. Test both successful output and failure/absence cases with an artifact that
   has the relevant DWARF or BTF feature.
5. Keep generated build output and test artifacts out of patches.

## Commands

- `/pahole-review`: deep review of a patch or top commit.
- `/pahole-verify`: build and focused test verification plan.
- `/pahole-debug`: investigate a loader, encoder, output, or test failure.
