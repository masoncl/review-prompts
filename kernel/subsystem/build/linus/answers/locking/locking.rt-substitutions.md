- `struct rw_semaphore` reader release by another task: works on RT;
  `up_read_non_owner()` in `kernel/locking/rwsem.c` is common to both
  configurations and on RT drops the reader count without an owner test.
- `rwlock_t` and `struct rw_semaphore` readers on RT: several hold the lock
  at once; `rwbase_read_trylock()` in `kernel/locking/rwbase_rt.c` only
  increments a count while `READER_BIAS` is set.
- `struct mutex` and `spinlock_t` waiters on RT: do not always sleep; the top
  waiter spins in `rtmutex_spin_on_owner()` (`kernel/locking/rtmutex.c`,
  `CONFIG_SMP`) while the owner is running on a CPU.
- `struct semaphore`: unchanged on RT, as `raw_spinlock_t` is;
  `kernel/locking/semaphore.c` has no `CONFIG_PREEMPT_RT` branch.
