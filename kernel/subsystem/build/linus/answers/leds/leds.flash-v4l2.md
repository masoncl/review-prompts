- `v4l2_flash_init()`: rejects only a NULL `config`; a NULL `fled_cdev` or a
  NULL `ops` is accepted.
- `struct v4l2_flash`: allocated with `devm_kzalloc()` on `dev` in
  `__v4l2_flash_init()`; `v4l2_flash_release()` does not free it.
- LED pointer: stored bare in `struct v4l2_flash`; the wrapper takes no
  reference on the LED.
- `v4l2_flash_init()` drives the LED before any open:
  `v4l2_flash_init_controls()` calls `v4l2_ctrl_handler_setup()`, which runs
  `v4l2_flash_s_ctrl()` for each control that is neither a button nor
  read-only, until one returns an error.
  - This reaches `led_set_flash_strobe()`, `led_set_flash_timeout()`,
    `led_set_flash_brightness()` and `led_set_brightness_sync()`.
  - Sysfs is not disabled and `led_access` is not held at that point.
  - The return value of `v4l2_ctrl_handler_setup()` is ignored.
- **Unsafe usage**: calling `v4l2_flash_init()` on a flash LED that has not
  passed `led_classdev_flash_register_ext()`.
  - Safe: register first, then init, as `mt6370_led_register()` does;
    registration is what guarantees `ops->strobe_set`.
- `v4l2_flash_open()` and `v4l2_flash_close()`: act only when
  `v4l2_fh_is_singular()`, that is on the first open and the last close.
- `v4l2_flash_open()`: calls `led_trigger_remove()` for the flash LED and for
  the indicator, under `led_access`.
- `v4l2_flash_close()`: does not restore the trigger.
- `v4l2_flash_close()`: sets the `STROBE_SOURCE` control back to software when
  that control exists, under `led_access`, before `led_sysfs_enable()`.
- `LED_SYSFS_DISABLE`: stops only store handlers that test
  `led_sysfs_is_disabled()`; show handlers such as `flash_strobe_show()` and
  `flash_brightness_show()` still call the driver while the sub-device is
  open.
- `led_set_brightness_sync()`: returns `-EBUSY` while `blink_delay_on` or
  `blink_delay_off` is set, and `-ENOTSUPP` without
  `brightness_set_blocking`.
- Indicator LED: neither `led_classdev_register_ext()` nor
  `v4l2_flash_indicator_init()` checks its `brightness_set_blocking`; without
  it `__sync_device_with_v4l2_controls()` fails and `v4l2_flash_open()`
  returns the error.
- `V4L2_CID_FLASH_LED_MODE` set to none or flash: the result of
  `led_set_brightness_sync()` with `LED_OFF` is ignored.
