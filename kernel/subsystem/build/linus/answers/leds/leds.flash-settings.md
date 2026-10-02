- Value between two steps: rounded to the nearest step counted from `min`, a
  tie goes up; `led_clamp_align()` adds `step / 2` before it clamps.
- LED suspended (`LED_SUSPENDED`): `led_set_flash_brightness()` and
  `led_set_flash_timeout()` both return 0, not `-EBUSY`; the op is not called
  and the aligned value stays in `val`.
- Cached value: `led_flash_resume()` writes it to the driver when
  `led_classdev_resume()` runs.
- Missing op: `-EINVAL` only when the LED is not suspended; while suspended
  the helper returns 0.
- `val`: written before the op is called, and kept when the op fails or is
  missing.
- `step`: a divisor in `led_clamp_align()`; it must be non-zero before either
  helper is called.
- `fled_cdev`: must be non-NULL; the helpers write `val` before
  `has_flash_op()` tests the pointer.
- `ops`: must be non-NULL; `has_flash_op()` in
  `drivers/leds/led-class-flash.c` dereferences it without a test.
