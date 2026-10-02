- Two failure modes, depending on where the option is tested.
- Header declares unconditionally, defining file not built: the register
  function compiles and the link fails on the undefined
  `__tracepoint_` symbol.
- Header hides the event behind `#ifdef`: the register function is not
  declared at all, so the compile fails; `include/trace/events/preemptirq.h`
  leaves only the empty `trace_preempt_enable()` and `trace_preempt_disable()`
  macros without `CONFIG_TRACE_PREEMPT_TOGGLE`, and
  `include/trace/events/syscalls.h` declares nothing without
  `CONFIG_HAVE_SYSCALL_TRACEPOINTS`.
- Architecture-defined tracepoint: `page_fault_user` and `page_fault_kernel`,
  declared in `include/trace/events/exceptions.h`, defined only by
  `arch/x86/mm/fault.c` and `arch/riscv/mm/fault.c`.
- `arch/riscv/mm/Makefile`: builds `fault.o` only under `CONFIG_MMU`.
- User that accounts for it: `RV_MON_PAGEFAULT` in
  `kernel/trace/rv/monitors/pagefault/Kconfig`, with `depends on X86 || RISCV`
  and `depends on MMU`.
- Other RV entries of the same kind, for example: `RV_MON_SNEP` depends on
  `TRACE_PREEMPT_TOGGLE`, `RV_MON_STS` on `TRACE_IRQFLAGS`, `RV_MON_SLEEP` on
  `HAVE_SYSCALL_TRACEPOINTS`.
- RV monitors are `bool`, so a missing dependency breaks the vmlinux build, not
  a module.
