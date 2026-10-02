- Table names: there is no hwmon_attr_templates or __hwmon_attr_templates
  array; the per-type tables are gathered in `__templates` and their sizes
  in `__templates_size`, both in `drivers/hwmon/hwmon.c`.
- `__templates` and `__templates_size`: two separate arrays indexed by
  `enum hwmon_sensor_types`; a new type needs an entry in each, and nothing
  checks that they agree.
- Build-time checks: `drivers/hwmon/hwmon.c` has no `BUILD_BUG_ON()` and no
  `static_assert()` that ties an enumeration to its table.
- Errors from `hwmon_genattr()` other than `-ENOENT`: fail the whole
  registration.
- Sensor type inside `__templates` with a `__templates_size` entry of 0:
  every bit of that type is skipped.
- `hwmon_chip_attrs`: holds complete file names, not formats;
  `hwmon_genattr()` uses the string as the name for `hwmon_chip`.
- `hwmon_notify_event()`: indexes the same two arrays; returns `-EINVAL`
  for an index at or beyond the size, and passes a NULL slot to
  `scnprintf()` as the format without a test.
- `is_string_attr()`: must list a new label attribute for each type that
  has it; `hwmon_energy64` has its own line.
- Attribute missing from `is_string_attr()`: is shown by `hwmon_attr_show()`
  through `ops->read` as a number.
- `hwmon_energy64`: shares `enum hwmon_energy_attributes`, the macros
  `HWMON_E_ENABLE`, `HWMON_E_INPUT` and `HWMON_E_LABEL`, and
  `hwmon_energy_attr_templates` with `hwmon_energy`; a new energy
  attribute applies to both types.
- `hwmon_attr_show()`: passes the address of an `s64`, cast to `long *`,
  for `hwmon_energy64`; a new type wider than `long` needs the same
  handling there.
- Limit: 32 attributes per type, since `config` in
  `struct hwmon_channel_info` is `const u32 *`.
- `enum hwmon_power_attributes`: has 31 values, so one bit is left.
- `hwmon_max`: must stay the last value of `enum hwmon_sensor_types`;
  drivers size arrays by it, for example `ps_type_attrs` in
  `drivers/power/supply/power_supply_hwmon.c`.
- `Documentation/ABI/testing/sysfs-class-hwmon`: holds the full description
  of the attributes it lists, each under a `What:` line.
- `Documentation/hwmon/hwmon-kernel-api.rst`: has a table of sensor types
  and a table of macro prefixes, and no list of attributes; it changes for
  a new type, not for a new attribute.
