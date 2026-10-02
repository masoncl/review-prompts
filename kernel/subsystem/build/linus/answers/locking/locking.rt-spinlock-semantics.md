- `spin_lock_bh()` on RT: calls `local_bh_disable()` and then
  `rt_spin_lock()`; `read_lock_bh()` and `write_lock_bh()` call
  `local_bh_disable()` and then `rt_read_lock()` or `rt_write_lock()`. What
  that excludes is under "Bottom halves and per-CPU data".
- Migration and RCU protection: start only after the lock is acquired;
  `__rt_spin_lock()` calls `rcu_read_lock()` and `migrate_disable()` after
  `rtlock_lock()` returns, so a task blocked on the lock has neither.
- `rt_spin_unlock()`, `rt_read_unlock()`, `rt_write_unlock()`: call
  `rcu_read_unlock()` last, so a lock inside an RCU-freed object stays valid
  until the rtmutex release has finished.
