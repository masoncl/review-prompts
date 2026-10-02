- Read in `led_classdev_register_ext()` when `init_data->fwnode` is set:

  | Property | Effect |
  |---|---|
  | `linux,default-trigger` | replaces `led_cdev->default_trigger` |
  | `retain-state-shutdown` | sets `LED_RETAIN_AT_SHUTDOWN` |
  | `max-brightness` | replaces `led_cdev->max_brightness` |
  | `color` | replaces `led_cdev->color` |

- `led_cdev->color` at or above `LED_COLOR_ID_MAX`: `dev_warn()` only;
  registration continues and the value stays.
- `retain-state-suspended` and `panic-indicator`: not read by the core;
  drivers read them, for example `gpio_leds_create()` in
  `drivers/leds/leds-gpio.c`.
- `led-pattern`: read by `led_get_default_pattern()` in
  `drivers/leds/led-core.c` from the LED class device's node; triggers call
  it from `activate()` while `LED_INIT_DEFAULT_TRIGGER` is set, for example
  `timer_trig_activate()`.
- `trigger-sources`: read by triggers from the LED class device, for example
  `gpio_trig_activate()` and `usbport_trig_port_observed()`; neither core
  registration nor the LED driver parses it.
- `default-brightness`: within `drivers/leds` only
  `led_pwm_default_brightness_get()` in `drivers/leds/leds-pwm.c` reads it,
  for `LEDS_DEFSTATE_ON`.
