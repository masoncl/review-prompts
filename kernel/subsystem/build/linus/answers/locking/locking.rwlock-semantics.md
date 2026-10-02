- Lockdep and `read_lock()`: `rwlock_acquire_read()` records a recursive
  read only when `read_lock_is_recursive()` is true. With
  `CONFIG_QUEUED_RWLOCKS` a process-context `read_lock()` is a non-recursive
  read, so `check_deadlock()` reports a nested one under
  `CONFIG_PROVE_LOCKING`.
- `in_interrupt()` is also true in a BH-disabled section, so `read_lock_bh()`
  and a `read_lock()` under `local_bh_disable()` take the non-queueing path in
  `queued_read_lock_slowpath()` and count as recursive for lockdep.
- `read_lock_irq()` and `read_lock_irqsave()` in process context:
  `in_interrupt()` is false, so they queue behind a waiting writer like a
  plain `read_lock()`.
- `queued_read_trylock()`: fails on any bit of `_QW_WMASK`, a waiting writer
  included, and has no `in_interrupt()` exception.
- PREEMPT_RT read recursion: not safe. `rt_read_lock()` uses the same
  `rwbase_read_lock()` as described under "Reader-writer semaphores", so a
  second read blocks once a writer owns the rtmutex and has removed
  `READER_BIAS`.
- PREEMPT_RT and lockdep: `CONFIG_QUEUED_RWLOCKS` depends on `!PREEMPT_RT`, so
  `read_lock_is_recursive()` is always true and lockdep records every
  `rt_read_lock()` as a recursive read. It does not report a nested read
  there, although the lock can deadlock on one.
