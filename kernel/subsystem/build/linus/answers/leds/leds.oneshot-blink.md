- A request is dropped only when `LED_BLINK_ONESHOT` is set and
  `timer_pending()` is true for `blink_timer`.
- `LED_BLINK_ONESHOT` alone refuses nothing: `led_timer_function()` does not
  clear it when the blink ends.
- `invert`: selects only the resting state, that is which write sets
  `LED_BLINK_ONESHOT_STOP`: the off write when clear, the on write when set.
- First phase: `led_timer_function()` picks it from `led_cdev->brightness`,
  not from `invert`.
- Full cycle: happens only if the LED is in its resting state at the call
  (off for `invert` clear, on for `invert` set).
- LED not in its resting state at the call: the first tick writes the resting
  state and the blink ends with no visible cycle.
