- `delayed_work_timer_fn()`: has no check of the disable count; it calls
  `__queue_work()` directly.
- What keeps a disabled delayed item from running: `try_to_grab_pending()`
  with `WORK_CANCEL_DELAYED` deletes the armed timer, or steals the item once
  the handler has queued it, before the count is raised.
