- `__rq_lockp()` in `kernel/sched/sched.h`: tests `rq->core_enabled` only.
  `rq_lockp()` tests `sched_core_enabled()`, which is the static key
  `__sched_core_enabled` and `rq->core_enabled`.
- `raw_spin_rq_lock_nested()` and `raw_spin_rq_trylock()`: test
  `sched_core_disabled()` first and then take `&rq->__lock`; otherwise they
  loop on `__rq_lockp()`.
- `raw_spin_rq_unlock()`: unlocks `rq_lockp()`. `lockdep_assert_rq_held()`,
  `rq_pin_lock()`, `rq_unpin_lock()` and `rq_repin_lock()` use `__rq_lockp()`.
- Lock other than the embedded one: only when `rq->core_enabled` is set and
  `rq->core != rq`. For the core leader `rq->core == rq`, so it gets its own
  `__lock`.
- `rq->core` is written by CPU hotplug, not by core-scheduling enable: see
  `sched_core_cpu_starting()`, `sched_core_cpu_deactivate()` and
  `sched_core_cpu_dying()` in `kernel/sched/core.c`. `rq->core_enabled` is
  written by `__sched_core_flip()`.
- `__sched_core_flip()`: for each online core, spins until
  `rq->core->core_pick_in_flight` is zero before it writes `core_enabled`.
  With `sched_core_enabled(rq)` on an online CPU, `pick_next_task()` raises
  the counter and drops it at `out_set_next`.
- `rq_pin_lock()`: also calls `assert_balance_callbacks_empty()`, which warns
  under `CONFIG_PROVE_LOCKING` when `rq->balance_callback` holds anything but
  `balance_push_callback`.
- Guards: there is no guard for `raw_spin_rq_lock_irq()`. The raw guard is
  `raw_spin_rq_lock_irqsave`; `__task_rq_lock` is a guard too. Search
  `kernel/sched/sched.h` for `DEFINE_LOCK_GUARD_1` and `DEFINE_LOCK_GUARD_2`.
- **Potentially unsafe usage**: taking `&rq->__lock` directly instead of
  through a wrapper.
  - Unsafe: when `rq->core_enabled` can be set for `rq`. Other CPUs then
    serialise on `&rq->core->__lock`, which this does not take.
  - Safe: `sched_core_lock()`, which takes the embedded lock of every CPU in
    `cpu_smt_mask()`, the core leader included.
  - Safe: after `sched_core_disabled()` returned true with preemption off, as
    `raw_spin_rq_lock_nested()` does. This pairs with `synchronize_rcu()` in
    `__sched_core_enable()`.
