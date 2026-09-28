# DWARF and Common Type-Graph Review

## Loader Responsibilities

The DWARF loader translates DIEs and attributes into pahole's per-CU tag graph.
Review changes for both the immediate DIE and references that may be resolved
later. A valid DIE can be a declaration rather than a definition, omit an
optional attribute, refer through `DW_AT_specification`/`DW_AT_abstract_origin`,
or point into alternate/split debug information.

## Checklist

- [ ] Check each `dwarf_*` result and distinguish “attribute absent” from an
      API/error result.
- [ ] Preserve reference ownership: a DIE reference must resolve in the correct
      CU or alternate-debug context.
- [ ] Do not assume a name, byte size, location, declaration file, or child
      DIE exists for every valid tag.
- [ ] Handle declarations/forward declarations without treating them as full
      aggregates.
- [ ] Keep DWARF version and architecture-specific ABI cases covered by a
      minimal fixture where behavior differs.

## Layout-Sensitive Types

For members and parameters, review byte offset, bit offset, bit size, alignment,
and register/stack assignment separately. Do not infer one from another. In
particular, a language ABI can leave register holes or align aggregates and
floating-point values differently; test the affected target ABI explicitly.

## Common Traps

- Resolving a referenced type in the current CU after the source established
  that it belongs to alternate/split debug info.
- Losing a declaration-vs-definition distinction and emitting duplicate or
  incomplete types.
- Recoding bitfields without proving that endianness, DWARF version, and
  zero-width behavior are retained.
- Changing a hash/cache key without considering anonymous types, repeated names,
  and type qualifiers.

## CTF Loader: Legacy Compatibility Surface

Treat `ctf_loader.c` as legacy support, not a dormant or frozen code path.
Binutils continues to evolve its CTF production and handling, so changes in
binutils can expose new encodings, attributes, ordering, or edge cases that
pahole's loader must understand. When a CTF issue is reported, compare the
producing binutils behavior with the loader's assumptions before “fixing” the
shared type model.

Keep CTF-specific interpretation at the CTF boundary and preserve the common
CU/tag invariants used by other readers. Add a minimal CTF regression artifact
where practical; do not use a DWARF-only test as evidence that a CTF loader
update is correct. Changes to shared reader APIs should explicitly consider the
legacy CTF path even when the primary motivation is DWARF or BTF.
