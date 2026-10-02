- `tools/objtool/Documentation/objtool.txt` explains 12 numbered entries. It has
  no entry for the retpoline, noinstr, DF, "return with modified stack frame",
  "return with UACCESS enabled" or "undefined stack state" messages.

| # | Documented text | Printed in | Kind | Printed text differs |
|---|---|---|---|---|
| 1 | call without frame pointer save/setup | `validate_insn()` | counted | `func+0x..`, no `()` |
| 2 | unreachable instruction | `validate_reachable_instructions()` | counted | same |
| 3 | missing __noreturn ... | `validate_reachable_instructions()` | counted | same |
| 4a | can't find starting instruction | `decode_instructions()` | fatal `ERROR()` | `error:` |
| 4b | can't decode instruction | `arch_decode_instruction()` in `tools/objtool/arch/x86/decode.c` | fatal `ERROR()` | `error:`, "at `<sec>:0x<off>`", no symbol prefix |
| 5 | unsupported instruction in callable function | `validate_insn()` | counted | `func+0x..` |
| 6 | sibling call ... modified stack frame | `validate_sibling_call()` | counted | `func+0x..` |
| 7 | stack state mismatch | `insn_cfi_match()` | counted | appends `: cfa1=...`, `reg1[..]`, `type1=` or `drap1=` |
| 8 | falls through to next function | `do_validate_branch()` | counted | same, plain `WARN()` |
| 9 | call to funcB() with UACCESS enabled | `validate_call()` | counted | `funcA+0x..: call to ...`, not `funcA() call to` |
| 10 | stack layout conflict in alternatives | `propagate_alt_cfi()` | counted | has `objtool:`; appends `: <location>` |
| 11 | unannotated intra-function call | `add_call_destinations()` | fatal `ERROR_INSN()` | `error: objtool: func+0x..:` prefix |
| 12 | not an indirect call target | nowhere | - | no code in the tree has the string |

- Entry 1: tested only with `opts.stackval`, only after `validate_call()`
  returned 0, and not for `is_special_call()` destinations.
- Entry 2: runs only when `validate_functions()` and `validate_unwind_hints()`
  together returned 0, see `if (!w)` in `check()`.
- Entries 2 and 8: suppressed when `file->ignore_unreachables` is set, which
  `--no-unreachable` does; `scripts/Makefile.lib` passes it for
  `CONFIG_GCOV_KERNEL` or `CONFIG_KCOV`.
- Entry 2 fix in the documentation: annotate with `SYM_FUNC_START` and
  `SYM_FUNC_END`, or `SYM_CODE_START` plus unwind hints. The noreturn fix
  belongs to entry 3.
- Entry 3: printed instead of entry 2 when the previous instruction is
  `dead_end` and has a call destination.
- Entry 5, `iret`: the documentation names it, but inside an `STT_FUNC` symbol
  `arch_decode_instruction()` in `tools/objtool/arch/x86/decode.c` does not make
  it `INSN_SYSRET`.
- Entry 6: the documentation says "branch to an UNDEF symbol";
  `is_sibling_call()` also covers a jump to the first instruction of another
  function in the same file, and an indirect jump that is not a jump table.
- Entry 6 fix in the documentation: unwind hints, move the destination into the
  file, or `SYM_CODE_START` with hints. It does not mention
  `STACK_FRAME_NON_STANDARD`.
- Entry 8 fix in the documentation: add the callee to the noreturn list, remove
  a wrong `unreachable()`, or look for undefined behaviour.
- Entry 8, `global_noreturns`: exists, as a static array in
  `__dead_end_function()`, filled from `tools/objtool/noreturns.h` through
  `NORETURN()`.
- Entry 9: `validate_call()` tests noinstr first; the callee name is
  `pv_ops[N]` or `{dynamic}` for an indirect call, see `call_dest_name()`.
- Entry 10: `propagate_alt_cfi()` returns -1, but `validate_insn()` returns 1,
  so it is a counted warning. It is reported at the first instruction of the
  original group.
- Entry 12: the nearest code is in `create_ibt_endbr_seal_sections()`: with
  `opts.module`, `init_module` or `cleanup_module` on `file->endbr_list` gives
  the fatal `ERROR()` "Magic init_module() function name is deprecated, use
  module_init(fn) instead".
- Macro names in the documentation: `SYM_FUNC_START`, `SYM_FUNC_END`,
  `SYM_CODE_START`, `SYM_CODE_END`; it has no older names.
- Under `--werror` every counted row above prints `error:` (see "Warnings and
  errors").
