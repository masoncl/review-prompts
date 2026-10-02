- `led_set_brightness()` starts no blink of any kind.
- `LED_BLINK_DISABLE`: set only in `led_set_brightness()`;
  `led_set_brightness_nosleep()` and `led_set_brightness_sync()` neither set
  it nor stop a software blink.
- `led_set_brightness_nopm()`: makes no runtime-PM call; what it skips is the
  clamp, the write to `led_cdev->brightness` and the `LED_SUSPENDED` test.
- Triggers in `drivers/leds/trigger/`: several call
  `led_set_brightness_nosleep()` directly, for example
  `led_heartbeat_function()` from its own timer, and so bypass the blink
  handling in `led_set_brightness()`.
- `led_mc_set_brightness()`: defined in `drivers/leds/led-core.c`, declared
  in `include/linux/leds.h`; stores the intensities, then calls
  `led_set_brightness()`.
