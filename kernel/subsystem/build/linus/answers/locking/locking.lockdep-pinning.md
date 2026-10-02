- Pin warnings: plain `WARN()`; they do not turn lockdep off and the release
  still happens.
- Wrong cookie: `__lock_unpin_lock()` warns "pin count corrupted" only if the
  cookie is larger than `pin_count`; a smaller wrong cookie leaves the entry
  pinned.
- `__lock_set_class()` and `__lock_downgrade()`: have no pin test;
  `reacquire_held_locks()` carries `pin_count` over.
- Entry that takes the pin: `__lock_pin_lock()` walks the held stack from the
  bottom and pins the first entry that `match_held_lock()` accepts.
- Entry with `references` set: `match_held_lock()` accepts any lock whose
  class equals the class of the entry, so pin, unpin and release of any
  instance of the class all act on that one entry.
- Entries merge only if the top of the held stack has the same class and a
  nest lock is passed; see `__lock_acquire()`.
- **Unsafe usage**: releasing any lock of the class while a held-lock entry
  shared through a nest lock is pinned; `__lock_release()` warns "releasing a
  pinned lock" before it drops `references`.
  - Safe: call `lockdep_unpin_lock()` with the cookie before any instance of
    the class is released, and `lockdep_repin_lock()` after.
  - Safe: pinning a lock that is never taken with a nest lock, so its entry
    matches one instance only, as `rq_pin_lock()` and `rq_unpin_lock()` in
    `kernel/sched/sched.h` do.
- **Unsafe usage**: releasing a lock that sits between two entries of the
  class in the held stack while the upper entry, taken with a nest lock, is
  pinned; `reacquire_held_locks()` merges the upper entry into the lower one
  and the merge path of `__lock_acquire()` drops its `pin_count`.
  - Safe: release in reverse order of acquisition while pinned, so
    `__lock_release()` returns before `reacquire_held_locks()`.
