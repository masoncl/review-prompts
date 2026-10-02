- `LED_BLINK_SW` in the timer callback: not tested; `led_heartbeat_function()`
  and `led_activity_function()` re-arm regardless of it.
- `LED_BLINK_BRIGHTNESS_CHANGE`: the timer callback does
  `test_and_clear_bit()` on it and, if it was set, copies
  `new_blink_brightness` into `blink_brightness` before choosing the level.
- Zero through `led_set_brightness()`: `set_brightness_delayed()` calls
  `led_stop_software_blink()`, which clears `LED_BLINK_SW` and stops only the
  core's `blink_timer`; the trigger's timer keeps running and is not told.
- After that zero: non-zero `led_set_brightness()` calls go straight to
  `led_set_brightness_nosleep()` and a later tick of the trigger's timer
  overwrites them.
- `brightness_store()` in `drivers/leds/led-class.c`: avoids this by calling
  `led_trigger_remove()` before it writes zero.
- `heartbeat_trig_deactivate()` and `activity_deactivate()` clear
  `LED_BLINK_SW` themselves; the `err_add_groups` path of
  `led_trigger_set()` calls `deactivate` without
  `led_stop_software_blink()`.
- **Potentially unsafe usage**: a trigger timer that writes the LED without
  `LED_BLINK_SW` set.
  - Unsafe: when the trigger takes its on level from `blink_brightness`; a
    non-zero `led_set_brightness()` then goes to
    `led_set_brightness_nosleep()`, never sets
    `LED_BLINK_BRIGHTNESS_CHANGE`, and a later tick overwrites the value.
  - Safe: when the trigger computes every level itself and does not use
    `blink_brightness`, as `pattern_trig_timer_common_function()` in
    `drivers/leds/trigger/ledtrig-pattern.c`.
- **Unsafe usage**: calling `led_set_brightness()` from the trigger's own
  timer while `LED_BLINK_SW` is set; non-zero is only recorded in
  `new_blink_brightness` and zero queues `LED_BLINK_DISABLE`.
  - Safe: `led_set_brightness_nosleep()`, as `led_heartbeat_function()` and
    `led_activity_function()` use.
  - Safe: `led_set_brightness()` from a timer whose trigger never sets
    `LED_BLINK_SW`, as `pattern_trig_timer_common_function()`.
