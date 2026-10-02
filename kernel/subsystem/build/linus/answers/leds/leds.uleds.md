- `uleds_misc`: minor is `MISC_DYNAMIC_MINOR`; there is no ULEDS_MINOR in this
  tree.
- `uleds_open()`: allocates `struct uleds_device` and sets `led_cdev.name` and
  `led_cdev.brightness_set`; `uleds_write()` does not allocate the structure.
- Registration: `uleds_write()` calls `devm_led_classdev_register()` with
  parent `uleds_misc.this_device`, not `led_classdev_register()`.
- Removal: `uleds_release()` calls `devm_led_classdev_unregister()` on the same
  parent, only if the state is `ULEDS_STATE_REGISTERED`.
- Hook: the driver sets `brightness_set`, not `brightness_set_blocking`, and
  writes no `flags` (no `LED_CORE_SUSPENDRESUME`).
- Name checks in `uleds_write()`, each failing with `-EINVAL`: empty, `"."`,
  `".."`, contains `/`, or no `'\0'` within `LED_MAX_NAME_SIZE` bytes.
- Unterminated name: rejected, never truncated or terminated by the driver.
- `max_brightness <= 0`: `-EINVAL`, so negative values are rejected too.
- Order of checks in `uleds_write()`: `-EBUSY` is tested before the size, so
  any non-empty write to a registered fd gives `-EBUSY`.
- Failed write: leaves the state at `ULEDS_STATE_UNKNOWN`, so the same fd can
  write again.
- Name clash: `led_classdev_next_name()` in `drivers/leds/led-class.c` appends
  `_<n>`; uleds does not set `LED_REJECT_NAME_CONFLICT`.
- Renamed LED: `led_cdev.name` keeps the name as written, and nothing on the fd
  reports the final name.
- Name clash where the suffixed name does not fit in `LED_MAX_NAME_SIZE`:
  the write fails with `-ENOMEM`.
- Value read: one `int` (`sizeof(udev->brightness)`), not one byte.
- `uleds_read()` with `count` below `sizeof(int)`: returns 0, not `-EINVAL`.
- `Documentation/leds/uleds.rst`: says a single byte is read and shows
  `struct uleds_user_dev` without `max_brightness`; the code does neither.
- `uleds_read()` before registration: `-ENODEV`.
- First read after a successful write: does not block, because
  `uleds_write()` sets `new_data`; it returns the stored `brightness`, which
  is 0 unless something has set the LED since.
- `uleds_brightness_set()`: sets `new_data` and wakes `waitq` only when the
  value differs from the stored `brightness`.
- `struct uleds_device`: keeps only the latest value, in `brightness`; changes
  between two reads collapse into one.
- `mutex` of `struct uleds_device`: taken by `uleds_write()` and
  `uleds_read()` only; `uleds_brightness_set()` writes `brightness` and
  `new_data`, and `uleds_poll()` reads `new_data`, without it.
