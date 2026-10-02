- `ASM_REACHABLE`: writes `.discard.reachable`; no file under `tools/objtool`
  names that section, and the macro has no users.
- `UNWIND_HINT`: besides `.discard.unwind_hints` it writes
  `.discard.annotate_data` through `ANNOTATE_DATA_SPECIAL`; `check()` does not
  read that section.
- `.discard.annotate_data`: read only by `create_fake_symbols()` in
  `tools/objtool/klp-diff.c`, which `tools/objtool/Build` compiles only with
  `BUILD_KLP`.
