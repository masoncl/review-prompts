- `led_trigger_get_led()` and `led_trigger_get_drvdata()`: macros in
  `include/linux/leds.h`, defined only under `CONFIG_LEDS_TRIGGERS`.
- Failed `activate`: `led_trigger_set()` does not call `deactivate` and sets
  `trigger_data` to NULL, so `activate` frees what it stored before it returns
  the error, as `gpio_trig_activate()` does.
- `set_device_name()` in `drivers/leds/trigger/ledtrig-netdev.c`: tests
  `led_get_trigger_data()` for NULL to detect a call from inside
  `netdev_trig_activate()`; this relies on the core clearing the pointer on
  detach.
- The core removes only `trig->groups`; a file the trigger adds itself stays
  until the trigger removes it, for example `ports_group` in
  `drivers/usb/core/ledtrig-usbport.c`.
- **Unsafe usage**: in `activate`, starting an IRQ, notifier, timer or work
  whose handler calls `led_get_trigger_data()`, before
  `led_set_trigger_data()` has stored the pointer.
  - Unsafe: the handler can run as soon as it is registered and gets NULL.
  - Safe: store first, then register, as `gpio_trig_activate()` does before
    `request_threaded_irq()`; `gpio_trig_irq()` dereferences
    `led_get_trigger_data()` with no NULL test.
- **Unsafe usage**: taking `led_cdev->led_access` or `led_cdev->trigger_lock`
  in the handler of an attribute in `trig->groups`.
  - Unsafe: `led_trigger_write()` holds both across `device_remove_groups()`
    in `led_trigger_set()`, which waits for running handlers.
  - Safe: a lock inside the trigger data, as `device_name_show()` takes
    `trigger_data->lock` in `drivers/leds/trigger/ledtrig-netdev.c`.
