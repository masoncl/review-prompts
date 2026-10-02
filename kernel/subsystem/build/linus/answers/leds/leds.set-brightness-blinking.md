- Zero while `LED_BLINK_SW` is set: `led_set_brightness()` only sets
  `LED_BLINK_DISABLE` and queues `set_brightness_work`; the timer is stopped
  and the off value written later, in `set_brightness_delayed()`.
- Non-zero while `LED_BLINK_SW` is set: the value goes to
  `new_blink_brightness` with `LED_BLINK_BRIGHTNESS_CHANGE`;
  `led_set_brightness()` does not write `blink_brightness` or the hardware.
- Blink run by `blink_timer`: the recorded value reaches the hardware only in
  the off-to-on branch of `led_timer_function()`, not at the next tick if the
  LED is on.
- Blink that ends first, for example a one-shot at rest: the value is not
  written when the blink ends, and `LED_BLINK_BRIGHTNESS_CHANGE` stays set
  for the next blink's first off-to-on tick.
- Non-zero while `LED_BLINK_DISABLE` or `LED_SET_BRIGHTNESS` is pending: this
  test comes before the `LED_BLINK_SW` test; the value goes to
  `delayed_set_value` with `LED_SET_BRIGHTNESS` and the work is queued.
