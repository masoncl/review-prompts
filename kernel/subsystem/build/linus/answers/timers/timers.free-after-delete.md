- Callback that re-arms its own timer with `mod_timer()`: `timer_delete_sync()`
  is enough; it returns only after the callback has ended and the re-armed
  timer is detached.
- Callback that re-arms with `add_timer_on()` onto a different
  `struct timer_base`: no sync variant covers it; see "Waiting for a running
  callback".
- **Potentially unsafe usage**: `timer_delete_sync()` then `cancel_work_sync()`
  then free, for a timer and a work item that start each other.
  - Unsafe: when nothing stops the work from calling `mod_timer()` between the
    two calls; the timer is then queued in freed memory.
  - Safe: when the teardown has already made the re-arm condition false, as
    `put_unbound_pool()` in `kernel/workqueue.c` does: it destroys all workers
    first, so `too_many_workers()` is false and `idle_cull_fn()` skips
    `mod_timer()`.
  - Safe: `timer_shutdown_sync()` first, then `cancel_work_sync()` or
    `destroy_workqueue()`, as `vc4_bo_cache_destroy()` in
    `drivers/gpu/drm/vc4/vc4_bo.c` does; `__mod_timer()` discards the work's
    re-arm because `timer->function` is NULL.
- `timer_destroy_on_stack()`: only calls `debug_object_free()`, and is empty
  without `CONFIG_DEBUG_OBJECTS_TIMERS`, where it does not dequeue the timer.
- On-stack timer: delete it with `timer_delete_sync()` before
  `timer_destroy_on_stack()`, as `schedule_timeout()` in
  `kernel/time/sleep_timeout.c` does.
- Free of an object that embeds a still-active timer: reported only with both
  `CONFIG_DEBUG_OBJECTS_TIMERS` and `CONFIG_DEBUG_OBJECTS_FREE`;
  `debug_check_no_obj_freed()` is an empty stub without the latter.
