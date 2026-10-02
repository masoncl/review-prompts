| Form | What this tree does |
|---|---|
| `read_seqcount_begin()` | Ordering comes from `smp_load_acquire()` in `seqprop_sequence()`, not from `smp_rmb()`; `smp_rmb()` is on the retry side, in `do_read_seqcount_retry()`. |
| `raw_read_seqcount_begin()` | Is `__read_seqcount_begin()`: waits for even, has the acquire load. Differs from `read_seqcount_begin()` only by `seqcount_lockdep_reader_access()`, which exists under `CONFIG_DEBUG_LOCK_ALLOC`. Used in ordinary code, for example `hrtimer_active()`. |
| `raw_read_seqcount()` | Returns the count as read, possibly odd. On PREEMPT_RT with a spinlock, rwlock or mutex type it first locks and unlocks the associated lock when the count is odd, so it can block. |
| `raw_seqcount_try_begin()` | Is `raw_read_seqcount()` plus the odd test, so it has the same PREEMPT_RT lock wait before it returns false. |
| `scoped_seqlock_read()` | First pass is always lockless. Target `ss_lockless`: retries lockless without bound. Target `ss_lock` or `ss_lock_irqsave`: one more pass under `sl->lock`, then done. |

- `__read_seqcount_retry()`: the only non-latch read form without a barrier;
  `__read_seqcount_begin()` has the same ordering as the other begin forms.
- Odd value from `raw_read_seqcount()`: passed unchanged to
  `read_seqcount_retry()` it validates a section that ran inside a write
  section; `raw_seqcount_begin()` clears bit 0 so the retry fails.
- `scoped_seqlock_read()` body left with `break`: the lock is released by
  `__scoped_seqlock_cleanup()`, but `read_seqretry()` is not run, so a
  lockless pass is not validated.
- `afs_lookup_volume_rcu()` in `fs/afs/callback.c` leaves that way, after it
  has taken a reference on the volume it found.
- `scoped_seqlock_read()` target `ss_done`: calls
  `__scoped_seqlock_invalid_target()`, which is declared in
  `include/linux/seqlock.h` and defined nowhere.
