- `led_set_flash_strobe()`: calls `ops->strobe_set` with no test of `ops` or
  of the op; a NULL there is a NULL dereference, not `-EINVAL`.
- `led_get_flash_strobe()`: tests `ops->strobe_get` but not `ops`.
- `LED_SUSPENDED`: neither helper tests it; the op is called on a suspended
  LED.
- **Unsafe usage**: calling either helper on a `struct led_classdev_flash`
  that has not passed `led_classdev_flash_register_ext()` with
  `LED_DEV_CAP_FLASH` set.
  - Safe: `flash_strobe_store()` and `flash_strobe_show()`; the `flash_strobe`
    attribute is created only by `led_flash_init_sysfs_groups()`, which runs
    after the `ops` and `strobe_set` checks.
  - Safe: `v4l2_flash_s_ctrl()` on an LED registered before
    `v4l2_flash_init()`; `__fill_ctrl_init_data()` creates the mode and strobe
    controls only when the flag is set.
- `flash_strobe_store()`: holds `led_cdev->led_access` around
  `led_set_flash_strobe()`.
- `flash_strobe_show()`: takes no lock around `led_get_flash_strobe()`, and
  does not test `led_sysfs_is_disabled()`.
- `v4l2_flash_s_ctrl()` and `v4l2_flash_g_volatile_ctrl()`: call the helpers
  without `led_access`.
- `led_access` therefore does not serialise `strobe_get` against `strobe_set`;
  the helpers take no lock of their own.
