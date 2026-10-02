- `include/linux/hwmon.h` marks three functions deprecated by comment:
  `hwmon_device_register()`, `hwmon_device_register_with_groups()`,
  `devm_hwmon_device_register_with_groups()`.
- `hwmon_device_register_for_thermal()`: not marked in the header; the
  restriction is the kerneldoc in `drivers/hwmon/hwmon.c` plus
  `EXPORT_SYMBOL_NS_GPL()` in namespace "HWMON_THERMAL", which only
  `drivers/thermal/thermal_hwmon.c` imports.
- `hwmon_device_register()`: present, still has callers, calls `dev_warn()` on
  every call; the two with_groups functions print no deprecation message.
- NULL arguments in the other registration functions;
  `hwmon_device_register_with_info()` returns `-EINVAL` for NULL `dev` and for
  NULL `name`:

| Function | NULL `dev` | NULL `name` |
|---|---|---|
| `hwmon_device_register()` | accepted | always NULL, `name` file hidden |
| `hwmon_device_register_with_groups()` | accepted | `-EINVAL` |
| `devm_hwmon_device_register_with_groups()` | `-EINVAL` | `-EINVAL`, no fallback |
| `hwmon_device_register_for_thermal()` | `-EINVAL` | `-EINVAL` |

- `show`/`store` handlers in `groups` of a with_groups device: called without
  `lock` of `struct hwmon_device`; with no `chip`,
  `__hwmon_device_register()` installs `groups` as given and the core never
  takes the lock for that device.
- `name` and `label` class attributes: created for every variant by
  `hwmon_dev_attr_groups`; `hwmon_dev_attr_is_visible()` hides each when its
  string is NULL.
- `hwmon_lock()` and `hwmon_notify_event()`: usable on a device from any
  variant; `mutex_init()` runs for all in `__hwmon_device_register()`.
- devm_hwmon_device_unregister is not in this tree;
  `hwmon_device_unregister()` is the only unregister function, and a devm
  registration is undone only by devres.
