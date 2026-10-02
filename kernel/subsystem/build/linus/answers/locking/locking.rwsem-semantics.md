- New reader with a writer queued, in `rwsem_down_read_slowpath()`: it queues
  only if `count` has `RWSEM_WRITER_LOCKED` or `RWSEM_FLAG_HANDOFF`, or the
  lock is reader-owned with another reader counted. Otherwise it takes the
  lock ahead of the queued writer.
- Read recursion follows from that: the second `down_read()` sees
  `RWSEM_FLAG_WAITERS`, `RWSEM_READER_OWNED` and its own first count, so it
  queues behind the writer.
- Readers do not spin: only `rwsem_down_write_slowpath()` calls
  `rwsem_optimistic_spin()`.
- `rwsem_mark_wake()` with a reader at the head: grants the lock to readers
  anywhere in the queue, skipping writers, up to `MAX_READERS_WAKEUP`; a
  reader queued behind a writer gets the lock before that writer.
- `down_read_non_owner()` and `up_read_non_owner()`: functions only under
  `CONFIG_DEBUG_LOCK_ALLOC`; otherwise macros for `down_read()` and
  `up_read()` in `include/linux/rwsem.h`.
- Read lock released by another task: reported only by lockdep, in
  `lock_release()`. `CONFIG_DEBUG_RWSEMS` in `__up_read()` tests that the lock
  is reader-owned, not which task calls.
- PREEMPT_RT, `__rwbase_read_lock()` in `kernel/locking/rwbase_rt.c`: every
  reader that misses the fast path goes through the rtmutex slow lock and
  waits for the writer that owns it. The header comment of that file (step 3,
  "not writer fair") does not match the body.
- PREEMPT_RT, effect: once a writer owns the rtmutex and has removed
  `READER_BIAS`, `down_read_trylock()` fails and new readers wait until that
  writer releases the rtmutex.
- PREEMPT_RT read recursion: deadlocks the same way; the second read blocks on
  the rtmutex while the writer waits for the first read to end.
- PREEMPT_RT priority inheritance: a reader blocked on the rtmutex boosts the
  writer that owns it, through `task_blocks_on_rt_mutex()`; a writer waiting
  for readers to drain boosts nobody.
- PREEMPT_RT spinning: there is no handoff bit, but the top waiter on the
  rtmutex spins on a running owner in `rtmutex_spin_on_owner()` under
  `CONFIG_SMP`.
