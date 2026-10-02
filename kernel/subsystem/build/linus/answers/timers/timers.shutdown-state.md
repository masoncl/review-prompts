- `add_timer()`, `add_timer_local()`, `add_timer_global()`, `add_timer_on()` on a
  shut-down timer: return `void`, so the caller gets no indication at all.
- `mod_timer()`, `mod_timer_pending()`, `timer_reduce()` on a shut-down timer:
  return 0.
- Shutdown state: is only `timer->function == NULL`; there is no bit for it in
  `timer->flags`, and the arming paths test nothing else.
- `timer->function == NULL` does not prove a shutdown: a timer set up with a
  NULL callback, as `sock_init_data_uid()` in `net/core/sock.c` does, looks the
  same and has its arming discarded the same way; so does a zeroed
  `struct timer_list` without `CONFIG_DEBUG_OBJECTS_TIMERS`.
- Reading `timer->function` outside `kernel/time/timer.c`: is unlocked;
  shutdown writes it under `base->lock`, which callers cannot take.
