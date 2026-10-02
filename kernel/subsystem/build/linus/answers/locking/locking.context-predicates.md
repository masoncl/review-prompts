- `preempt_count()` layout: bits 16-23 are `HARDIRQ_DISABLE_MASK`, the
  nesting count of `local_interrupt_disable()`; `HARDIRQ_MASK` is bits
  24-27; `NMI_BITS` is 4 with `CONFIG_HAS_SEPARATE_PREEMPT_RESCHED_BITS`,
  else 1 with nesting kept in the per-CPU `nmi_nesting`.
- `in_atomic()` inside `local_interrupt_disable()` or a
  `raw_spin_lock_irq_disable()` region: true, with or without
  `CONFIG_PREEMPT_COUNT`.
- `in_atomic()` inside `local_irq_disable()`: still false;
  `preempt_count()` is unchanged, and only `irqs_disabled()`, and
  `preemptible()` through it, see the disable.
- `in_interrupt()` and `in_task()`: do not look at `HARDIRQ_DISABLE_MASK`.
- `in_softirq()` true on PREEMPT_RT: says only that this task has a
  BH-disabled count; without `CONFIG_PREEMPT_RT_NEEDS_BH_LOCK` a softirq
  handler may still run on this CPU in another task.
- `CONFIG_PREEMPT_COUNT`: search Kconfig files for
  `select PREEMPT_COUNT`; `PROVE_LOCKING` selects it too, except on
  `ARCH_NO_PREEMPT`.
