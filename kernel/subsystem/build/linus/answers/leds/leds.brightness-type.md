- Driver callbacks: `brightness_set` and `brightness_set_blocking` take
  `enum led_brightness`; `brightness_get` returns it. The core set functions,
  for example `led_set_brightness()`, take `unsigned int`.
- Trigger API is still enum-typed: `led_trigger_event()`,
  `led_mc_trigger_event()`, the `brightness` member of `struct led_trigger`,
  `led_trigger_get_brightness()`; also `led_mc_calc_color_components()`.
- `led_classdev_notify_brightness_hw_changed()`: takes `unsigned int`; its
  stub without `CONFIG_LEDS_BRIGHTNESS_HW_CHANGED` takes
  `enum led_brightness`.
- Values above `LED_FULL` pass through the enum-typed parameters:
  `max_brightness` can exceed 255, for example `0xfff` in
  `drivers/leds/leds-dac124s085.c`.
- `enum led_brightness` status: marked only by the comment "obsolete/useless"
  above its definition; no attribute or build check enforces anything.
- `drivers/leds/TODO`: says "Get rid of it, or make it into typedef or
  something"; it names no replacement type.
- `LED_FULL` in the core: still the default `max_brightness`, and triggers
  pass it to mean "on", for example `led_panic_blink()`.
- `LED_FULL` through `led_set_brightness()`: limited to `max_brightness` when
  that is below 255; when it is above 255 the LED gets 255, not full.
- `defon_trig_activate()` in `drivers/leds/trigger/ledtrig-default-on.c`:
  passes `led_cdev->max_brightness` to `led_set_brightness_nosleep()`; it does
  not call `led_trigger_event()`.
