- `call_timer_fn()`: receives the callback as its `fn` argument and reads
  nothing from the timer after the callback returns; see `call_timer_fn()` in
  `kernel/time/timer.c`.
- `expire_timers()`: reads `timer->function` and `timer->flags` under
  `base->lock` before the call, and afterwards does not read the timer.
