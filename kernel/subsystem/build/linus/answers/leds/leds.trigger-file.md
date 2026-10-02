- Declaration: `BIN_ATTR()` in `drivers/leds/led-class.c`, giving
  `bin_attr_trigger`; the LED class defines no `dev_attr_trigger`.
- Name matching: `sysfs_streq()`, for none, default and trigger names alike.
- Return value of `led_trigger_set()`: ignored by `led_trigger_write()`; the
  write returns `count` even when `activate` failed and the LED was left with
  no trigger.
- `none` and `default`: handled before the list walk, so a registered trigger
  with either name cannot be selected.
- `none` with no trigger attached: nothing changes, brightness included.
- `default` with `default_trigger` NULL: nothing changes; the write returns
  `count`.
- `default` when the named trigger is not registered: the current trigger
  stays attached, a module load is requested, and the write returns `count`.
- Read listing: " default" follows none when `led_cdev->default_trigger` is
  non-NULL; it is never bracketed.
- `led_trigger_read()`: takes `triggers_list_lock` then `trigger_lock`, both
  for read, and does not test `led_sysfs_is_disabled()`.
