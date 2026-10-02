- `--uaccess`: passed for `CONFIG_HAVE_UACCESS_VALIDATION` in
  `scripts/Makefile.lib`; there is no CONFIG_X86_SMAP in this tree.
- `INSN_STAC` and `INSN_CLAC`: produced only by
  `tools/objtool/arch/x86/decode.c`.
- `validate_call()`: has three tests only (noinstr, uaccess, DF); it has no
  `__fentry__` test.
- DF: `INSN_STD` and `INSN_CLD` in `validate_insn()` are not gated by
  `opts.uaccess`, so the DF checks run in every `validate_branch()` walk.
- Inside a safe-listed function, `validate_return()` with access off: warns
  "return with UACCESS disabled from a UACCESS-safe function".
- Inside a safe-listed function, `INSN_CLAC` with `uaccess_stack` empty: warns
  "UACCESS-safe disables UACCESS".
- `uaccess_safe_builtin`: holds no `memcpy`, `memset`, `__memcpy` or
  `__memset` entry.
- Flags save and restore: tracked in `handle_insn_ops()`, not in
  `update_cfi_state()`, and only when `opts.uaccess` is set and the
  instruction has `alt_group` set.
- `alt_group`: `handle_group_alt()` sets it on the original instructions of an
  alternative as well as on the replacement.
- `pushf` or `popf` outside any alternative: updates the CFI stack state only;
  `state->uaccess` and `uaccess_stack` do not change.
- `ASM_STAC_UNSAFE` and `ASM_CLAC_UNSAFE` in `arch/x86/include/asm/smap.h`:
  carry `ANNOTATE_IGNORE_ALTERNATIVE` in the replacement, so `skip_alt_group()`
  drops it and objtool sees no change of access.
