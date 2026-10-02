- Tasks Trace readers (`rcu_read_lock_trace()`, `rcu_read_lock_tasks_trace()`,
  `guard(rcu_tasks_trace)`): SRCU-fast readers of
  `rcu_tasks_trace_srcu_struct`, defined in `kernel/rcu/tasks.h`.
- `synchronize_rcu_tasks_trace()` and `call_rcu_tasks_trace()`: inline
  wrappers for `synchronize_srcu()` and `call_srcu()` on that domain; see
  `include/linux/rcupdate_trace.h`.
- There is no rcu_trace_implies_rcu_gp() here. BPF passes the final free
  straight to `call_rcu_tasks_trace()`, for example `bpf_map_put()` in
  `kernel/bpf/syscall.c` and `do_call_rcu_ttrace()` in `kernel/bpf/memalloc.c`.
- What makes that cover plain RCU readers under `CONFIG_TREE_SRCU`:
  `srcu_readers_active_idx_check()` calls `synchronize_rcu()` or
  `synchronize_rcu_expedited()` for a domain with `SRCU_READ_FLAVOR_SLOWGP`.
- The reverse does not hold: `call_rcu()` and `synchronize_rcu()` do not wait
  for `rcu_read_lock_trace()` readers; `__bpf_prog_put_noref()` picks by
  `prog->sleepable`.
- RCU-watching check: `rcu_read_lock()`, `srcu_read_lock_fast()`,
  `srcu_read_lock_fast_updown()` and `srcu_down_read_fast()` have
  `RCU_LOCKDEP_WARN(!rcu_is_watching(), ...)`.
- `rcu_read_lock_trace()` and `rcu_read_unlock_trace()`: each adds an
  `smp_mb()` unless `CONFIG_TASKS_TRACE_RCU_NO_MB`.
- Tracepoint probes: run under `guard(srcu_fast_notrace)(&tracepoint_srcu)`,
  or under `guard(rcu_tasks_trace)()` for faultable (syscall) tracepoints,
  not under `preempt_disable()`; see `include/linux/tracepoint.h`.
- Examples of waiting for every kind of reader that reaches the object:
  - `tracepoint_synchronize_unregister()`: Tasks Trace, then
    `tracepoint_srcu`.
  - `ftrace_shutdown()` in `kernel/trace/ftrace.c`:
    `synchronize_rcu_tasks_rude()`, then `synchronize_rcu_tasks()`.
  - `bpf_tramp_image_put()` in `kernel/bpf/trampoline.c`:
    `call_rcu_tasks_trace()` chained into `call_rcu_tasks()`.
