| Type | Macro | What objtool does |
|---|---|---|
| `ANNOTYPE_NOENDBR` (1) | `ANNOTATE_NOENDBR`, `ANNOTATE_NOENDBR_SYM()` | sets `insn->noendbr`; `validate_ibt()` accepts references to it; also passes the ENDBR test in `read_unwind_hints()` |
| `ANNOTYPE_RETPOLINE_SAFE` (2) | `ANNOTATE_RETPOLINE_SAFE`; x86 `ANNOTATE_UNRET_SAFE`, `VALIDATE_UNRET_END` | error unless the instruction is an indirect jump, indirect call, return or NOP; `validate_retpoline()` and `validate_sls()` skip it; on a NOP it ends the `validate_unret()` walk |
| `ANNOTYPE_INSTR_BEGIN` (3) | `ANNOTATE_INSTR_BEGIN()`, from `instrumentation_begin()` | `insn->instr++` |
| `ANNOTYPE_INSTR_END` (4) | `ANNOTATE_INSTR_END()`, from `instrumentation_end()` | `insn->instr--` |
| `ANNOTYPE_UNRET_BEGIN` (5) | `ANNOTATE_UNRET_BEGIN`, `VALIDATE_UNRET_BEGIN` | sets `insn->unret`; `validate_unrets()` starts there under `--unret` |
| `ANNOTYPE_IGNORE_ALTS` (6) | `ANNOTATE_IGNORE_ALTERNATIVE` | marks one alternative arm as not followed; see below |
| `ANNOTYPE_INTRA_FUNCTION_CALL` (7) | `ANNOTATE_INTRA_FUNCTION_CALL` | error unless `INSN_CALL`; the call becomes `INSN_JUMP_UNCONDITIONAL` and keeps its stack op |
| `ANNOTYPE_REACHABLE` (8) | `ANNOTATE_REACHABLE` | clears `insn->dead_end` |
| `ANNOTYPE_NOCFI` (9) | `ANNOTATE_NOCFI_SYM` | sets `nocfi` on the symbol that contains the instruction; error "dodgy NOCFI annotation" if there is none |
| `ANNOTYPE_DATA_SPECIAL` (1) | `ANNOTATE_DATA_SPECIAL` | goes to `.discard.annotate_data`; marks the start of a special-section entry for `tools/objtool/klp-diff.c` |

- `ANNOTYPE_DATA_SPECIAL`: its value 1 is in a separate number space; it does
  not collide with `ANNOTYPE_NOENDBR` because the section differs.
- `ANNOTYPE_IGNORE_ALTS`: `handle_group_alt()` copies `insn->ignore_alts` of
  the first original instruction to the original `struct alt_group`, and of
  the first replacement instruction to the replacement group.
- `skip_alt_group()`: makes `validate_insn()` stop at an instruction whose
  group has `ignore` set; the other arms are still validated.
- Annotation on the original arm: the replacements are followed and the
  original is not, as `smap_save()` in `arch/x86/include/asm/smap.h` needs.
- Annotation on the replacement arm: the original is followed and that
  replacement is not, as `ASM_CLAC_UNSAFE` needs.
- Comment above `ANNOTATE_IGNORE_ALTERNATIVE` in `include/linux/annotate.h`:
  describes only the second case.
- `ANNOTYPE_NOCFI`: only `validate_retpoline()` tests `nocfi`, under
  `--retpoline` and `--cfi`, to suppress "no-cfi indirect call!" for calls
  inside that symbol.
- `ANNOTATE_INSTR_BEGIN()` and `ANNOTATE_INSTR_END()`: C only; the asm forms
  are commented out in `include/linux/annotate.h`.
