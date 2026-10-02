- `CONFIG_PREEMPT_RT`: `local_bh_disable()` and `spin_lock()` sections stay
  readers although they are preemptible, because `__local_bh_disable_ip()` in
  `kernel/softirq.c` and `rt_spin_lock()` call `rcu_read_lock()`.
- `__local_bh_disable_ip()` on `CONFIG_PREEMPT_RT`: calls `rcu_read_lock()`
  only on the task's first BH-disable and only if `preemptible()`; from a
  non-preemptible caller the region is a reader through that caller's state.
- Threaded interrupt handlers: a forced-threaded handler runs inside
  `local_bh_disable()` in `irq_forced_thread_fn()`, so it is a reader. A
  handler that runs through `irq_thread_fn()` alone is not.
- `rcu_softirq_qs()` in `kernel/rcu/tree.c`: is a quiescent state inside a
  BH-disabled region; `synchronize_rcu()` waits only up to that call.
- `handle_softirqs()` in `kernel/softirq.c`: calls `rcu_softirq_qs()` after
  each pass over the pending handlers when run from ksoftirqd on non-RT, so a
  reader there does not span two passes.
- `rcu_softirq_qs_periodic()`: calls `rcu_softirq_qs()` at most once per
  `HZ / 10`, and never on `CONFIG_PREEMPT_RT`, between passes of long-running
  softirq-like loops; for example `napi_threaded_poll_loop()` in
  `net/core/dev.c`.
- `lockdep_assert_in_rcu_reader()` in `include/linux/rcupdate.h`: the
  assertion that accepts implicit readers; it passes on any of the three
  lockdep maps or `!preemptible()`.
