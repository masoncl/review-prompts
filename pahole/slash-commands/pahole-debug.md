# /pahole-debug - pahole Debug

Investigate a pahole failure with the smallest reproducible debug-information
artifact.

1. Identify whether failure occurs while loading DWARF/BTF, transforming the
   type graph, encoding BTF, or formatting CLI output.
2. Load the matching focused guide and trace the relevant CU, tag ID, and type
   wrappers through the path.
3. Reproduce with a minimal source fixture or the smallest supplied binary.
4. Inspect both stdout and stderr, and preserve failing test artifacts when
   available under `/tmp/pahole-tests/`.
5. Propose a fix plus a regression test that validates the semantic result.

For BTF failures, inspect type ordering, IDs, strings, and section/symbol
metadata. For DWARF failures, inspect optional attributes, DIE references,
declarations, offsets, and target ABI assumptions before changing shared logic.
