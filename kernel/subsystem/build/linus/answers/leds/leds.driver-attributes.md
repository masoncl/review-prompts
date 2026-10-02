- `groups` with `led_classdev_multicolor_register_ext()`: overwritten
  unconditionally with the multicolor groups; a value the driver set is lost
  silently.
- Attributes added after registration: not forbidden; the core does it for
  `brightness_hw_changed` and for trigger `groups`, and multicolor drivers
  must, for example `devm_device_add_group()` on `led_cdev.dev` in
  `drivers/hid/hid-lenovo-go-s.c`.
- Files added after registration: appear after the `KOBJ_ADD` uevent sent by
  `device_add()`; files from `groups` exist before it.
- `groups` array lifetime: `device_create_with_groups()` stores the pointer
  and `device_remove_attrs()` reads it at unregistration, so the array must
  stay valid until `led_classdev_unregister()` returns.
- Attribute names: share one directory with the class attributes and with the
  `groups` of whichever trigger is attached; a clash with a trigger attribute
  makes `device_add_groups()` fail in `led_trigger_set()`, and the trigger is
  not attached.
- `led_access` and `LED_SYSFS_DISABLE`: the core applies neither to driver
  handlers; a handler that must respect them takes `led_access` and tests
  `led_sysfs_is_disabled()` itself, as `flash_strobe_store()` in
  `drivers/leds/led-class-flash.c` does.
- **Potentially unsafe usage**: a handler of an attribute in
  `led_cdev->groups` that runs without `led_access`.
  - Unsafe: when it calls a core function that uses `set_brightness_work`,
    `blink_timer` or `led_cdev->wq`, for example `led_set_brightness()` on an
    LED with only `brightness_set_blocking`; `led_classdev_register_ext()`
    sets these up after `device_create_with_groups()` has made the files
    visible.
  - Safe: the handler takes `led_access` first, as `flash_brightness_store()`
    does; `led_classdev_register_ext()` holds `led_access` from before the
    device is created until registration is complete.
  - Safe: the handler reads only driver data that was set before the register
    call, as `ns2_led_sata_show()` in `drivers/leds/leds-ns2.c` does.
