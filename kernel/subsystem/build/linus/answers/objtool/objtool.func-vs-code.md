- ELF type: set by the END macro, not the START macro; `SYM_FUNC_END` passes
  `SYM_T_FUNC` and `SYM_CODE_END` passes `SYM_T_NONE` to `SYM_END()`.
- x86 `SYM_FUNC_START` in `arch/x86/include/asm/linkage.h`: emits no ENDBR;
  only `SYM_TYPED_FUNC_START` does.
- UNWIND_HINT_EMPTY: not in this tree; use `UNWIND_HINT_UNDEFINED` or
  `UNWIND_HINT_END_OF_STACK` from `arch/x86/include/asm/unwind_hints.h`.
- Warnings that fire only for code inside an `STT_FUNC` symbol (the test is
  `func` or `insn_func()`):
  - "return with modified stack frame"
  - "sibling call from callable instruction with modified stack frame"
  - "call without frame pointer save/setup"
  - "unsupported instruction in callable function"
  - "undefined stack state"
  - "redundant UACCESS disable" and "redundant CLD"
  - "falls through to next function"
  - "BP used as a scratch register"; `update_cfi_state()` sets `bp_scratch`
    only under `--stackval` for an instruction with `insn_func()`
  - "unsupported call to non-function", an error in `add_call_destinations()`
  - "is missing an ELF size annotation", from `validate_symbol()`, which
    `validate_section()` calls for `STT_FUNC` symbols only
- Not specific to either kind: "unsupported stack register modification",
  "unsupported stack pointer realignment", "stack state mismatch" and
  "unannotated intra-function call".
