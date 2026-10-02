- `led_classdev_notify_brightness_hw_changed()`: writes
  `brightness_hw_changed`, never `brightness`.
- Drivers write `brightness` at run time too; for example
  `aat1290_led_flash_strobe_set()` zeroes it under the driver's own mutex.
- `led_access`: held by some callers of the three core writers
  (`led_set_brightness_nosleep()`, `led_set_brightness_sync()`,
  `led_update_brightness()`), for example `brightness_store()`,
  `brightness_show()` and `led_classdev_register_ext()`;
  `led_trigger_event()` and `led_timer_function()` do not take it, so it does
  not serialise writes to the field.
- `led_set_brightness()` returns without writing `brightness` when:
  - the value is non-zero and `LED_SET_BRIGHTNESS` or `LED_BLINK_DISABLE` is
    pending: the value goes to `delayed_set_value`;
  - the value is non-zero and `LED_BLINK_SW` is set: the value goes to
    `new_blink_brightness`;
  - the value is 0 and `LED_BLINK_SW` is set: `LED_BLINK_DISABLE` is queued.
- `set_brightness_delayed()`: its `LED_SET_BRIGHTNESS_OFF` and
  `LED_SET_BRIGHTNESS` steps call the driver and do not write `brightness`.
  After the first and third case above the hardware has the new value and the
  field keeps the old one.
- `led_update_brightness()`: stores the `brightness_get` result without
  limiting it to `max_brightness`; `led_classdev_register_ext()` calls it, so
  a driver's initial value is overwritten when `brightness_get` exists and
  returns no error.
- `led_classdev_suspend()`: turns the hardware off through
  `led_set_brightness_nopm()`, which does not write the field;
  `led_classdev_resume()` passes the field back to the same function.
- While `LED_SUSPENDED` is set: `led_set_brightness_nosleep()` and
  `led_set_brightness_sync()` write the field and skip the driver.
