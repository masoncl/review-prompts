- `struct rt_mutex_base` (`include/linux/rtmutex.h`): the priority-inheritance
  lock core. `struct rt_mutex` is only `struct rt_mutex_base` plus a
  `struct lockdep_map`.
- Under `CONFIG_PREEMPT_RT`, `spinlock_t` and `struct mutex` embed
  `struct rt_mutex_base` directly, not `struct rt_mutex`. Of the lock types
  substituted on RT, only `struct ww_mutex` wraps `struct rt_mutex`.
- `struct futex_pi_state` in `kernel/futex/futex.h`: embeds
  `struct rt_mutex_base` directly too, with or without `CONFIG_PREEMPT_RT`.
- `struct rwbase_rt` (`include/linux/rwbase_rt.h`): a reader count plus a
  `struct rt_mutex_base`. Under `CONFIG_PREEMPT_RT` both `rwlock_t` and
  `struct rw_semaphore` are built on it.
- Waiter queues of non-RT `struct mutex`, non-RT `struct rw_semaphore` and
  `struct semaphore`: the lock holds only a `first_waiter` pointer. There is
  no list head in the lock (no `wait_list` member); the waiters' `list`
  members form a ring.
  - A sole waiter has an empty `list`; `__mutex_remove_waiter()` and
    `__rwsem_del_waiter()` use `list_empty(&waiter->list)` to mean "last
    waiter".
  - A walk ends when it reaches `first_waiter` again; see
    `__ww_waiter_next()` in `kernel/locking/ww_mutex.h` and `next_waiter()`
    in `kernel/locking/rwsem.c`.
- `blocked_on` in `struct task_struct`: the `struct mutex` the task is
  waiting for. `__mutex_lock_common()` sets it on every non-RT build, not
  only with `CONFIG_SCHED_PROXY_EXEC`.
- `blocked_lock` in `struct task_struct`: the `raw_spinlock_t` that
  serialises `blocked_on`. `__mutex_lock_common()` takes it inside the
  mutex's `wait_lock`.
- `blocked_donor` in `struct task_struct`: back link from a mutex owner to
  the task blocked on that mutex in the chain that `find_proxy_task()`
  followed; set by `find_proxy_task()` in `kernel/sched/core.c`. When
  `sched_proxy_exec()` is true and it is set, `__mutex_unlock_slowpath()`
  forces a handoff and prefers the donor over `first_waiter` if the donor is
  blocked on this mutex.
- `blocker` in `struct task_struct` (`CONFIG_DETECT_HUNG_TASK_BLOCKER`): the
  address of the mutex, semaphore or rwsem the task sleeps on, with the kind
  in the low two bits; see `include/linux/hung_task.h`.
- `struct semaphore`: `last_holder` under `CONFIG_DETECT_HUNG_TASK_BLOCKER`
  is a debugging hint, not an owner.
- `struct lockdep_map`: not in every lock. `struct semaphore` and
  `struct rt_mutex_base` have none, and `kernel/locking/semaphore.c` makes no
  lockdep call; only the semaphore's inner `raw_spinlock_t` is tracked. In
  `raw_spinlock_t`, `spinlock_t`, `rwlock_t`, `struct mutex`,
  `struct rw_semaphore` and `struct rt_mutex`, `dep_map` exists only under
  `CONFIG_DEBUG_LOCK_ALLOC`.
- `context_lock_struct()` (`include/linux/compiler-context-analysis.h`):
  defines the lock types, for example `context_lock_struct(mutex)` in
  `include/linux/mutex_types.h`. A search under `include/` for the plain
  struct definition of `struct mutex`, `struct rw_semaphore`, `spinlock_t`,
  `raw_spinlock_t`, `rwlock_t`, `seqlock_t`, `local_lock_t` or
  `struct ww_mutex` finds nothing.
- `struct semaphore`, `struct percpu_rw_semaphore` and
  `struct rt_mutex_base`: not declared with `context_lock_struct()`.
- `__guarded_by()`: ties a member to the lock that protects it, for example
  `first_waiter` to `wait_lock` in `struct mutex`.
- `scoped_guard (raw_spinlock_init, &lock->wait_lock)` in
  `__mutex_init_generic()`: `raw_spinlock_init` is a guard class that
  initialises the lock; this is initialisation, not a critical section.
- `struct percpu_rw_semaphore`: `block` gives writer-writer exclusion and
  stops new readers; blocked readers and writers both queue on `waiters`;
  `writer` is where the one writer that holds `block` waits for readers to
  drain.
- `rqspinlock_t` (`include/asm-generic/rqspinlock.h`,
  `kernel/bpf/rqspinlock.c`): a spinlock outside `kernel/locking/` whose
  `res_spin_lock()` returns `int`. Under `CONFIG_QUEUED_SPINLOCKS` it reuses
  `struct qnode` and `_Q_MAX_NODES` from `kernel/locking/qspinlock.h` with
  its own per-CPU `rqnodes` array.
