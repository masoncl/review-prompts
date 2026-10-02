- Lock held around `play_effect`: `dev->event_lock`; `struct ml_device` has
  no timer_lock field.
- `erase_effect()` in `drivers/input/ff-core.c`: calls `ff->playback`
  directly under `dev->event_lock`, not through `dev->event`, so it reaches
  `play_effect` when `dev->ready` is false or `dev->inhibited` is set.
- `input_ff_event()` path: reached only while `dev->ready` is set
  (`input_event_dispose()`) and `dev->inhibited` is clear
  (`input_get_disposition()`).
- After `input_unregister_device()` returns: the helper no longer calls
  `play_effect` from the timer (see "Memoryless helper timer"), so work
  stopped after that point is not re-queued.
- `play_effect` after `dev->close`: possible on an inhibited device, from the
  timer and from `erase_effect()`.
- Suspend: the helper does not stop the timer, so `play_effect` can queue
  work after the suspend callback has cancelled it.
- `regulator_haptic_suspend()`: does not call `cancel_work_sync()`; it sets
  `haptic->suspended` under `haptic->mutex`, which `regulator_haptic_work()`
  tests.
- `isa1200_suspend()`: when `input_device_enabled()` is true, sets
  `isa->suspended`, which `isa1200_vibrator_play_effect()` tests before
  `schedule_work()`.
- **Potentially unsafe usage**: stopping deferred work only in `dev->close`.
  - Unsafe: when the work uses data freed at unbind and nothing stops the
    work after `input_unregister_device()`; on a device inhibited through
    sysfs the flush at unregister calls `play_effect`, and `dev->close` does
    not run.
  - Safe: stop the work or URBs after `input_unregister_device()` and before
    freeing, as `xpad_disconnect()` does with `xpad_stop_output()`;
    `ml_ff_stop()` has shut the timer down by then.
- **Potentially unsafe usage**: `cancel_work_sync()` before the input device
  is unregistered.
  - Unsafe: when nothing stops `play_effect` from queuing the work again.
  - Safe: set a flag under a lock that the queuing path tests, then cancel,
    as `bigben_remove()` and `bigben_schedule_work()` do.
