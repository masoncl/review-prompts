- Not private to `drivers/leds/led-core.c`:
  `drivers/leds/trigger/ledtrig-heartbeat.c` and
  `drivers/leds/trigger/ledtrig-activity.c` set `LED_BLINK_SW` in activate,
  clear it in deactivate, and consume `LED_BLINK_BRIGHTNESS_CHANGE` in their
  own timer functions.
- `multi_intensity_store()` in `drivers/leds/led-class-multicolor.c` reads
  `LED_BLINK_SW`.
- No file outside `drivers/leds/` touches `work_flags` of
  `struct led_classdev`.
- `LED_BLINK_SW` set: does not mean `blink_timer` is armed; the two triggers
  above run their own timers.
- `LED_BLINK_SW` in the core: set only in `led_set_software_blink()`; cleared
  in `led_stop_software_blink()`, `led_blink_set()` and
  `led_timer_function()`.
- `led_stop_software_blink()`: clears `LED_BLINK_SW` only.
  `LED_BLINK_ONESHOT` is cleared only by `led_blink_set()`.
- `LED_BLINK_ONESHOT` set, which only `led_blink_set_oneshot()` does:
  `led_blink_setup()` skips the driver's `blink_set` and uses software blink.
- `LED_SET_BLINK`: set by `led_blink_set_nosleep()` when the driver has both
  `blink_set` and `brightness_set_blocking`; `set_brightness_delayed()` then
  calls `led_blink_set()`.
- `led_set_brightness_nopm()` deferring 0: clears pending `LED_SET_BRIGHTNESS`
  and `LED_SET_BLINK` before it sets `LED_SET_BRIGHTNESS_OFF`.
- `LED_SET_BRIGHTNESS` setters besides `led_set_brightness_nopm()`:
  `led_set_brightness()` with a non-zero value when a set or a blink disable
  is already pending, and `set_brightness_delayed()` after the off step when
  `delayed_set_value` is not `LED_OFF`.
- One non-atomic write: `led_classdev_register_ext()` stores
  `work_flags = 0`.
