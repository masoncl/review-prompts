# Output, CLI, and Transformation Review

`pahole` is both a type-inspection tool and a producer of output consumed by
people and scripts. Review a mode change across its filters, formatter, and
exit/error paths instead of checking only option parsing.

## Checklist

- [ ] Long and short option paths set the same state and reject missing or
      incompatible arguments cleanly.
- [ ] A new filter applies to the requested type classes; structs, unions,
      typedef aliases, and declarations are not conflated accidentally.
- [ ] Normal output remains on stdout (or the user-selected output stream) and
      diagnostics remain on stderr.
- [ ] Output changes preserve required ordering, indentation, and declarations;
      avoid altering unrelated modes.
- [ ] Reorganization/layout transformations recompute sizes, holes, padding,
      and cacheline summaries from the transformed representation.
- [ ] Pretty-printing an instance validates the selected type and each member
      offset before reading bytes from input.

## CLI Tests

Prefer a `tests/*.sh` test that checks help/error behavior and a minimal debug
artifact that proves the emitted type/output behavior. Use stable semantic
matches rather than asserting a full large dump unless formatting is precisely
what the change intends to guarantee.
