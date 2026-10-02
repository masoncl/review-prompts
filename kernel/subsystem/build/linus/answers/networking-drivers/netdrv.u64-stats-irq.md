- `u64_stats_update_begin_irqsave()`: also needed when a reader of the same
  `struct u64_stats_sync` can run in interrupt context on the writer's CPU; on
  32-bit `__read_seqcount_begin()` in `include/linux/seqlock.h` spins while the
  sequence is odd.
- 32-bit, not `CONFIG_PREEMPT_RT`: the irqsave variant satisfies the
  preemption assertion without help, because
  `lockdep_assert_preemption_disabled()` accepts hardirqs disabled; it can be
  called with `preempt_count()` zero.
- 32-bit, `CONFIG_PREEMPT_RT`: `local_irq_save()` followed by
  `preempt_disable()` through `preempt_disable_nested()`.
- 64-bit: `__u64_stats_irqsave()` returns 0 and interrupts stay enabled, so
  the pair excludes nothing; only `u64_stats_t` updates, which go through
  `local64_t` operations such as `local64_add()`, get any help, and a plain
  `u64` `+=` shared with an interrupt handler gets none.
- Reader variants: none are defined; no name beginning u64_stats_fetch_begin_
  or u64_stats_fetch_retry_ exists anywhere in the tree, so readers in every
  context use `u64_stats_fetch_begin()` and `u64_stats_fetch_retry()`.
