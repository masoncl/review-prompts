- `LED_DEV_CAP_FLASH`: set by the driver in `led_cdev.flags` before the call;
  `led_classdev_flash_register_ext()` only tests it.
- With the flag, in order: `led_cdev.brightness_set_blocking` must be set,
  then `ops` and `ops->strobe_set`; each failure returns `-EINVAL`.
- With the flag: `led_cdev->flash_resume` is set to `led_flash_resume()`.
- Without the flag: none of these checks run, `ops` may be NULL, and no flash
  attribute is created.
- `led_access`: initialised by `led_classdev_register_ext()`, not by the flash
  code.
- There is no led_flash_groups array; `led_flash_init_sysfs_groups()` fills
  `fled_cdev->sysfs_groups`.
- Group selection: strobe always; brightness if `ops->flash_brightness_set`;
  timeout if `ops->timeout_set`; fault if `ops->fault_get`.
- `led_cdev->groups` with the flag: overwritten with
  `fled_cdev->sysfs_groups`, so groups a driver put there before the call are
  dropped.
- `sysfs_groups` terminator: `led_flash_init_sysfs_groups()` never writes the
  NULL entry.
  - `LED_FLASH_SYSFS_GROUPS_SIZE` is 5, four groups plus the terminator.
- **Unsafe usage**: registering with `LED_DEV_CAP_FLASH` a
  `struct led_classdev_flash` whose `sysfs_groups` is not zeroed.
  - Safe: the structure comes from zeroed memory, as in `mt6370_led_probe()`,
    which allocates it with `devm_kzalloc()`; the entry after the last group
    is then NULL when `led_classdev_register_ext()` passes `led_cdev->groups`
    to `device_create_with_groups()`, and `internal_create_groups()` in
    `fs/sysfs/group.c` walks the array up to the first NULL.
- `__fill_ctrl_init_data()` in
  `drivers/media/v4l2-core/v4l2-flash-led-class.c`: also tests the flag; for an
  `fled_cdev` without it, it warns and creates no flash or torch control.
