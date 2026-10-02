- `struct unwind_hint` in `include/linux/objtool_types.h`: has no sym_offset
  field, and `struct instruction` has no unwind_hint member; the
  per-instruction state is the bits `hint`, `save`, `restore` and the pointer
  `cfi`.
- `UNWIND_HINT_TYPE_END_OF_STACK`: becomes `ORC_TYPE_END_OF_STACK`, not
  `ORC_TYPE_UNDEFINED`; see `init_orc_entry()` in
  `tools/objtool/arch/x86/orc.c`.
- `sp_reg`, `sp_offset`, `signal`: `read_unwind_hints()` reads them only for
  `UNWIND_HINT_TYPE_END_OF_STACK`, `UNWIND_HINT_TYPE_CALL`,
  `UNWIND_HINT_TYPE_REGS` and `UNWIND_HINT_TYPE_REGS_PARTIAL`; for the other
  four types it moves to the next hint first.
- `UNWIND_HINT_TYPE_FUNC`: the instruction gets `func_cfi`, built by
  `set_func_state()` from `arch_initial_func_cfi_state()`, with type
  `UNWIND_HINT_TYPE_CALL`. The `ORC_REG_SP` and 8 that x86 `UNWIND_HINT_FUNC`
  passes are not used.
- `UNWIND_HINT_TYPE_UNDEFINED`: the instruction gets `force_undefined_cfi`;
  while `force_undefined` is set `update_cfi_state()` returns before looking
  at any stack op, until another hint replaces the state.
- CFA base `CFI_UNDEFINED` without `force_undefined`: the next stack op inside
  an `STT_FUNC` warns "undefined stack state".
- `UNWIND_HINT_TYPE_SAVE`: clears `hint` and sets `save`, so the instruction
  keeps the tracked state, `validate_unwind_hints()` does not start a walk
  there, and it does not count for the tests of `next_insn->hint`.
- `UNWIND_HINT_TYPE_RESTORE`: keeps `hint` set; `read_unwind_hints()` leaves
  `cfi` unset and `validate_insn()` fills it from the instruction with `save`.
- "UNWIND_HINT_IRET_REGS without ENDBR": only for
  `UNWIND_HINT_TYPE_REGS_PARTIAL`, not `UNWIND_HINT_TYPE_REGS`; needs `--ibt`,
  a global symbol starting at the instruction, an instruction that is not
  `INSN_ENDBR` and has no `noendbr`. It is an `ERROR_INSN()` and
  `read_unwind_hints()` returns -1.
- x86 `UNWIND_HINT_ENTRY` in `arch/x86/include/asm/unwind_hints.h`: emits
  `VALIDATE_UNRET_BEGIN` and `UNWIND_HINT_TYPE_END_OF_STACK`; no hint type is
  specific to entry.
- loongarch `UNWIND_HINT_FUNC` in `arch/loongarch/include/asm/unwind_hints.h`:
  emits `UNWIND_HINT_TYPE_CALL` with `ORC_REG_SP`, not
  `UNWIND_HINT_TYPE_FUNC`.
