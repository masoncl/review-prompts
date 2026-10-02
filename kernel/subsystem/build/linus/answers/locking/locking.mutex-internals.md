- Waiter queue: a circular list through the `list` member of each
  `struct mutex_waiter`, with no list head. `first_waiter` is the front, the
  entry before it is the tail, and NULL means no waiters.
- Queue helpers: `__mutex_add_waiter()` takes a `pos` waiter instead of a list
  head (NULL means tail) and moves `first_waiter` when inserting before the
  front. See also `__ww_waiter_next()` in `kernel/locking/ww_mutex.h`, which
  ends the walk when it comes back round to `first_waiter`.
- `MUTEX_FLAG_WAITERS`: set by `__mutex_add_waiter()` only when the queue goes
  from empty to one waiter.
- `__mutex_remove_waiter()`: when the last waiter leaves, clears all of
  `MUTEX_FLAGS`, not only `MUTEX_FLAG_WAITERS`.
- Fast path (`__mutex_trylock_fast()`, `__mutex_unlock_fast()`): compiled out
  by `CONFIG_DEBUG_LOCK_ALLOC`, not by `CONFIG_DEBUG_MUTEXES`. With
  `CONFIG_DEBUG_MUTEXES` alone the fast path is built.
- `CONFIG_MUTEX_SPIN_ON_OWNER`: `depends on SMP && ARCH_SUPPORTS_ATOMIC_RMW` in
  `kernel/Kconfig.locks`; it does not depend on `CONFIG_DEBUG_MUTEXES`, so
  debug kernels spin too.
- Handoff without `MUTEX_FLAG_HANDOFF`: `__mutex_unlock_slowpath()` takes the
  handoff path whenever `sched_proxy_exec()` is true and
  `current->blocked_donor` is set (`CONFIG_SCHED_PROXY_EXEC`).
- Handoff target: `current->blocked_donor` if that task is blocked on this
  mutex, otherwise the task of `first_waiter`. The task named with
  `MUTEX_FLAG_PICKUP` is therefore not always the first waiter.
- `__mutex_handoff()` with a NULL task: an ordinary release that keeps
  `MUTEX_FLAG_WAITERS`; this happens on the forced path when nobody waits.
- Per-task tracking: `__mutex_lock_common()` records the mutex in
  `current->blocked_on` with `__set_task_blocked_on()`, under
  `current->blocked_lock` taken inside `wait_lock`.
  `__mutex_unlock_slowpath()` clears it for the task it wakes.
- First-waiter spin: `__mutex_lock_common()` clears `blocked_on` and drops both
  locks before `mutex_optimistic_spin()`, then sets it again afterwards.
