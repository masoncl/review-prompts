- `led_classdev_notify_brightness_hw_changed()`: stores the value and calls
  `sysfs_notify_dirent()` on the cached node; it sends no uevent and does not
  touch the kobject.
- Calling context of `led_classdev_notify_brightness_hw_changed()`: nothing
  in it sleeps; `kernfs_notify()` in `fs/kernfs/file.c` takes its lock with
  `spin_lock_irqsave()` and defers the rest with `schedule_work()`.
- `CONFIG_LEDS_BRIGHTNESS_HW_CHANGED`: no Kconfig entry in this tree selects
  or depends on it; a driver that sets the flag and calls the function builds
  either way, and with the symbol off there is silently no attribute.
- `brightness_hw_changed_show()`: returns `-ENODATA` only while the field is
  exactly -1, the value `led_classdev_register_ext()` stores.
- `thinkpad_acpi.c` is at `drivers/platform/x86/lenovo/thinkpad_acpi.c`.
- **Unsafe usage**: calling
  `led_classdev_notify_brightness_hw_changed()` on an LED registered without
  `LED_BRIGHT_HW_CHANGED`.
  - Unsafe: when the `struct led_classdev` was not zero-initialised; the only
    guard is `WARN_ON(!led_cdev->brightness_hw_changed_kn)`, and
    registration writes that field only when the flag is set.
  - Unsafe: on a zeroed structure the call warns and returns without
    notifying.
  - Safe: flag set before registration, as `t14s_kbd_backlight_probe()` in
    `drivers/platform/arm64/lenovo-thinkpad-t14s.c` does.
- **Unsafe usage**: an event source that can call
  `led_classdev_notify_brightness_hw_changed()` after
  `led_classdev_unregister()`.
  - Unsafe: `led_remove_brightness_hw_changed()` drops the node reference with
    `sysfs_put()` and leaves `brightness_hw_changed_kn` set, so the
    `WARN_ON()` does not fire and `sysfs_notify_dirent()` gets a stale node.
  - Safe: event source released before the LED, as in `t14s_ec_probe()`:
    `devm_led_classdev_register()` runs before
    `devm_request_threaded_irq()`, so devres frees the interrupt first.
  - Safe: the same order also covers the start: the LED is registered before
    the interrupt can fire.
