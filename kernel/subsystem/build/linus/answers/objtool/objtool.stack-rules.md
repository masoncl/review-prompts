- "unsupported stack state": no such warning under `tools/objtool`; a bad
  frame at return is "return with modified stack frame" from
  `validate_return()`.
- `ASM_CALL_CONSTRAINT`: is `"+r" (current_stack_pointer)` in
  `arch/x86/include/asm/asm.h`; `current_stack_pointer` is the register
  variable declared on the line above it.
- `ASM_CALL_CONSTRAINT`: defined with no configuration test, so it is the same
  with and without frame pointers; only x86 defines it.
- Frame-pointer-only checks: the two checks behind `opts.stackval` in
  `tools/objtool/check.c`: "call without frame pointer save/setup" in
  `validate_insn()`, and setting `bp_scratch` in `update_cfi_state()`, which
  `validate_return()` reports as "BP used as a scratch register".
- `--stackval`: passed for `CONFIG_STACK_VALIDATION` in `scripts/Makefile.lib`;
  that option depends on `HAVE_STACK_VALIDATION && UNWINDER_FRAME_POINTER` in
  `lib/Kconfig.debug`. `CONFIG_FRAME_POINTER` alone does not pass it.
- "call without frame pointer save/setup": not raised when
  `is_special_call()` is true (call to a symbol with `fentry` or
  `embedded_insn`), nor outside an `STT_FUNC`.
- Saved registers at return: `has_modified_stack_frame()` compares every
  entry of `regs` with `initial_func_cfi`, in every mode; it is not a
  frame-pointer-only check.
- Every other stack check: runs in every walk, that is over all text when
  `validate_branch_enabled()` is true (`--stackval`, `--orc` or `--uaccess`),
  and over the noinstr sections with `--noinstr` alone
  (`validate_noinstr_sections()`).
- Indirect jump inside a function: the stack walk needs no annotation for it;
  `is_sibling_call()` takes an `INSN_JUMP_DYNAMIC` with no jump table as a
  sibling call, so it needs the entry stack state.
- `INSN_SYSCALL` and `INSN_SYSRET` in a function: "unsupported instruction in
  callable function" only when the next instruction has no `hint`.
- `iret` inside an `STT_FUNC`: decoded in `tools/objtool/arch/x86/decode.c` as
  a stack op that adds 40 to the stack pointer, not as `INSN_SYSRET`.
- `STACK_FRAME_NON_STANDARD_FP()` in `include/linux/objtool.h`: expands to
  `STACK_FRAME_NON_STANDARD()` only under `CONFIG_FRAME_POINTER`, and to
  nothing otherwise, so the function is still validated for ORC.
