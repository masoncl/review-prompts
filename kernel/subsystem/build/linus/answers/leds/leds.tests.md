- `drivers/leds/led-test.c`: KUnit suite named `led`, two cases,
  `led_test_class_register()` and `led_test_class_add_lookup_and_get()`.
- `led_test_class_register()` checks: `max_brightness` defaults to `LED_FULL`;
  `brightness` is read back from `brightness_get` at registration; a duplicate
  name registers as `led-test_1` while `cdev->name` stays `led-test`; with
  `LED_REJECT_NAME_CONFLICT` the duplicate fails with `-EEXIST`.
- `led_test_class_add_lookup_and_get()` checks: `led_add_lookup()`, then
  `devm_led_get()` by `con_id`, then `led_remove_lookup()`.
- Not covered: brightness clamping, triggers, blink, the multicolor and flash
  classes, sysfs files, suspend and resume.
- `CONFIG_LEDS_KUNIT_TEST`: tristate, `depends on KUNIT && LEDS_CLASS`,
  `default KUNIT_ALL_TESTS`.
- `drivers/leds/.kunitconfig` exists; run with
  `tools/testing/kunit/kunit.py run --kunitconfig drivers/leds`.
- `tools/leds/Makefile`: builds only `uledmon` and `led_hw_brightness_mon`,
  with `-I../../include/uapi` so they use this tree's
  `include/uapi/linux/uleds.h`; `make -C tools leds` also works.
- `tools/leds/get_led_device_info.sh`: a script, not built; it prints the
  parent device details of an LED and validates the LED name against
  `include/dt-bindings/leds/common.h`, found relative to the script or given as
  a second argument.
- `led_hw_brightness_mon`: the file it polls exists only with
  `CONFIG_LEDS_BRIGHTNESS_HW_CHANGED` and `LED_BRIGHT_HW_CHANGED` set in the
  LED's `flags`.
- `tools/testing/selftests/`: has no LED directory.
