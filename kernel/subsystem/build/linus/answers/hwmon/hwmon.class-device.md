- There is no hwmon_dev_name_is_valid() here; the name test is an inline
  `strpbrk()` in `__hwmon_device_register()`.
- `label` attribute: a `kstrdup()` copy of the `label` device property of the
  device passed in; a failing `device_property_read_string()` fails
  registration.
- NULL parent: `hwmon_device_register_with_groups()` and
  `hwmon_device_register()` do not test `dev`; the hwmon device then has no
  parent, for example in `drivers/platform/mips/cpu_hwmon.c`.
- `dev_get_drvdata()` on the hwmon device: returns the `drvdata` argument of
  the registration call; the core never copies the parent's driver data.
- `hwmon_device_unregister()` on a device whose name does not parse as
  `HWMON_ID_FORMAT`, such as the parent: `dev_dbg()` only; nothing is
  unregistered and no id is freed.
