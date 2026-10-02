- `dev` that is not a hwmon class device (for example the parent): `WARN()`
  and `-EINVAL` before anything is notified; see `is_hwmon_device()`.
- Return value: 0 or `-EINVAL` only; the attribute name is built in stack
  arrays, so there is no `-ENOMEM`.
- Uevent: sent with `kobject_uevent_env()`, `KOBJ_CHANGE` and one variable
  `NAME=<attribute name>`; its result is dropped.
- Thermal: `hwmon_thermal_notify()` runs for every `attr` of type
  `hwmon_temp`, for example `hwmon_temp_max_alarm`, not only
  `hwmon_temp_input`.
- `channel`: not checked against the chip info.
- `templates[attr]`: not tested for NULL; only the two range checks on `type`
  and `attr` exist.
