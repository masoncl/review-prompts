- There is no syscall_enter_from_user_mode() in this tree;
  `syscall_enter_from_user_mode_randomize_stack()` (a macro) and
  `syscall_enter_from_user_mode_work()` in `include/linux/entry-common.h` do
  that job.
- `syscall_enter_from_user_mode_work()`: returns `bool` (run the syscall or
  skip it) and hands back the possibly changed number through its `long *`
  argument; `syscall_enter_from_user_mode_randomize_stack()` yields that same
  value, not the number.
- Generic syscall entry and exit work: inline in
  `include/linux/entry-common.h` (`syscall_trace_enter()`,
  `syscall_exit_work()`, `syscall_exit_to_user_mode()`), not in
  `kernel/entry/common.c`.
- `kernel/entry/common.c`: holds `exit_to_user_mode_loop()` and the
  `irqentry_enter()` family, and no syscall code;
  `kernel/entry/syscall-common.c` holds only the out-of-line tracepoint and
  audit helpers.
- `enter_from_user_mode()` and `exit_to_user_mode()`: shared with interrupt
  entry, defined in `include/linux/irq-entry-common.h`.
- x86 dispatch: a generated `switch`, not a table lookup; see
  `x64_sys_call()`, `x32_sys_call()` in `arch/x86/entry/syscall_64.c` and
  `ia32_sys_call()` in `arch/x86/entry/syscall_32.c`.
- `sys_call_table` in `arch/x86/entry/syscall_64.c`: holds native 64-bit
  stubs only and is read only by `arch_syscall_addr()` in
  `kernel/trace/trace_syscalls.c`; x86-64 has no table array for x32 or ia32.
- arm64 dispatch: indexes `sys_call_table` and `compat_sys_call_table` in
  `invoke_syscall()`, `arch/arm64/kernel/syscall.c`.
- `SYSCALL_WORK_*` and the `syscall_work` word: exist only under
  `CONFIG_GENERIC_ENTRY`; otherwise `set_syscall_work()` and its siblings in
  `include/linux/thread_info.h` act on `TIF_*` bits in `flags`.
- arm64: selects `CONFIG_GENERIC_IRQ_ENTRY` but not `CONFIG_GENERIC_ENTRY`, so
  its syscall path is its own (`el0_svc_common()`, tested against
  `_TIF_SYSCALL_WORK`).
- `syscall_trace_enter()`: the generic inline and unrelated per-architecture
  functions share the name. The generic inline returns true to run the
  syscall and false to skip it; the arm64 one in
  `arch/arm64/kernel/ptrace.c`, for example, returns the syscall number or
  `NO_SYSCALL`.
- Entry hooks: `ptrace_report_syscall_permit_entry()`,
  `seccomp_permit_syscall()` and `__seccomp_permit_syscall()` return `bool`,
  true meaning "run the syscall"; there is no ptrace_report_syscall_entry() or
  __secure_computing() in this tree.
- `SYSCALL_WORK_SYSCALL_RSEQ_SLICE`: an entry work bit that is not a tracer
  hook; set in `kernel/rseq.c`, handled by `rseq_syscall_enter_work()` after
  syscall user dispatch and before ptrace.
- `struct restart_block`: used as `current->restart_block`, a member of
  `struct task_struct`; the member of that name left in csky's
  `struct thread_info` is read by no code.
- `SYSCALL_DEFINEx()` layers on x86: the stub prefixed `__x64_` or `__ia32_`
  takes `const struct pt_regs *`, `__se_sys##name` takes each argument as
  `long` or `long long` and casts it to the declared type, `__do_sys##name`
  is the body; see `arch/x86/include/asm/syscall_wrapper.h`.
