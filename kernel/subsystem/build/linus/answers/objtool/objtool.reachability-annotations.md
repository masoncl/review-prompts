- `ANNOTATE_REACHABLE`: goes on the dead-end instruction itself, the `ud2` or
  the `call` to a noreturn function, not on the instruction after it.
- C form `ANNOTATE_REACHABLE(label)`: `label` must be the label of the
  dead-end instruction; x86 `ARCH_WARN_REACHABLE` passes `1b`, the `ud2` in
  `_BUG_FLAGS()`.
- Asm form `ANNOTATE_REACHABLE`: takes no argument and annotates the next
  instruction emitted, as before `call \cfunc` in `arch/x86/entry/entry_64.S`.
- `dead_end` is set in two places: `decode_instructions()` for `INSN_BUG`, and
  `annotate_call_site()` for a non-sibling call when `dead_end_function()` is
  true.
- `__dead_end_function()`: matches `tools/objtool/noreturns.h` by name for
  non-local symbols only; it also treats any non-weak function defined in the
  object as noreturn when its body has no `INSN_RETURN` and no sibling call.
- Running off the end of a function: not a dead end; `do_validate_branch()`
  warns "falls through to next function".
