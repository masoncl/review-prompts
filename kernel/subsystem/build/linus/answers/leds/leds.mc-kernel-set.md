- Signature: `led_mc_set_brightness(led_cdev, intensity_value, num_colors,
  brightness)`; `brightness` is last.
- Return type: `led_mc_set_brightness()` and `led_mc_trigger_event()` both
  return void; a caller cannot detect failure.
- `led_mc_set_brightness()` on a LED without `LED_MULTI_COLOR`:
  `dev_err_once()`, no change, no fallback to `led_set_brightness()`.
- `led_mc_set_brightness()` with wrong `num_colors`: `dev_err_once()`, no
  change to intensities or brightness.
- `led_mc_trigger_event()` on a LED without `LED_MULTI_COLOR`: skips it
  itself, with no log message; only a `num_colors` mismatch reaches the
  `dev_err_once()` in `led_mc_set_brightness()`.
- `led_mc_trigger_event()`: does not blink; it only calls
  `led_mc_set_brightness()` for each LED on `trig->led_cdevs` that has
  `LED_MULTI_COLOR`.
- Clamping: `led_mc_set_brightness()` stores `intensity_value[i]` as given;
  neither `max_intensity` nor `max_brightness` limits it, unlike
  `multi_intensity_store()`.
- `trig->brightness`: not written by `led_mc_trigger_event()`, while
  `led_trigger_event()` writes it.
- LED bound to the trigger after the event: `led_trigger_set()` applies only
  `trig->brightness` unless the trigger has `activate`; a multicolor trigger
  resends the color from `activate`, as
  `power_supply_led_trigger_activate()` in
  `drivers/power/supply/power_supply_leds.c` does.
- **Potentially unsafe usage**: calling `lcdev_to_mccdev()` on a
  `struct led_classdev`.
  - Unsafe: when the LED comes from a list or lookup that can hold plain
    LEDs, such as `trig->led_cdevs`, and `LED_MULTI_COLOR` was not tested;
    the `container_of()` result does not point at a
    `struct led_classdev_mc`.
  - Safe: after testing `led_cdev->flags & LED_MULTI_COLOR`, as
    `led_mc_set_brightness()` in `drivers/leds/led-core.c` does; the flag is
    set only by `led_classdev_multicolor_register_ext()`.
  - Safe: in a callback of the driver that registered the LED with
    `led_classdev_multicolor_register_ext()`, as `lp50xx_brightness_set()`
    in `drivers/leds/leds-lp50xx.c` does; `lp50xx_probe_dt()` installs it
    only on the `led_cdev` member of its `struct led_classdev_mc`.
