| Helper | Built under | Check when built | Otherwise |
|---|---|---|---|
| `lockdep_assert_held()` | `CONFIG_LOCKDEP` | `WARN_ON()` on every failing call unless the task has a matching held-lock entry, any mode | no run-time check |
| `lockdep_assert_held_write()` | `CONFIG_LOCKDEP` | as above, entry must have `read` 0 | no run-time check |
| `lockdep_assert_held_read()` | `CONFIG_LOCKDEP` | as above, entry must have `read` 1 or 2 | no run-time check |
| `lockdep_assert_not_held()` | `CONFIG_LOCKDEP` | `WARN_ON()` if an entry matches | nothing |
| `lockdep_assert_irqs_disabled()` | `CONFIG_PROVE_LOCKING` | `WARN_ON_ONCE()` if per-CPU `hardirqs_enabled` is set | nothing |
| `lockdep_assert_preemption_disabled()` | `CONFIG_PROVE_LOCKING` | `WARN_ON_ONCE()` if `preempt_count()` is 0 and `hardirqs_enabled` is set; nothing without `CONFIG_PREEMPT_COUNT` | nothing |
| `rwsem_assert_held()` | `CONFIG_LOCKDEP` | `lockdep_assert_held()` | `rwsem_assert_held_nolockdep()`: `WARN_ON()` if nobody holds it |
| `assert_spin_locked()` | every build | `BUG_ON()` if nobody holds it | nothing on UP without `CONFIG_DEBUG_SPINLOCK` |

- `CONFIG_LOCKDEP` without `CONFIG_PROVE_LOCKING` (for example
  `CONFIG_LOCK_STAT` alone): the held asserts check, the irq and preemption
  asserts are empty.
- `lockdep_assert_held()`, `lockdep_assert_held_write()` and
  `lockdep_assert_held_read()`: also expand `__assume_ctx_lock()` or
  `__assume_shared_ctx_lock()` in both builds, which tells the compiler's
  context analysis to assume the lock is held; see
  `include/linux/compiler-context-analysis.h`.
- `lockdep_assert_not_held()` and `lockdep_assert_held_once()`: do not expand
  `__assume_ctx_lock()`.
- Held-lock entry shared through a nest lock: `match_held_lock()` matches by
  class, so `lockdep_assert_held()` passes for any lock of that class, held or
  not.
