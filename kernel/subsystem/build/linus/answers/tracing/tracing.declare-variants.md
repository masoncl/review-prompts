- `DECLARE_TRACE()`: passes `name##_tp` to `__DECLARE_TRACE()`, so every
  generated name carries the suffix; a call site fires it as, for example,
  `trace_sched_set_need_resched_tp()` in `kernel/sched/core.c`.
- `DECLARE_TRACE_EVENT()` is what `TRACE_EVENT()` and `DEFINE_EVENT()` expand
  to; it passes the name unchanged.
- Definition: no `.c` file in this tree calls `DEFINE_TRACE()`; it takes name,
  proto and args. A bare tracepoint is defined by including its header under
  `CREATE_TRACE_POINTS`; `include/trace/define_trace.h` turns
  `DECLARE_TRACE()` into `DEFINE_TRACE()` on the suffixed name.
- `DECLARE_TRACE_SYSCALL()`: `include/trace/define_trace.h` has no mapping for
  it, and nothing in this tree uses it.
- Export: there is no EXPORT_TRACEPOINT_GPL() or EXPORT_TRACEPOINT() here; use
  `EXPORT_TRACEPOINT_SYMBOL_GPL()` or `EXPORT_TRACEPOINT_SYMBOL()` with the
  suffixed name, as `kernel/sched/core.c` does for `sched_set_state_tp`.
- `trace_call__` plus the name: defined beside the normal trace function by
  `__DECLARE_TRACE()` and `__DECLARE_TRACE_SYSCALL()`; it runs the probes
  without testing the static key.
- `trace_call__` form, what it keeps: in `__DECLARE_TRACE()` the `cond` test
  (`cpu_online(raw_smp_processor_id())` and any `TP_CONDITION()`), the
  read-side guard, and `might_fault()` in the syscall variant.
- `trace_call__` form, what it drops: the `CONFIG_LOCKDEP` "RCU not watching"
  warning that the normal trace function makes.
- `trace_call__` form, intended place: code reached only after
  `tracepoint_enabled()` or the generated enabled function tested true, for
  example `__trace_set_current_state()` in `kernel/sched/core.c` and
  `queued_spin_release_traced()` in `kernel/locking/qspinlock.c`.
- `trace_call__` form with no probe registered: enters the read section (in
  `__DECLARE_TRACE()` only when `cond` passes), finds `funcs` NULL and calls
  nothing; the cost is the lost static branch, not a crash.
