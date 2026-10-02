- Reports that end validation: those that call `debug_locks_off()`, which
  includes every `DEBUG_LOCKS_WARN_ON()` and every table overflow.
- Reports that leave lockdep on: the held asserts (`WARN_ON()`), the pin
  warnings and `lockdep_rcu_suspicious()`; the first two can repeat,
  `RCU_LOCKDEP_WARN()` reports once per call site.
- After `debug_locks` is 0: `lock_acquire()` and `lock_release()` return at
  once, so the held-lock stack is frozen, not maintained.
- After `debug_locks` is 0: `lockdep_hardirqs_on()` and
  `lockdep_hardirqs_off()` return at once too, so irq state is no longer
  tracked.
- `rwsem_assert_held()` in a lockdep build after `debug_locks` is 0: checks
  nothing; it does not fall back to the count test.

| Call | Switched off | Still done |
|---|---|---|
| `lockdep_off()` | acquire, release, pin and softirq tracking for the task; held asserts pass; RCU lockdep checks | hardirq tracking, `lockdep_assert_irqs_disabled()`, `lockdep_assert_preemption_disabled()`, the NMI test in `verify_lock_unused()` |
| `lockdep_set_novalidate_class()` | dependency edges, recursion check, irq usage bits | held-stack entry, `check_wait_context()`, nest-lock test, unlock balance, held asserts |
| `lockdep_set_notrack_class()` | everything in `__lock_acquire()` and `lock_release()` | nothing; `lockdep_assert_held()` on the lock warns |

- `lockdep_off()`: raises `current->lockdep_recursion`, which stays with the
  task; the irq asserts test the per-CPU `lockdep_recursion` instead.
- `lockdep_set_notrack_class()`: has no caller in this tree.
- `lockdep_set_notrack_class()` on a lock the task holds: `lock_release()`
  returns early on the new key, so the held-stack entry is never removed.
- Class change on a held lock: use `lock_set_class()`, or
  `lock_set_novalidate_class()` as `device_lock_reset_class()` in
  `include/linux/device.h` does.
- **Unsafe usage**: a lock acquired on one side of `lockdep_off()` or
  `lockdep_on()` and released on the other.
  - Unsafe: acquired inside and released outside, `__lock_release()` finds no
    entry and reports "bad unlock balance detected".
  - Unsafe: acquired outside and released inside, the entry stays on the held
    stack.
  - Safe: acquire and release both inside the region, as `start_report()` and
    `end_report()` in `mm/kasan/report.c` do with `report_lock`;
    `lock_acquire()` and `lock_release()` both test `lockdep_enabled()`.
