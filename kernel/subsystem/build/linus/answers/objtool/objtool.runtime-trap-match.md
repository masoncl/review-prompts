- `ANNOTATE_REACHABLE(1b)` on x86 and `ANNOTATE_REACHABLE(10001b)` on
  LoongArch: the label is on the trap instruction itself, not on the
  instruction after it.
- Section used: `.discard.annotate_insn`, read by `read_annotate()`.
- x86-64 `WARN()` with a format and `WARN_ONCE()` under
  `HAVE_ARCH_BUG_FORMAT_ARGS`: no trap at the call site;
  `__WARN_print_arg()` emits `static_call_mod(WARN_trap)(...)`.
- That static call for objtool: a call to a static-call trampoline;
  `annotate_call_site()` returns for `sym->static_call_tramp` before it
  consults `dead_end_function()`, so the site is never a dead end.
- `__WARN_trap()` in `arch/x86/entry/entry.S`: `ANNOTATE_REACHABLE`, then
  `ud1 (%edx), %_ASM_ARG1`, then `RET`; the `ud1` is `INSN_BUG` and the
  annotation keeps the `RET` reachable.
- Run time: `__static_call_transform()` in `arch/x86/kernel/static_call.c`
  patches such call sites to that `ud1` (`warninsn`); objtool never sees it
  at the call site.
- `ud2` plus `ARCH_WARN_REACHABLE`: what x86 `WARN_ON()`, `WARN_ON_ONCE()`
  and `__WARN()` emit through `__WARN_FLAGS()`.
