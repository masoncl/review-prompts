- There is no del_timer_sync() here; `timer_delete_sync()` and
  `timer_shutdown_sync()` in `kernel/time/timer.c` stop a timer source.
