- The parse of `dev_name()` against `HWMON_ID_FORMAT` is the only test:
  `hwmon_device_unregister()` does not call `is_hwmon_device()` and does
  not compare `dev->class` with `hwmon_class`.
- **Unsafe usage**: calling `hwmon_device_unregister()` on a device from
  `devm_hwmon_device_register_with_info()` or
  `devm_hwmon_device_register_with_groups()`; `devm_hwmon_release()` calls
  it again on the same pointer, after `device_unregister()` dropped the
  reference and `hwmon_dev_release()` may have freed the device.
  - Safe: register with `hwmon_device_register_with_info()` and unregister
    once by hand, as `arctic_fan_probe()` and `arctic_fan_remove()` in
    `drivers/hwmon/arctic_fan_controller.c` do; only the devm functions add
    `devm_hwmon_release()`.
