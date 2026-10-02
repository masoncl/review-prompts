- `led_classdev_suspend()`: saves nothing; `led_cdev->brightness` is the only
  copy of the value that `led_classdev_resume()` writes back.
- `led_classdev_suspend()`: flushes `set_brightness_work`, so a
  `brightness_set_blocking` driver too has been called with `LED_OFF` on
  return; `led_classdev_resume()` does not flush.
- `led_classdev_resume()`: calls `flash_resume` when the pointer is set, before
  it clears `LED_SUSPENDED`; `led_classdev_flash_register_ext()` sets the
  pointer when the driver has `LED_DEV_CAP_FLASH`.
- `LED_SUSPENDED` seen by the driver: set before the suspend write and cleared
  after the resume write, so a `brightness_set` callback sees it set in both.
- `LED_CORE_SUSPENDRESUME`: opt-in; without it `led_suspend()` and
  `led_resume()` do nothing.
- `LED_CORE_SUSPENDRESUME` from firmware: the core never sets it;
  `retain-state-suspended` is parsed by drivers only, for example
  `gpio_leds_create()` in `drivers/leds/leds-gpio.c`.
- `LED_SUSPENDED` in `drivers/leds/led-core.c`: tested only by
  `led_set_brightness_nosleep()` and `led_set_brightness_sync()`; a value is
  cached and applied at resume only if the call reaches one of them.
- `led_set_brightness()` with `LED_BLINK_SW` set, non-zero value, and neither
  `LED_SET_BRIGHTNESS` nor `LED_BLINK_DISABLE` pending: stored in
  `new_blink_brightness`, not in `led_cdev->brightness`.
- `led_set_brightness()` with `LED_BLINK_SW` set, value 0: queues
  `set_brightness_delayed()`, which calls the driver with `LED_OFF` while
  suspended and does not store to `led_cdev->brightness`.
- `led_blink_set()` while suspended: calls the driver's `blink_set` callback;
  nothing on that path tests `LED_SUSPENDED`.
- `blink_timer`: not stopped by `led_classdev_suspend()`; resume writes
  whichever blink phase the timer stored last.
- `led_update_brightness()`: no `LED_SUSPENDED` test; with a `brightness_get`
  callback it overwrites `led_cdev->brightness` with the hardware value, and
  resume restores that. `brightness_show()` calls it.
- **Potentially unsafe usage**: calling `led_update_brightness()` on an LED
  that has `brightness_get`.
  - Unsafe: while `LED_SUSPENDED` is set; the value that
    `led_classdev_resume()` restores is replaced by what the hardware reports.
  - Safe: before `led_classdev_suspend()`, as `kbdlight_suspend()` in
    `drivers/platform/x86/lenovo/thinkpad_acpi.c` does; `led_classdev_resume()`
    is what reads the field.
