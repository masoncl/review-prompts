- `struct hrtimer` has no `state` field; the queued state is the bool
  `is_queued`, next to `is_rel`, `is_soft`, `is_hard` and `is_lazy`.
- `hrtimer_is_queued()`: `READ_ONCE(timer->is_queued)`, nothing else.
- `HRTIMER_STATE_ENQUEUED` and `HRTIMER_STATE_INACTIVE`: defined as `true`
  and `false` inside `kernel/time/hrtimer.c` only; code outside cannot use
  them and cannot mask `is_queued` with them.
- `hrtimer_is_queued()` and the callback: independent; it returns false
  while the callback runs, and true while the callback runs if the timer was
  started again meanwhile.
- **Potentially unsafe usage**: acting on `hrtimer_is_queued()` without a
  lock that serialises starts and cancels.
  - Unsafe: when the timer can expire or be started on another CPU, or the
    callback can be running; the value is stale on return.
  - Safe: for a timer that is only started on the local CPU with
    `HRTIMER_MODE_PINNED` and `HRTIMER_MODE_HARD`, tested with interrupts
    disabled on that CPU, as `hrtick_schedule_exit()` in
    `kernel/sched/core.c` does; the callback cannot run then.
