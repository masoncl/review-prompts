# pahole Architecture: Readers, Type Model, Writers, and `pfunct`

## Purpose and Evolution

Pahole began as a tool for analyzing Linux kernel data-structure layouts:
finding holes, padding, and candidate member orderings that can make structures
smaller or better laid out. It has evolved into a Rosetta-stone-like store and
translator for debug types. The shared DWARVES model accepts DWARF, then Compact
Type Format (CTF), and now BTF, allowing tools and writers to inspect or emit a
common representation rather than being tied to a single input format.

Review changes with both roles in mind. Layout output and reorganization must
remain faithful to ABI/debug metadata, while readers and writers must preserve
the type information needed by all supported formats—not only the immediate
format or tool that motivated a patch.

## The Overall Data Flow

```
ELF + DWARF / BTF / CTF
        │
        ▼
format-specific reader ──► `struct cus` / per-CU `struct cu`
                                 │
                                 ▼
                         tags, types, functions,
                         members, namespaces, references
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
     pahole formatters      BTF/CTF writers       pfunct
  layout/reorg/emission       and ELF output    function printer
```

Readers construct the shared DWARVES representation; writers and tools consume
it. An edit at either boundary must not make the central representation depend
on one input format or one output mode unless that is an explicit contract.

## Readers and Writers

`struct debug_fmt_ops` provides format-specific initialization, loading,
allocation/free hooks, declaration metadata access, and CU teardown. The reader
must build tags with the invariants expected by general helpers. In particular,
it must set the owning CU, preserve source-format facts that downstream code
needs, and not expose an incompletely initialized tag.

Writers include textual formatting/emission and BTF encoding. They must consume
the shared model without assuming the input was DWARF: BTF and CTF can lack
facts that DWARF carries, such as alignment or declaration metadata. Keep a
format-specific conditional at the boundary where the fact is known; do not
invent missing metadata in a generic tag helper.

Review shared reader/writer changes for a round trip where relevant:

- Does the reader preserve enough identity, layout, and declaration data?
- Does the writer maintain required ordering and reject unsupported state?
- Is a partial load or encode failure distinguishable from a successful empty
  result?
- Are `conf_load` feature flags honored consistently in both paths?

## Representation of Structure Layout

`struct class_member` carries both raw layout information and derived layout
state: byte/bit offsets and sizes, bitfield placement, byte/bit holes, static
membership, accessibility, virtuality, and optional alignment. `struct type`
holds aggregate size, member counts, alignment/natural alignment, declaration
state, and aggregate-level padding/packing-related state through its class view.

Treat raw debug information and derived annotations differently:

- Preserve raw offsets, sizes, and `has_bit_offset` from the reader.
- Recompute holes, padding, natural alignment, and inferred packed attributes
  after moving, adding, removing, or resizing members.
- Account for a negative `hole`: inherited-class layout may deliberately reuse
  ancestor padding.
- Keep byte and bit arithmetic separate. A bitfield's storage-unit byte size is
  not its bit size, and a zero-width/terminal bitfield needs its own boundary
  case.

## Formatting Hints Are Output Policy

`struct conf_fprintf` is a set of presentation hints for the shared formatter:
type expansion, pointer expansion, offsets, indentation, cachelines, comments,
padding/packed/aligned annotations, declaration information, parameter names,
and pretty-print ranges. They should affect presentation, not mutate the base
type graph or become an accidental format-conversion policy.

When adding a hint, review its default, option wiring, propagation through
recursive calls, and interactions with `expand_types`, type emission, and
formats lacking alignment information. Verify that one output mode does not
leak its configuration into a later invocation.

## `pfunct`: Function Information Printer

`pfunct` uses the same loaders and `conf_load`/`conf_fprintf` infrastructure to
find and print functions, prototypes, parameters, inline expansions, variables,
and selected statistics. It therefore provides a useful independent consumer
of function tags and formatter logic—not merely a small CLI wrapper.

For changes to function DIEs, prototypes, parameter layout, inline metadata,
or `dwarves_fprintf.c`, test the relevant `pfunct` mode as well as `pahole`:

- ordinary and `--all` function listing;
- DWARF and BTF input where both are supported;
- `--no_parm_names`, prototype/verbose output, and type expansion if touched;
- address/name/class filtering and split-BTF base handling when applicable.

Do not collapse distinct declarations merely because their display names match:
`pfunct` tracks function tags with their CUs, and duplicate/inlined definitions
need the source/identity context retained by the loader.

## `fullcircle`: Compile-and-Compare Round Trip

`fullcircle` checks whether type information can make a useful round trip. For
a single-compilation-unit object with debug information, it runs
`pfunct --compile` to emit compilable C declarations, compiles that generated
C with debug information (reusing compiler flags inferred from `DW_AT_producer`
when possible), then invokes `codiff -q -s` to compare the original and
regenerated objects' type information.

It is a high-value integration consumer of the loader, function/type emitter,
compiler-facing C syntax, and `codiff`; it is not a universal semantic proof.
It intentionally returns early for multi-CU input and its producer-flag
inference is compiler/output-format dependent. When changing `pfunct --compile`,
`dwarves_emit`, type declarations, or `codiff` comparison behavior, use a
single-CU fixture with `fullcircle` where its constraints apply, plus focused
tests for the particular type property. Review shell changes for temporary-file
cleanup and for failures from `pfunct`, the compiler, and `codiff` being
propagated rather than masked.
