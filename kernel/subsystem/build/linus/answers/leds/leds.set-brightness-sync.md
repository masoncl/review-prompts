- Blink test: reads `blink_delay_on` and `blink_delay_off`, not
  `LED_BLINK_SW`.
- Order: blink test, write to `led_cdev->brightness`, `LED_SUSPENDED` test,
  callback.
- Suspended and blinking: `-EBUSY`, and `led_cdev->brightness` is not
  written.
- Suspended with no `brightness_set_blocking`: 0.
- After a one-shot blink has finished: still `-EBUSY`, because
  `led_timer_function()` clears `LED_BLINK_SW` and leaves the delay fields;
  `led_stop_software_blink()` zeroes them.
- `drivers/leds/trigger/ledtrig-timer.c` and
  `drivers/leds/trigger/ledtrig-oneshot.c`: write the delay fields directly
  from sysfs, so `-EBUSY` can be returned with no timer running.
- Hardware blink started through `led_blink_set_nosleep()`: the delays are
  passed by value and not written to `blink_delay_on` or `blink_delay_off`,
  so this alone does not cause `-EBUSY`.
