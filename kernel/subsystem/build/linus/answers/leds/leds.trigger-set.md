- Removal of the old trigger, in order: `list_del_rcu()` under
  `leddev_list_lock`, `synchronize_rcu()`, `cancel_work_sync()` on
  `set_brightness_work`, `led_stop_software_blink()`,
  `device_remove_groups()`, `deactivate`, clear `trigger`, `trigger_data`,
  `activated` and `LED_INIT_DEFAULT_TRIGGER`, then `led_set_brightness()` to
  `LED_OFF`.
- On removal, `deactivate` runs after the trigger's sysfs groups are gone and
  software blink is stopped, and while `led_cdev->trigger` still points at
  the old trigger.
- Attach, in order: `list_add_tail_rcu()`, set `led_cdev->trigger`,
  `synchronize_rcu()`, `flush_work()`, `activate` (or `led_set_brightness()`
  with `trig->brightness`), `device_add_groups()`, uevent.
- LED is on `trig->led_cdevs` before `activate` runs, so an `activate` that
  calls `led_trigger_event()` reaches its own LED, as
  `power_supply_led_trigger_activate()` does.
- `LED_OFF` on removal is unconditional; there is no LED_KEEP_TRIGGER flag in
  this tree.
- `activated`: `led_trigger_set()` never sets it to true and the error path
  does not write it; a trigger that uses it sets it in its own `activate`, as
  `pattern_trig_activate()` does.
- `trigger_lock`: must be held for write; nothing in `led_trigger_set()`
  asserts it.
- Callers of `led_trigger_set()`: all are in `drivers/leds/led-triggers.c` and
  `drivers/leds/led-class.c`; other code uses `led_trigger_remove()`.
