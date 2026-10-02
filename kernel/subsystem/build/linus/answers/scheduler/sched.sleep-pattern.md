- `prepare_to_wait()`, `prepare_to_wait_exclusive()` and
  `prepare_to_wait_event()`: call `set_current_state()`, not
  `__set_current_state()`, although they hold `wq_head->lock`.
- Lockless `waitqueue_active()` wakers: rely on that barrier and need their
  own `smp_mb()` after the condition store; `wq_has_sleeper()` in
  `include/linux/wait.h` supplies it.
- **Potentially unsafe usage**: `__set_current_state()` to a sleeping state
  before `schedule()`.
  - Unsafe: when a condition test follows and the waker stores the condition
    without a lock that the sleeper holds across the state store; the store
    can pass the condition load, which the `smp_store_mb()` in
    `set_current_state()` prevents.
  - Safe: the state store is under the lock that the waker holds when it
    stores the condition, as `___down_common()` in
    `kernel/locking/semaphore.c` does under `sem->lock`.
  - Safe: `do_wait_for_common()` in `kernel/sched/completion.c`, under
    `x->wait.lock`, which `complete()` holds across the store and the wake-up.
  - Safe: no condition is tested and `schedule()` is called unconditionally,
    as `schedule_timeout_interruptible()` in `kernel/time/sleep_timeout.c`
    does.
- **Potentially unsafe usage**: a call that can sleep between
  `set_current_state()` and `schedule()`.
  - Unsafe: when the call sleeps on most passes, or no loop tests the
    condition again; the call returns in `TASK_RUNNING`, so the following
    `schedule()` does not block.
  - Safe: the call seldom sleeps and the loop stores the state and tests the
    condition again, so a sleep costs one extra pass; `resolve_symbol()` in
    `kernel/module/main.c`, the condition of a
    `wait_event_interruptible_timeout()`, does so after
    `sched_annotate_sleep()`.
  - Safe: `wait_woken()` with `woken_wake_function()`; the state is stored
    only inside `wait_woken()`, after the caller's condition test.
- `__might_sleep()` warning for that usage: built only with
  `CONFIG_DEBUG_ATOMIC_SLEEP`, and silent once `sched_annotate_sleep()` has
  cleared `current->task_state_change`.
- `TASK_INTERRUPTIBLE` and `TASK_KILLABLE` loops: with a matching signal
  pending, `try_to_block_task()` stores `TASK_RUNNING` and `schedule()` returns
  without sleeping, so the loop needs its own signal exit.
- `___wait_event()`: gets that exit from the return value of
  `prepare_to_wait_event()`.
- Special states: `is_special_task_state()` in `include/linux/sched.h` defines
  the set; besides stopped, traced and dead it holds `TASK_PARKED`,
  `TASK_FROZEN` and `TASK_WAKING`.
- Setter checks under `CONFIG_DEBUG_ATOMIC_SLEEP`: `set_current_state()` and
  `__set_current_state()` warn on a special state; `set_special_state()` warns
  on a normal one.
- `set_special_state()` user: `__kthread_parkme()` in `kernel/kthread.c`
  stores `TASK_PARKED` with it.
