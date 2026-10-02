- `trigger`: created only with `CONFIG_LEDS_TRIGGERS`; a binary attribute
  handled by `led_trigger_read()` and `led_trigger_write()` in
  `drivers/leds/led-triggers.c`; `drivers/leds/` defines no `trigger_show()`
  or `trigger_store()`, and `led_trigger_group` is defined in
  `drivers/leds/led-class.c`.
- `brightness_show()`: with `CONFIG_LEDS_TRIGGERS`, takes
  `led_cdev->trigger_lock` for read inside `led_trigger_is_hw_controlled()`,
  drops it, then takes `led_access` around `led_update_brightness()`.
- `brightness_show()` with a trigger attached whose `trigger_type` is set
  (an LED-private trigger): returns `-ENODATA` and never calls
  `brightness_get`.
- `brightness_store()` and `led_trigger_write()` with `LED_SYSFS_DISABLE` set:
  return `-EBUSY`, tested under `led_access` before the input is parsed.
- `led_trigger_write()` with "none" or "default": goes through
  `led_trigger_remove()` or `led_trigger_set_default()`, still under
  `led_access`; only a named trigger takes `triggers_list_lock` in
  `led_trigger_write()` itself.
- Write of 0 to `brightness`: calls `led_trigger_remove()` for any attached
  trigger; a non-zero write never touches the trigger.
- Write of 0 with a trigger attached: `led_trigger_set()` stops the software
  blink synchronously (`cancel_work_sync()`, `led_stop_software_blink()`,
  then the trigger's `deactivate`) before `led_set_brightness()` runs.
- Write of 0 with no trigger attached and `LED_BLINK_SW` set (blink started
  by `led_blink_set()` from kernel code): `led_set_brightness()` sets
  `LED_BLINK_DISABLE` and queues `set_brightness_work`; the blink stops in
  the work item.
- `brightness_store()`: does not call `led_stop_software_blink()` itself
  (only through `led_trigger_remove()`) and does not call `flush_work()`;
  with a `brightness_set_blocking` driver the write can return before the
  hardware has changed.
- Hardware blink (driver `blink_set` succeeded): `LED_BLINK_SW` is not set, so
  `led_set_brightness()` passes every value to the driver; stopping the blink
  on 0 is the driver's job, see the comment at `blink_set` in
  `include/linux/leds.h`.
- Without `CONFIG_LEDS_TRIGGERS`: `led_trigger_remove()` is an empty inline in
  `include/linux/leds.h`.
