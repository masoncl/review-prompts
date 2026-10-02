- `CONFIG_DEBUG_MUTEXES` by itself: of the rules listed in
  `Documentation/locking/mutex-design.rst` it checks only initialisation
  through the API (`lock->magic`) and owner-only unlock, which also catches a
  second unlock. The sentence there that the option fully enforces the list
  does not hold; the option can be set without lockdep.
- Owner at unlock: `MUTEX_WARN_ON(__owner_task(owner) != current)` in
  `__mutex_unlock_slowpath()` and `__mutex_handoff()` in
  `kernel/locking/mutex.c`.
- `debug_mutex_unlock()` in `kernel/locking/mutex-debug.c`: tests only
  `lock->magic`, and runs only when the unlock goes on to take `wait_lock`.
- Held mutex reinitialised: `mutex_init_lockdep()` calls
  `debug_check_no_locks_freed()`, under `CONFIG_DEBUG_LOCK_ALLOC`;
  `debug_mutex_init()` only sets `lock->magic`.
- Recursive locking: reported by `check_deadlock()` in
  `kernel/locking/lockdep.c`, which needs `CONFIG_PROVE_LOCKING`; on non-RT
  `CONFIG_DEBUG_LOCK_ALLOC` alone does not report it.
- Exit with a mutex held, and freeing memory that holds one:
  `debug_check_no_locks_held()` and `debug_check_no_locks_freed()` are lockdep
  functions, empty stubs without `CONFIG_LOCKDEP` in
  `include/linux/debug_locks.h`; nothing under `CONFIG_DEBUG_MUTEXES` checks
  either.
- One holder at a time: enforced in every configuration; on non-RT by the
  cmpxchg on `owner`.
- `mutex_trylock()` in interrupt context: `check_wait_context()` returns early
  for a trylock, and the non-RT `mutex_trylock()` tests only `lock->magic`.
- PREEMPT_RT: `CONFIG_DEBUG_MUTEXES` depends on `!PREEMPT_RT` and
  `struct mutex` has no `magic` member; the owner check is
  `debug_rt_mutex_unlock()` under `CONFIG_DEBUG_RT_MUTEXES`.
- PREEMPT_RT `mutex_trylock()` in `kernel/locking/rtmutex_api.c`: under
  `CONFIG_DEBUG_RT_MUTEXES` it warns when `in_task()` is false and returns 0.
