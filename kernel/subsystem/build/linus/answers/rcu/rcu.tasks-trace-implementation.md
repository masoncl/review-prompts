- Tasks Trace RCU: a mapping onto SRCU-fast; there is one
  `struct srcu_struct`, `rcu_tasks_trace_srcu_struct`, defined by
  `DEFINE_SRCU_FAST()` in `kernel/rcu/tasks.h` and exported.
- Reader and update-side functions: all static inlines in
  `include/linux/rcupdate_trace.h`.
- `CONFIG_TASKS_RCU_GENERIC`: is `TASKS_RCU || TASKS_RUDE_RCU`, so a kernel
  with only `CONFIG_TASKS_TRACE_RCU` builds none of the `struct rcu_tasks`
  code and has no Tasks grace-period kthread.
- `rcu_read_lock_trace()`: calls `__srcu_read_lock_fast()` directly, not
  `srcu_read_lock_fast()`, so `srcu_check_read_flavor()` is never run for it.
- `struct task_struct`: still holds `trc_reader_nesting` and
  `trc_reader_scp`; `rcu_read_lock_trace()` uses both.
- End of a Tasks Trace grace period, Tree SRCU: at least one RCU grace period
  has elapsed inside it. See `srcu_readers_active_idx_check()` in
  `kernel/rcu/srcutree.c`; for `SRCU_READ_FLAVOR_SLOWGP` it calls
  `synchronize_rcu()` or `synchronize_rcu_expedited()` on each scan, and
  `srcu_advance_state()` scans twice before `srcu_gp_end()`.
- Some callers rely on the guarantee unconditionally: a
  `call_rcu_tasks_trace()` callback frees memory that plain RCU readers also
  use, with no chained `call_rcu()`. For example
  `__bpf_prog_array_free_sleepable_cb()` in `kernel/bpf/core.c` and
  `bpf_selem_free_trace_rcu()` in `kernel/bpf/bpf_local_storage.c`.
- rcutorture checks the guarantee: `tasks_tracing_torture_read_lock()` in
  `kernel/rcu/rcutorture.c` sometimes protects a reader with
  `rcu_read_lock()` while the updater uses only Tasks Trace.
- Tiny SRCU (`CONFIG_TINY_SRCU`, default with `TINY_RCU`):
  `include/linux/srcutiny.h` maps `DEFINE_SRCU_FAST()` to `DEFINE_SRCU()` and
  `__srcu_read_lock_fast()` to `__srcu_read_lock()`; `srcu_barrier()` is
  `synchronize_srcu()` and `srcu_expedite_current()` is empty.
- Tiny SRCU grace period: `kernel/rcu/srcutiny.c` never calls
  `synchronize_rcu()`; callbacks run from the `srcu_drive_gp()` work item,
  which cannot run inside an RCU reader there: `CONFIG_TINY_RCU` means one
  CPU, and `__rcu_read_lock()` is `preempt_disable()`.
