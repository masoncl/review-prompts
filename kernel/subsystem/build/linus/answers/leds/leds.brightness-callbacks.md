- Neither callback set: `led_classdev_register_ext()` makes no test of the
  callbacks and registers the LED.
- Both set: `led_set_brightness_nopm()` and the work handler both use
  `brightness_set`; in the core only `led_set_brightness_sync()` reaches
  `brightness_set_blocking`.
- `brightness_set` from the work item: happens even for a driver that has
  `brightness_set`, because `led_set_brightness()` queues the work itself
  when it stops a software blink or finds a change pending.
- Locks around `brightness_set`: `brightness_store()` holds `led_access`,
  `led_trigger_event()` holds `rcu_read_lock()`, `led_timer_function()` and
  the work item hold no LED lock; no lock is common to all paths.
