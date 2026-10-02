- Default: `led_classdev_register_ext()` sets `LED_FULL` when the field is
  zero; `led_init_core()` does not touch it.
- `max-brightness` fwnode property: read in `led_classdev_register_ext()`
  before the zero test, and only when `init_data` and `init_data->fwnode` are
  both set; `led_classdev_register()` passes no `init_data`.
- The property value replaces the driver's value with no comparison, so it
  can be larger than what the driver set.
- No other input: `max-brightness` is the only property that
  `led_classdev_register_ext()` reads into the field.
- Limit: the core limits a brightness to `max_brightness` in two places
  only, the `min()` in `led_set_brightness_nosleep()` and the `min()` in
  `led_set_brightness_sync()`.
- `brightness_store()`: neither rejects nor limits; it passes the parsed
  value to `led_set_brightness()`.
- `led_set_brightness()` with a non-zero value while `LED_SET_BRIGHTNESS` or
  `LED_BLINK_DISABLE` is pending: the value reaches the driver callback from
  `set_brightness_delayed()` without passing either `min()`.
