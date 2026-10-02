- `tracepoint_synchronize_unregister()`: `synchronize_rcu_tasks_trace()`, then
  `synchronize_srcu(&tracepoint_srcu)`; it contains no direct
  `synchronize_rcu()` call.
- What it waits for: probes already running on faultable tracepoints (Tasks
  Trace RCU, the guard in `__DECLARE_TRACE_SYSCALL`) and on tracepoints
  declared with `__DECLARE_TRACE` (`tracepoint_srcu`); it takes no tracepoint
  argument.
- **Potentially unsafe usage**: freeing probe `data`, or returning from the
  exit function of the module that holds the probe, after
  `tracepoint_probe_unregister()` with no grace period.
  - Unsafe: when the probe dereferences `data` that is freed, or its text is
    unloaded, before a grace period of the reader's domain ends; a task that
    loaded the old array entry still calls the probe. `synchronize_rcu()` or
    `call_rcu()` is not that grace period: the reader in `__DECLARE_TRACE`
    holds only `tracepoint_srcu`.
  - Safe: `tracepoint_synchronize_unregister()` between the unregister and the
    free, as `perf_trace_event_unreg()` in `kernel/trace/trace_event_perf.c`
    does before `free_percpu()`; the readers it waits for are the guards in
    `__DECLARE_TRACE` and `__DECLARE_TRACE_SYSCALL`.
  - Safe: deferring the free with `call_tracepoint_unregister_atomic()`, which
    does not block, for a tracepoint that is not faultable, as
    `bpf_link_free()` in `kernel/bpf/syscall.c` does; it is `call_srcu()` on
    `tracepoint_srcu`, the domain the reader holds.
  - Safe: for a faultable tracepoint, `call_tracepoint_unregister_syscall()`,
    which is `call_rcu_tasks_trace()`; `bpf_link_free()` calls
    `call_rcu_tasks_trace()` directly for those links.
  - Safe: a built-in probe registered with NULL `data`, where nothing is freed,
    as `tracing_sched_unregister()` in `kernel/trace/trace_sched_switch.c`.
- `call_tracepoint_unregister_syscall()`: has no caller in this tree.
- Choosing between the two helpers: test `tracepoint_is_faultable()`, as
  `release_probes()` in `kernel/tracepoint.c` does.
- Without `CONFIG_TRACEPOINTS`: both helpers are empty stubs that never invoke
  the callback, so a free deferred through them never happens.
- `bpf_probe_unregister()` in `kernel/trace/bpf_trace.c`: only unregisters; the
  deferred free is in `bpf_link_free()`.
