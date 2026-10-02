- Nesting order: `led_access`, then `leds_list_lock` or `triggers_list_lock`,
  then `trigger_lock`, then `leddev_list_lock`.
- `triggers_list_lock` and `leds_list_lock`: the core never takes one while it
  holds the other; `led_trigger_register()` and `led_trigger_unregister()`
  release the first before taking the second.
- `led_access` outside `leds_list_lock`: `led_classdev_register_ext()` holds
  `led_access` while it takes `leds_list_lock` for write and while it calls
  `led_trigger_set_default()`.
- `led_trigger_register()`, `led_trigger_unregister()` and
  `led_trigger_read()`: do not take `led_access`.
- `leddev_list_lock`: a `spinlock_t`, taken with plain `spin_lock()` and only
  in `led_trigger_set()`; walkers of `trig->led_cdevs` do not take it.
- `activate` and `deactivate`: run with `trigger_lock` held for write, plus
  whatever the caller of `led_trigger_set()` holds; any lock a callback takes
  nests inside those.
- `led_trigger_unregister()`: tests `next_trig` with `list_empty_careful()`
  before it takes any lock.
- `led_trigger_panic_notifier()` in `drivers/leds/trigger/ledtrig-panic.c`:
  walks `leds_list`, and `led_trigger_set_panic()` rewrites
  `led_cdev->trigger` and `trig_list`, with no lock and no RCU list
  operation, from the panic notifier only.
