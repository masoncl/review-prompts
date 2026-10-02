- Formula: `DIV_ROUND_CLOSEST(brightness * intensity,
  led_cdev->max_brightness)`; the result is rounded to nearest, not
  truncated.
- Divisor: always `led_cdev->max_brightness`;
  `led_mc_calc_color_components()` does not read `max_intensity`.
- `intensity` above `max_brightness`: gives a `subled_info[i].brightness`
  above `max_brightness` at full brightness; the helper does not clamp.
- Drivers with hardware global brightness, for example
  `drivers/leds/leds-lp50xx.c`: write `intensity` to the channel register
  directly and have no call to `led_mc_calc_color_components()`.
- Drivers that set a nonzero `max_intensity` (search `.max_intensity =`):
  none of them calls the helper for that LED.
- Callers outside the brightness callback: a driver may call it with a
  brightness of its own choice, for example `LED_FULL` after setting a
  pattern in `drivers/leds/rgb/leds-qcom-lpg.c`, or `cdev->max_brightness`
  in `drivers/leds/leds-turris-omnia.c`.
- Software-scaling example: `led_pwm_mc_set()` in
  `drivers/leds/rgb/leds-pwm-multicolor.c`.
