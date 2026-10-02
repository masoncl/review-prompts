- `struct led_classdev_flash`: three `struct led_flash_setting` members,
  `brightness`, `timeout` and `duration`.
- `struct led_flash_ops`: seven members; besides the five setters and getters
  for brightness, strobe and timeout it has `fault_get` and `duration_set`.
- `duration` and `duration_set`: reached only through
  `led_set_flash_duration()` in `drivers/leds/led-class-flash.c`, which has no
  caller in this tree.
- `duration_set`: no driver in this tree sets it.
- `duration`: no sysfs group, no control in
  `drivers/media/v4l2-core/v4l2-flash-led-class.c`, and `led_flash_resume()`
  does not re-apply it.
- `duration` unit: the only statement is the header comment, which says
  microseconds.
- `flash_brightness_set`, `flash_brightness_get`, `strobe_get`, `timeout_set`,
  `fault_get`, `duration_set`: optional; registration never fails for lack of
  one.
- Without `LED_DEV_CAP_FLASH`: no op is required and `ops` may be NULL, as in
  `qcom_flash_register_led_device()` for a node with no
  "flash-max-microamp".
