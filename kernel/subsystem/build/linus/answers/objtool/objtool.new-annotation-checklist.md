- Unknown type in `.discard.annotate_insn`: `__annotate_late()` reports
  "Unknown annotation type: %d" with `ERROR_INSN()` and returns -1; objtool
  exits non-zero even without `--werror`.
- `__annotate_early()` and `__annotate_ifc()`: ignore types they do not
  handle, so a type handled there still needs a `case` in `__annotate_late()`.
- Unknown type in `.discard.annotate_data`: `create_fake_symbols()` in
  `tools/objtool/klp-diff.c` skips the entry silently.
- Unknown unwind hint type: `read_unwind_hints()` does not reject it; it
  copies `hint->type` to `cfi.type`.
- `init_orc_entry()`: the only place that reports "unknown unwind hint type",
  and it runs only under `--orc`; x86 and loongarch each have one, in
  `tools/objtool/arch/x86/orc.c` and `tools/objtool/arch/loongarch/orc.c`.
- `UNWIND_HINT_TYPE_FUNC`, `UNWIND_HINT_TYPE_SAVE`, `UNWIND_HINT_TYPE_RESTORE`:
  have no `ORC_TYPE_` value; `read_unwind_hints()` consumes them, so they never
  reach `init_orc_entry()`.
- Change to `struct unwind_hint`: `read_unwind_hints()` fails with
  "struct unwind_hint size mismatch" when the section size is not a multiple
  of the size in the copy.
- `tools/include/linux/objtool_types.h`: the only copy of the type header;
  `include/linux/objtool.h` and `include/linux/annotate.h` have no copy under
  `tools/`.
- `orc_types.h` copies: `tools/arch/x86/include/asm/orc_types.h` and
  `tools/arch/loongarch/include/asm/orc_types.h`.
- `tools/objtool/sync-check.sh`: run as the first recipe line of the
  `$(OBJTOOL_IN)` rule in `tools/objtool/Makefile`.
