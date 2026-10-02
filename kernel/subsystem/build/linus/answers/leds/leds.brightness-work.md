- Workqueue: `led_cdev->wq`, which `led_classdev_register_ext()` sets to
  `leds_wq`; the core does not use `schedule_work()`.
- `leds_wq`: one `alloc_ordered_workqueue()` in `leds_init()` in
  `drivers/leds/led-class.c`, shared by every LED.
- `set_brightness_delayed()`: its brightness steps do not call
  `led_set_brightness_nopm()`; they call
  `set_brightness_delayed_set_brightness()`, which tries `brightness_set`
  first and `brightness_set_blocking` only on `-ENOTSUPP`.
- Off and non-zero requests: tracked by separate bits,
  `LED_SET_BRIGHTNESS_OFF` and `LED_SET_BRIGHTNESS`; of several pending
  non-zero values only the latest is delivered, a later 0 through
  `led_set_brightness_nopm()` drops a pending non-zero value, and a pending
  off is delivered as its own `LED_OFF` call before the latest non-zero
  value.
- `led_set_brightness()` with 0 then non-zero on a software-blinking LED,
  before the work runs: the second call is queued, so the handler stops the
  blink, sets `LED_OFF`, then sets the new value.
- Silent errors: `-ENOTSUPP` when `brightness_set` is NULL and
  `brightness_set_blocking` is NULL or returns it, and `-ENODEV` when both
  `LED_UNREGISTERING` and `LED_HW_PLUGGABLE` are set; every other negative
  value goes to `dev_err()`.
- `led_trigger_set()` removing a trigger: calls `cancel_work_sync()` on
  `set_brightness_work`, so a queued change may never reach the driver.
