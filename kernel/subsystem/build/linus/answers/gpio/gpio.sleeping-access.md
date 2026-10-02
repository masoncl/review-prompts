- Plain value calls on one descriptor: the check is a bare
  `WARN_ON(desc->gdev->can_sleep)`, placed after `VALIDATE_DESC()`. They do
  not call `might_sleep()` or `might_sleep_if()`.
  - The warning fires on every call, not once; it needs `CONFIG_BUG` and no
    debug option.
- `_cansleep` value calls: call `might_sleep()` unconditionally, before
  `VALIDATE_DESC()`, so the context rule applies to a NULL descriptor too.
  - There is no extra_checks in this tree.
  - `might_sleep()` reports only under `CONFIG_DEBUG_ATOMIC_SLEEP`; without it
    `might_sleep()` reports nothing for a `_cansleep` call from atomic
    context.
- `gpiod_cansleep()`: returns `desc->gdev->can_sleep` after `VALIDATE_DESC()`.
  It does not call `gpiod_to_chip()`.
- Choosing per line: `create_gpio_led()` and `gpio_led_set()` in
  `drivers/leds/leds-gpio.c` store `gpiod_cansleep()` at probe and pick the
  call from it.
- Rejecting sleeping lines: `pwm_gpio_probe()` in `drivers/pwm/pwm-gpio.c`
  fails probe when `gpiod_cansleep()` is true.
