- `Documentation/hwmon/submitting-patches.rst` on a non-standard attribute:
  create one only if really needed, discuss it on the mailing list first, and
  give a detailed explanation of why it is needed.
- "Standard": `Documentation/hwmon/submitting-patches.rst` defines it as
  specified in `Documentation/hwmon/sysfs-interface.rst`.
- Coverage: neither `Documentation/hwmon/sysfs-interface.rst` nor
  `Documentation/ABI/testing/sysfs-class-hwmon` lists every name in the
  template tables of `drivers/hwmon/hwmon.c`; for example `curr%d_label` and
  `power%d_label` are in neither.
- Documentation of a new attribute:
  `Documentation/hwmon/submitting-patches.rst` asks only that the driver's own
  file under `Documentation/hwmon/` exists and is up to date; no sentence
  requires an entry in `Documentation/ABI/testing/sysfs-class-hwmon` or in
  `Documentation/hwmon/sysfs-interface.rst`.
- debugfs: `Documentation/hwmon/submitting-patches.rst` does not mention it.
- Chip-specific sysfs attributes: `Documentation/hwmon/hwmon-kernel-api.rst`
  gives the `extra_groups` argument of `hwmon_device_register_with_info()` for
  them; `__hwmon_device_register()` puts those groups on the hwmon class
  device, next to the generated attributes.
- Deprecated attributes: `Documentation/hwmon/sysfs-interface.rst` calls only
  `alarms` and `beep_mask` deprecated; `temp[1-*]_type`, `temp[1-*]_crit` and
  `fan[1-*]_div` are standard.
- `alarms`: the core still generates it for `HWMON_C_ALARMS`, and for example
  `drivers/hwmon/lm83.c` sets that bit.
- `beep_mask`: has no template in `drivers/hwmon/hwmon.c`.
