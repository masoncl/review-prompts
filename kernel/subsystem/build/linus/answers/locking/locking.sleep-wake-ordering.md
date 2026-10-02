- `set_current_state()`: `smp_store_mb()` on `current->__state`; it pairs with
  `smp_mb__after_spinlock()` after `p->pi_lock` is taken in
  `try_to_wake_up()` in `kernel/sched/core.c`, which runs before
  `ttwu_state_match()` reads `p->__state`.
- `try_to_wake_up()` with `p == current`: takes no `pi_lock` and executes no
  `smp_mb__after_spinlock()`; it relies on program order.
- The pairing orders only the state against the condition; data stored before
  the condition needs its own `smp_wmb()` and `smp_rmb()` (or release and
  acquire) when the sleeper sees the condition without sleeping; see "SLEEP
  AND WAKE-UP FUNCTIONS" in `Documentation/memory-barriers.txt`.
- `prepare_to_wait()`, `prepare_to_wait_exclusive()`,
  `prepare_to_wait_event()`: call `set_current_state()`, not
  `__set_current_state()`, although they hold `wq_head->lock`; the caller
  tests the condition after the unlock, and an unlock does not stop that load
  moving up.
- **Potentially unsafe usage**: `__set_current_state()` with a sleeping state
  before the condition test.
  - Unsafe: when the condition is tested outside the lock under which the
    state was stored, or the waker changes the condition without that lock.
  - Safe: state store and condition test are in one critical section of a
    lock, and the waker changes the condition under that lock, as
    `___down_common()` and `__up()` do with `sem->lock` in
    `kernel/locking/semaphore.c`; the wakeup may follow the unlock, as in
    `up()`.
  - Safe: no condition, only a timeout, as `schedule_timeout_interruptible()`
    in `kernel/time/sleep_timeout.c`.
- **Potentially unsafe usage**: testing the condition before storing the
  state.
  - Unsafe: when the waker can set the condition and call the wakeup between
    the test and the state store; the wakeup finds `TASK_RUNNING` and is lost.
  - Safe: test and state store are under the lock that the waker holds to
    change the condition, as in `___down_common()`.
  - Safe: the condition is a pending signal and the state is one that
    `signal_pending_state()` honours, as `sigsuspend()` in `kernel/signal.c`;
    `__schedule()` executes `smp_mb__after_spinlock()` after `rq_lock()` and
    `try_to_block_task()` tests `signal_pending_state()` again.
- **Potentially unsafe usage**: a condition test that can block (takes a
  mutex, allocates with `GFP_KERNEL`) between `set_current_state()` and
  `schedule()`.
  - Unsafe: when the call blocks often; it returns in `TASK_RUNNING`, so
    `schedule()` does not block and the loop spins; `__might_sleep()` warns
    under `CONFIG_DEBUG_ATOMIC_SLEEP`.
  - Safe: the block is rare and an extra loop pass is harmless, annotated with
    `sched_annotate_sleep()`, as `resolve_symbol()` in `kernel/module/main.c`.
  - Safe: `wait_woken()` with `woken_wake_function()` in
    `kernel/sched/wait.c`; the condition is tested in `TASK_RUNNING` and
    `WQ_FLAG_WOKEN` carries the wakeup.
