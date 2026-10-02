- `is_string_attr()`: also matches `hwmon_energy64` with `hwmon_energy_label`.
- `hwmon_chip`, `hwmon_pwm` and `hwmon_intrusion`: have no string attribute;
  there is no hwmon_chip_label in this tree.
- `hwmon_attr_show_string()`: holds the hwmon mutex from before `read_string`
  until after `sysfs_emit()`. A string that is changed only by callbacks or
  under `hwmon_lock()` cannot change between the return and the print.
- A string changed or freed by code that does not hold the hwmon mutex: still
  unsafe, for example from an interrupt thread or a work item.
- `s` in `hwmon_attr_show_string()`: not initialised. A `read_string` that
  returns 0 without storing to `*str` makes the core print through a garbage
  pointer.
