- `struct rw_semaphore`: the same requirement as for a mutex. `__up_read()`
  and `__up_write()` in `kernel/locking/rwsem.c` call `rwsem_wake()`, which
  takes `sem->wait_lock`, after the atomic that releases `sem->count`.
- `struct rw_semaphore` on PREEMPT_RT: `rwbase_read_unlock()` takes
  `rtmutex.wait_lock` in `__rwbase_read_unlock()` after the
  `atomic_dec_and_test()` that drops the last reader.
- Where it is stated for rwsems: in
  `Documentation/locking/mutex-design.rst` ("most other sleeping locks like
  rwsems"); `up_read()` and `up_write()` carry no such comment.
- `spinlock_t` on PREEMPT_RT: `rt_spin_unlock()` does not touch the lock after
  releasing it. Its last access is the release cmpxchg or
  `rt_mutex_slowunlock()`, whose comment shows the lock, decrement, unlock,
  `kfree()` pattern it is written to allow.
- `spinlock_t` with debugging: `debug_spin_unlock()` and `spin_release()` run
  before the releasing store; see also the comment in
  `__pv_queued_spin_unlock_slowpath()`, which treats the lock memory as
  possibly freed right after the store.
- `refcount_dec_and_mutex_lock()`, and `kref_put_mutex()` built on it: the
  slow path that returns false calls `mutex_unlock()` after its own
  decrement, so they do not lift the requirement for a mutex that is freed
  with the object.
- Queue that the unlock slow paths of `struct mutex` and
  `struct rw_semaphore` read after the release: `first_waiter`.
