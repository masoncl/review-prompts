- `decode_file()` in `tools/objtool/check.c`: does all the reading; there is no
  decode_sections() in this tree.
- `include/linux/annotate.h`: defines `ASM_ANNOTATE()`, `ASM_ANNOTATE_LABEL()`,
  the asm `ANNOTATE` macro and every generic `ANNOTATE_` macro; x86
  `ANNOTATE_UNRET_SAFE` is an alias in `arch/x86/include/asm/nospec-branch.h`.
- `include/linux/objtool.h`: includes `include/linux/annotate.h` and defines
  `UNWIND_HINT`, `STACK_FRAME_NON_STANDARD`, `STACK_FRAME_NON_STANDARD_FP`,
  `ASM_REACHABLE` and `VALIDATE_UNRET_BEGIN`.
- `read_unwind_hints()`: runs after `read_annotate()` with `__annotate_early()`
  and with `__annotate_ifc()`, and before `read_annotate()` with
  `__annotate_late()`.
- `read_unwind_hints()` tests `insn->noendbr`, which only `__annotate_early()`
  sets; moving `ANNOTYPE_NOENDBR` to `__annotate_late()` breaks that test.
- `.discard.annotate_data`: a second annotation section with the same 8-byte
  entry layout and its own type numbers; `ANNOTATE_DATA_SPECIAL` writes it.
