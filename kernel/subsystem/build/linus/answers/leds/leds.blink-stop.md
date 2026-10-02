- `led_stop_software_blink()`: declared in `drivers/leds/leds.h`, not in
  `include/linux/leds.h`.
- `led_stop_software_blink()`: leaves `LED_BLINK_ONESHOT` and
  `LED_BLINK_ONESHOT_STOP` as they are.
- `led_stop_software_blink()` context: the `timer_delete_sync()` limits given
  under "Blink functions" apply.
- `led_blink_set()`: does not call `led_stop_software_blink()`; it calls
  `timer_delete_sync()` itself and does not zero `blink_delay_on` and
  `blink_delay_off`.
- `led_set_brightness_sync()`: stops no software blink; it returns `-EBUSY`
  when either `blink_delay_on` or `blink_delay_off` is non-zero and never
  touches `blink_timer`.
- `led_set_brightness_sync()` and a hardware blink started by the timer
  trigger: also `-EBUSY` when either field is non-zero, because
  `timer_trig_activate()` passes those two fields as the pointers and the
  driver's written-back delays land there.
- **Potentially unsafe usage**: writing the LED past `led_set_brightness()`,
  with `led_set_brightness_nosleep()` or the driver's `brightness_set`.
  - Unsafe: while `LED_BLINK_SW` is set and the caller is not the timer that
    implements the blink; `blink_timer` or the trigger's own timer stays
    armed and a later tick overwrites the write.
  - Unsafe: a direct `brightness_set` call during a software blink also
    leaves `led_cdev->brightness` stale, and `led_timer_function()` picks
    its next phase from that field.
  - Safe: from the timer that implements the blink, as
    `led_timer_function()` and `led_heartbeat_function()` do with
    `led_set_brightness_nosleep()`.
  - Safe: after `led_classdev_unregister()` has returned, as
    `rt2x00leds_unregister_led()` does with `brightness_set`;
    `led_classdev_unregister()` has called `led_stop_software_blink()`.
