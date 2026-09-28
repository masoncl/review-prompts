# pahole Patch Review Protocol

## Pre-Review Setup

Before reviewing, load `technical-patterns.md`. Identify whether the change is
in a reader/writer boundary, the common DWARVES model/layout representation,
formatter hints, `pfunct`, an encoder, output/CLI code, tests, CMake, or the
embedded `lib/bpf` submodule; then load the matching focused guide.

Read the whole changed call path. In pahole, a small change to a tag field,
iteration order, or error return can affect every later printer or encoder.

## Review Checklist

### Type Graph and Ownership

- [ ] IDs are resolved using the owning `struct cu`; pointers do not outlive
      the CU/container that owns them.
- [ ] New tags are initialized fully before insertion or exposure to walkers.
- [ ] Iteration is safe if the loop can add, remove, or free entries.
- [ ] Typedef, pointer, array, qualifier, and forward-declaration paths are
      handled deliberately rather than assumed to be concrete structures.
- [ ] Recursive types and anonymous types cannot cause unbounded recursion or
      accidental type merging.

### Reader/Writer Boundaries and Layout

- [ ] Format-specific readers preserve facts required by generic consumers, but
      generic code does not assume metadata unavailable in another format.
- [ ] `conf_load` controls are applied at the intended loading/encoding point;
      a configuration choice does not silently mutate unrelated output paths.
- [ ] Changes to `struct class_member` or aggregate layout distinguish raw
      offsets from derived holes, padding, alignment, and inferred attributes.
- [ ] Any layout mutation recalculates all derived state before formatting,
      reorganization, or encoding consumes it.
- [ ] `conf_fprintf` changes are presentation policy and are propagated through
      recursive formatting without leaking between invocations.
- [ ] Function/prototype changes are checked through `pfunct` as an additional
      consumer of the common loader and formatter paths.
- [ ] Changes to compilable type emission or `codiff` use `fullcircle` on an
      applicable single-CU fixture, in addition to focused semantic tests.

### Debug Information Semantics

- [ ] DWARF attributes are interpreted with their form, version, and possible
      absence in mind; references, declarations, and specification/origin
      relationships are not confused.
- [ ] BTF kind, vlen, type ID, string offset, and endianness semantics are
      retained through load/transform/encode paths.
- [ ] Bit offsets, bitfield sizes, alignment, flexible arrays, and zero-sized
      or incomplete types are preserved rather than normalized accidentally.
- [ ] Unsupported input produces an explicit, useful error or documented skip;
      malformed input never leads to an out-of-bounds read or partial success.

### Encoder and Output Correctness

- [ ] BTF emission checks every libbpf/ELF return value and reports the error.
- [ ] Type ordering/deduplication changes are reviewed for determinism and
      compatibility with split BTF and distilled-base workflows.
- [ ] Optional BTF features use runtime libbpf capability checks (including
      weak declarations), accurately report availability, and do not introduce
      target-kernel-version dependencies.
- [ ] `pahole` output remains parseable and stable where scripts/tests rely on
      it; diagnostics go to stderr and normal output to its selected stream.
- [ ] CLI filters affect all intended type kinds, including structs versus
      unions where applicable, without changing unrelated modes.

### C Safety and Error Handling

- [ ] Allocation sizes cannot overflow and allocations are checked before use.
- [ ] File descriptors, ELF/DWARF/BTF handles, buffers, and temporary tags are
      released on every failure path.
- [ ] Signed/unsigned conversions and narrowing cannot corrupt offsets, sizes,
      IDs, or array indexes.
- [ ] Input-derived counts and offsets are bounds checked before dereference.
- [ ] `gobuffer` users check reservation failures, retain offsets rather than
      realloc-invalidated pointers, and release the buffer on all exit paths.
- [ ] `rbtree` users preserve comparator ordering/equality, link then balance
      insertions, erase before freeing/reusing a node, and retain required
      mutation locking.

### Build and Tests

- [ ] A functional change adds or updates a focused test under `tests/`.
- [ ] The test compiles a minimal fixture with the needed language, compiler,
      architecture, and DWARF/BTF feature.
- [ ] The test checks semantic output, not fragile incidental formatting, unless
      output formatting itself is the contract.
- [ ] CMake changes work for both embedded and system libbpf configurations.
- [ ] Changes under `lib/bpf/` are clearly identified as a libbpf sync and do
      not mix unrelated local pahole edits.

### Commit Quality

- [ ] Subject has the customary component prefix, for example
      `dwarf_loader: ...`, `btf_encoder: ...`, `tests: ...`, or `pahole: ...`.
- [ ] Body explains the affected input case and user-visible/encoded result.
- [ ] Add `Fixes:` when correcting a known commit, and `Signed-off-by:` where
      the project workflow requires it.

## Conditional Context Loading

| Patch touches | Load file |
|---|---|
| Readers/writers, common layout model, `conf_fprintf`, `pfunct`, `fullcircle` | `architecture.md` |
| `dwarves.[ch]`, `dwarf_loader.c`, or legacy CTF loading | `dwarf.md` |
| `btf_*.c`, BTF output, `lib/bpf/` submodule | `btf.md` |
| `pahole.c`, emit/reorganize/printing, options | `output-and-cli.md` |
| CMake, test runner, fixtures, CI | `build-and-test.md` |
| Existing code seems suspicious | `false-positive-guide.md` |

## Review Output

Report actionable findings with the affected input shape, execution path, and
observable result. Do not call a theoretical issue a bug unless the changed
code reaches it. Email-style feedback is appropriate for `dwarves@vger.kernel.org`.
