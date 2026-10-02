- lm75_probe is not in this tree; `lm75_generic_probe()` in
  `drivers/hwmon/lm75.c` adds `lm75_remove()` with
  `devm_add_action_or_reset()` before the devm registration.
- `devm_hwmon_release()`: calls `hwmon_device_unregister()` for a device
  registered with a devm function; attached with `devres_add()` to the `dev`
  argument, so it runs when that device is unbound or deleted, which is the
  caller's unbind only if `dev` is the device the driver is bound to.
- Inside `device_del()`: `device_remove_attrs()` runs before
  `devres_release_all()`, so thermal zones and the `pec` file outlive the
  sysfs attributes; all are gone when `hwmon_device_unregister()` returns.
- **Unsafe usage**: calling `hwmon_notify_event()` or `hwmon_lock()` on the
  hwmon device after it is unregistered; `hwmon_dev_release()` has freed the
  `struct hwmon_device` both dereference.
  - Safe: IRQ requested with `devm_request_threaded_irq()` after the devm
    registration, so devres frees it first, as `lm75_generic_probe()` does.
  - Safe: work cancelled by a devm action added after the devm registration,
    as `lm90_stop_work()` added in `lm90_probe()`.
  - Safe: non-devm, remove what takes the lock and then unregister, as
    `corsairpsu_remove()` in `drivers/hwmon/corsair-psu.c` does with
    `debugfs_remove_recursive()` before `hwmon_device_unregister()`.
