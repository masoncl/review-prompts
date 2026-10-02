- Files: three, not two; `multi_max_intensity` (read-only) is added beside
  `multi_intensity` and `multi_index`.
- `multi_max_intensity`: prints `led_mc_get_max_intensity()` for each
  sub-LED, computed at read time, so a channel with `max_intensity` 0 shows
  the current `led_cdev.max_brightness`.
- Limit on a written value: `multi_intensity_store()` stores
  `min(value, led_mc_get_max_intensity())`, that is `max_intensity` if
  nonzero, else `led_cdev.max_brightness`.
- Over-limit value: clamped silently; the write still returns `size`, not an
  error.
- `led_sysfs_is_disabled()`: not called by `multi_intensity_store()`; a
  write succeeds while sysfs access is disabled for `brightness`.
- `LED_BLINK_SW` set in `work_flags`: `multi_intensity_store()` skips
  `led_set_brightness()`; only `intensity` is updated and the driver is not
  called by the store.
- `LED_BLINK_SW` clear: `led_set_brightness(led_cdev, led_cdev->brightness)`
  is the only path to the hardware; for a driver with only
  `brightness_set_blocking` the write to hardware happens later, from
  `set_brightness_work`.
