- `__DECLARE_TRACE`: probes run under
  `guard(srcu_fast_notrace)(&tracepoint_srcu)`; the tracepoint does not
  disable preemption or migration.
- `__DECLARE_TRACE` probe that uses per-CPU data or `smp_processor_id()`: has
  to disable preemption or migration itself unless the call site already did;
  the generated event probe disables preemption, with
  `guard(preempt_notrace)()` in `trace_event_raw_event_` plus the class name
  in `include/trace/trace_events.h`.
- `__DECLARE_TRACE` and sleeping: the probe inherits the context of the call
  site and nothing marks that site as sleepable; `bpf_raw_tp_link_attach()` in
  `kernel/bpf/syscall.c` returns `-EINVAL` for a sleepable program unless
  `tracepoint_is_faultable()`.
- `__DECLARE_TRACE_SYSCALL`: `rcu_read_lock_trace()` does not disable
  migration; `__bpf_trace_run()` in `kernel/trace/bpf_trace.c` runs a
  sleepable program under `rcu_read_lock_tasks_trace()` and calls
  `migrate_disable()` itself.
- `might_fault()` in the syscall variant: runs before the static-key test, so
  it checks the call site even while the tracepoint is disabled.
- Old probe array: `release_probes()` in `kernel/tracepoint.c` frees it with
  one callback, `call_srcu()` on `tracepoint_srcu` or
  `call_rcu_tasks_trace()`, chosen by `tracepoint_is_faultable()`.
- Probe `data`: the pointer is stored in the same `struct tracepoint_func`
  entry as the function, and the entry is covered by the same grace period;
  the tracepoint never frees what it points to.
- Static-call path: `__DO_TRACE_CALL()` reads `data` from the first array
  entry and the function from the static call separately;
  `tp_rcu_cond_sync()` in `kernel/tracepoint.c` keeps a new function from
  seeing old `data`.
- Comments in `kernel/tracepoint.c` that mention `rcu_dereference_sched()` or
  `preempt_disable()` around the call site do not describe what
  `__DECLARE_TRACE` does in this tree.
