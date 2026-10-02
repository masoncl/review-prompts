- `hwmon_attr_base()`: 0 for `hwmon_in` and `hwmon_intrusion`; 1 for every
  other type, `hwmon_pwm` and `hwmon_energy64` included.
- There is no hwmon_sensors prefix table; each template outside
  `hwmon_chip_attrs` is the whole name with one `%d`, such as "temp%d_input"
  in `hwmon_temp_attr_templates`.
- `hwmon_energy64`: `__templates[]` maps it to `hwmon_energy_attr_templates`,
  so its files are named `energy%d_...` exactly like those of `hwmon_energy`.
- Channel number: the position in `config[]` of one
  `struct hwmon_channel_info` plus the base; it restarts for every entry of
  `chip->info`.
- **Potentially unsafe usage**: a `hwmon_energy` and a `hwmon_energy64` entry
  in one `struct hwmon_chip_info`.
  - Unsafe: when both set the same `HWMON_E_` bit at the same `config[]`
    position and both are visible; the core does not check for duplicate
    names, `sysfs_add_file_mode_ns()` returns `-EEXIST` and
    `device_register()` fails.
  - Safe: when the bits at each position are disjoint, as in `ltc4282_info`
    in `drivers/hwmon/ltc4282.c`; the shared table in `__templates[]` is what
    makes the names equal.
- Name storage, for every type but `hwmon_chip`: `name[]` in
  `struct hwmon_device_attribute`, of `MAX_SYSFS_ATTR_NAME_LENGTH` (32)
  bytes; there is no MAX_SYSFS_ATTR_NAME_LEN and the name is not duplicated
  with `devm_kstrdup()`.
- Too-long name: `scnprintf()` cuts it at 31 characters; `hwmon_genattr()`
  ignores the return value and prints nothing.
