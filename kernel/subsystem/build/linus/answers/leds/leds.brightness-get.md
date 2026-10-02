- `led_update_brightness()`: returns 0 on success, never the brightness; the
  value is only in `led_cdev->brightness`.
- `led_update_brightness()`: takes no lock and has no lockdep assertion.
- `led_classdev_register_ext()`: holds `led_access` around the call; it locks
  the mutex before `device_create_with_groups()` and unlocks at the end.
- Callers outside `drivers/leds/`: take `led_access` themselves if they need
  it, as `uniwill_notify_kbd_led()` does with `guard(mutex)`.
- `brightness_show()`: returns `-ENODATA` without calling the driver when
  `led_trigger_is_hw_controlled()`, that is when the attached trigger has
  `trigger_type` set; without `CONFIG_LEDS_TRIGGERS` that test is always
  false.
- Triggers: no file under `drivers/leds/trigger/` calls
  `led_update_brightness()`.
