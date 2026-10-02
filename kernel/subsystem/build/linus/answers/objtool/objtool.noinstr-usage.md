- Call through a retpoline thunk: treated as an indirect call, so accepted
  only inside a begin/end region; its reloc is against the thunk, so
  `pv_call_dest()` does not accept it.
- Tail call: `validate_sibling_call()` runs `validate_call()` and not
  `validate_return()`; with the count above 0 it is accepted, with no
  "return with instrumentation enabled" warning.
- Noreturn callee: the call itself is still checked by `validate_call()`, but
  the walk stops at `insn->dead_end`, so no `instrumentation_end()` is needed
  after it.
- `instrumentation_end()` emits: a numeric label from `__COUNTER__`, a `nop`,
  and an `ANNOTATE_INSTR_END()` entry that refers back to the label with
  `__ASM_BREF()`. It emits no reachable annotation.
- `instrumentation_begin()`: emits the same label and `nop`; only the
  annotation type differs.
- Example of a bracketed region in `kernel/entry/common.c`:
  `irqentry_nmi_enter()`. `irqentry_enter()` has no begin/end of its own in
  this tree; the regions are in the inline helpers in
  `include/linux/irq-entry-common.h`.
