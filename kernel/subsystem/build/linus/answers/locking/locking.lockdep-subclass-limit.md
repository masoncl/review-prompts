- `spin_lock_nested()` or `mutex_lock_nested()` with a subclass of
  `MAX_LOCKDEP_SUBCLASSES` or more: `__lock_acquire()` hits
  `DEBUG_LOCKS_WARN_ON(subclass >= MAX_LOCKDEP_SUBCLASSES)` and returns before
  any class lookup.
- Log text on that path: the `DEBUG_LOCKS_WARN_ON()` warning, not "BUG:
  looking up invalid subclass".
- `DEBUG_LOCKS_WARN_ON()`: calls `debug_locks_off()`, so lockdep is off for
  the whole system from then on.
- "BUG: looking up invalid subclass": printed by `look_up_lock_class()`, which
  is reached with an unchecked subclass from `lockdep_init_map_type()` (for
  example `lockdep_set_subclass()`), `__lock_set_class()` and
  `verify_lock_unused()`.
- Without `CONFIG_DEBUG_LOCK_ALLOC`: the variants that end in _nested drop the
  subclass, so an out-of-range value is never seen; see
  `include/linux/spinlock.h` and `include/linux/mutex.h`.
