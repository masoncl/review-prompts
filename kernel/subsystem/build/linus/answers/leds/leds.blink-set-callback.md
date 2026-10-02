- Sleeping: allowed only when the driver also sets `brightness_set_blocking`.
- Without `brightness_set_blocking`: `led_blink_set_nosleep()` calls
  `blink_set` in the caller's context, for example from the timer callback
  `tpt_trig_timer()` in `net/mac80211/led.c` through `led_trigger_blink()`.
- **Unsafe usage**: a `blink_set` that can sleep in a driver that does not
  set `brightness_set_blocking`.
  - Safe: set `brightness_set_blocking` too, as the driver of
    `pca955x_led_blink()` does; the test in `led_blink_set_nosleep()` then
    defers the call to `set_brightness_work`.
  - Safe: a `blink_set` that takes only a spinlock, with `brightness_set`,
    as `bcm6328_blink_set()` in `drivers/leds/leds-bcm6328.c`.
- Delays the hardware cannot match: either adjust them, write them back and
  return 0, or return non-zero; `led_blink_setup()` accepts both, and
  `pca955x_led_blink()` does both.
- Non-zero return: `led_blink_setup()` starts the software blink with the
  delays as the callback left them, so a failing callback must not leave
  values it does not mean.
- Written-back delays: on success the core does not copy them into
  `blink_delay_on` or `blink_delay_off`; they reach only the caller's
  pointers.
- `timer_trig_activate()` in `drivers/leds/trigger/ledtrig-timer.c`: passes
  `&led_cdev->blink_delay_on` and `&led_cdev->blink_delay_off` as the
  pointers, so there the driver writes those fields itself.
- Turning off: the contract covers only an off write (`LED_OFF`) to
  `brightness_set` or `brightness_set_blocking`.
- Non-zero write during a hardware blink: the core passes it to the driver
  and the effect is the driver's choice; for example `bcm6328_led_set()`
  stops the blink for any value.
