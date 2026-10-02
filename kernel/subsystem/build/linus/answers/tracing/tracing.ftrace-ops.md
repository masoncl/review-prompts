- `fregs` may be NULL: `arch_ftrace_ops_list_func()` in
  `kernel/trace/ftrace.c` passes NULL when `ARCH_SUPPORTS_FTRACE_OPS` is 0.
  `ftrace_get_regs()` tests for it; `ftrace_regs_get_argument()` and the other
  accessors do not.
- `ftrace_get_regs()` result depends on the arch, not only on the flag:
  - arm64 and riscv define `arch_ftrace_get_regs()` as NULL under
    `CONFIG_DYNAMIC_FTRACE_WITH_ARGS`, so it is always NULL there.
  - without `CONFIG_HAVE_DYNAMIC_FTRACE_WITH_ARGS` the generic
    `arch_ftrace_get_regs()` returns `&arch_ftrace_regs(fregs)->regs` whenever
    `fregs` is non-NULL.
  - the x86, s390 and powerpc definitions return NULL unless a marker field
    shows a full save.
- `FTRACE_OPS_FL_SAVE_ARGS` in `include/linux/ftrace.h`: the flag an owner sets
  to be sure the argument accessors work. It is 0 with
  `CONFIG_DYNAMIC_FTRACE_WITH_ARGS`, else `FTRACE_OPS_FL_SAVE_REGS`.
- **Potentially unsafe usage**: calling `ftrace_regs_get_argument()` or
  another `fregs` accessor in a callback.
  - Unsafe: without `CONFIG_DYNAMIC_FTRACE_WITH_ARGS`, on an ops that did not
    ask for registers; `fregs` can be NULL and the accessor dereferences it.
  - Safe: the ops sets `FTRACE_OPS_FL_SAVE_ARGS`, as `fprobe_ftrace_ops` in
    `kernel/trace/fprobe.c` does; `__register_ftrace_function()` returns
    -EINVAL when that is `FTRACE_OPS_FL_SAVE_REGS` and
    `CONFIG_DYNAMIC_FTRACE_WITH_REGS` is off.
- `ftrace_partial_regs()`: use the return value, not the buffer passed in. The
  generic version ignores the buffer and returns a pointer into `fregs`; arm64
  and riscv copy into the buffer. It is not defined for an arch with
  `CONFIG_HAVE_DYNAMIC_FTRACE_WITH_ARGS` and without
  `CONFIG_HAVE_FTRACE_REGS_HAVING_PT_REGS` unless the arch supplies one.
- `ftrace_partial_regs_update()`: call it after changing the returned
  `struct pt_regs`; see `kernel/trace/bpf_trace.c`.
- `ftrace_regs_set_instruction_pointer()`: an empty macro without
  `CONFIG_HAVE_DYNAMIC_FTRACE_WITH_ARGS`; the ip is not changed.
- `FTRACE_OPS_FL_SAVE_REGS_IF_SUPPORTED`: read only in
  `__register_ftrace_function()`, under
  `#ifndef CONFIG_DYNAMIC_FTRACE_WITH_REGS`. With
  `CONFIG_DYNAMIC_FTRACE_WITH_REGS` it does nothing on its own; an ops that
  wants registers where available sets both flags, as `test_regs_probe` in
  `kernel/trace/trace_selftest.c` has on its second registration.
- Flags that are not the owner's to set, for example:

| Flag | Set by |
|---|---|
| `FTRACE_OPS_FL_DIRECT` | `register_ftrace_direct()` and `update_ftrace_direct_add()`, through `MULTI_FLAGS` |
| `FTRACE_OPS_FL_STUB` | core placeholder ops; `__ftrace_ops_list_func()` skips them |
| `FTRACE_OPS_FL_SUBOP` | `ftrace_startup_subops()` |
| `FTRACE_OPS_FL_GRAPH` | `register_ftrace_graph()` |
| `FTRACE_OPS_FL_ALLOC_TRAMP` | arch code, see `arch/x86/kernel/ftrace.c` |

- `FTRACE_OPS_FL_TRACE_ARRAY`: defined, never set or tested in this tree.
- `FTRACE_OPS_FL_DYNAMIC`: `__register_ftrace_function()` sets it when
  `is_kernel_core_data()` is false for the ops, whatever the owner set. A
  static ops in a module is therefore dynamic. There is no core_kernel_data()
  here.
- **Potentially unsafe usage**: setting `FTRACE_OPS_FL_PID` on an ops.
  - Unsafe: `ops->private` is non-NULL and is not a `struct trace_array *`;
    `ftrace_pids_enabled()` and `ftrace_pid_func()` dereference it as one.
  - Safe: `ops->private` is the trace array, as `ftrace_allocate_ftrace_ops()`
    in `kernel/trace/trace_functions.c` sets it.
- `ftrace_shutdown()` does the wait for the owner: `synchronize_rcu_tasks_rude()`
  then `synchronize_rcu_tasks()`, both unconditional inside
  `if (ops->flags & FTRACE_OPS_FL_DYNAMIC)`. `FTRACE_OPS_FL_RCU` plays no part.
- **Potentially unsafe usage**: freeing the ops, or memory its callback reads,
  right after `unregister_ftrace_function()`.
  - Unsafe: it returned non-zero. `ftrace_shutdown()` returns `-ENODEV` when
    `ftrace_disabled` is set, or the error of `__unregister_ftrace_function()`,
    before the wait.
  - Unsafe: the ops is in core kernel `.data` or `.bss` and
    `FTRACE_OPS_FL_DYNAMIC` is not set on it, so no wait is done.
  - Unsafe: without `CONFIG_DYNAMIC_FTRACE`; `ftrace_shutdown()` is then a macro
    in `kernel/trace/ftrace_internal.h` with no wait of its own, and
    `update_ftrace_function()` waits only when the trace function changes.
  - Safe: it returned 0 for an ops outside core kernel data, with
    `CONFIG_DYNAMIC_FTRACE`; `ftrace_shutdown()` in `kernel/trace/ftrace.c` has
    then done both waits, also when `ftrace_enabled` is 0.
