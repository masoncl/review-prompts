- Probe error path: `really_probe()` in `drivers/base/dd.c` runs
  `device_unbind_cleanup()` after probe returns an error, so a managed LED is
  unregistered after the probe function's own unwinding, as after `remove()`.
- **Potentially unsafe usage**: managed registration, with `remove()` or the
  probe error path releasing by hand something the callbacks use.
  - Unsafe: when the LED is still registered at that point;
    `devm_led_classdev_release()` runs later and
    `led_classdev_unregister()` calls the set callback with `LED_OFF`; the
    callback then queues on a destroyed workqueue, writes to a powered-down
    chip, or locks a destroyed mutex.
  - Unsafe: `mutex_destroy()` is an empty inline without
    `CONFIG_DEBUG_MUTEXES` (`include/linux/mutex.h`), so the mutex case shows
    up only with that option.
  - Safe: every such resource acquired with devm before the LED is
    registered, as `an30259a_probe()` in `drivers/leds/leds-an30259a.c` does
    with `devm_mutex_init()` and `devm_regmap_init_i2c()`; `release_nodes()`
    in `drivers/base/devres.c` releases in reverse order.
  - Safe: power-down registered with `devm_add_action()` before the LED, as
    `lm3532_parse_node()` in `drivers/leds/leds-lm3532.c` does.
  - Safe: `devm_led_classdev_unregister()` first, then the manual release, as
    `asus_wireless_remove()` does.
- **Unsafe usage**: unmanaged registration, with a resource the callbacks use
  released before `led_classdev_unregister()`.
  - Safe: unregister every LED, then `mutex_destroy()` and `kfree()`, as
    `npem_free()` in `drivers/pci/npem.c` does.
- sysfs handlers, including the driver's own `led_cdev->groups`: need the
  same resources until `device_unregister()` inside
  `led_classdev_unregister()` returns.
- `led_classdev_flash_unregister()` and
  `led_classdev_multicolor_unregister()`: both end in
  `led_classdev_unregister()`, so the same ordering applies.
