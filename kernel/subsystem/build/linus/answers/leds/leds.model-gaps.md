- Models name ledtrig-audio.c and ledtrig_audio_set(). `sound/core/control_led.c`
  does that job and reads the trigger state back with
  `led_trigger_get_brightness()`.
- Models take the usbport trigger to be the only reader of `trigger-sources`.
  `gpio_trig_activate()` returns `-EINVAL` when `gpiod_get_optional()` finds
  no GPIO under that name; `desired_brightness` is the gpio trigger's only
  sysfs file.
- Models do not know that `gpio` and `active_low` of `struct gpio_led` exist
  only under `CONFIG_GPIOLIB_LEGACY`; see `include/linux/leds.h`.
