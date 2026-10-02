- `led_access`: the lock held, from just before
  `device_create_with_groups()` until after `led_trigger_set_default()`.
- `leds_list_lock`: write-held only around the `list_add_tail()` onto
  `leds_list`, not across the default-trigger step.
- Order after device creation in `led_classdev_register_ext()`:
  1. `device_set_node()`, when `init_data->fwnode` is set
  2. `led_add_brightness_hw_changed()`, when `LED_BRIGHT_HW_CHANGED` is set
  3. `work_flags = 0`, `init_rwsem()` on `trigger_lock` (under
     `CONFIG_LEDS_TRIGGERS`), `brightness_hw_changed = -1` (under
     `CONFIG_LEDS_BRIGHTNESS_HW_CHANGED`)
  4. `max_brightness` default
  5. `led_update_brightness()`
  6. `wq = leds_wq`, `led_init_core()`
  7. list add
  8. `led_trigger_set_default()`
- List add comes after `led_init_core()`: a trigger attaching from another
  task through `led_trigger_register()` can reach the LED only after
  `brightness_get()` has run and the work item and timer exist.
- `led_trigger_register()` attach: takes `trigger_lock`, not `led_access`, so
  it can run between the list add and the unlock at the end.
- `max_brightness_show()`: takes `led_access`, so it blocks until
  registration ends, like `brightness_store()`.
- Handlers that do not wait for `led_access`: `led_trigger_read()`,
  `brightness_hw_changed_show()`, and the `led_trigger_is_hw_controlled()`
  test at the top of `brightness_show()`.
- `led_trigger_set_default()` call: compiled only under
  `CONFIG_LEDS_TRIGGERS`; it returns at once when `default_trigger` is NULL.
