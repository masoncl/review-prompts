- `__hwmon_device_register()`: does not search `info` for the chip entry; it
  tests `chip->info[0]->type == hwmon_chip` and reads only
  `chip->info[0]->config[0]`.
- Position-dependent flags: `HWMON_C_REGISTER_TZ` and `HWMON_C_PEC`, both
  tested in that one block; no other chip bit is read there.
- `hwmon_thermal_register_sensors()`: its loop starts at `info[1]`; it is
  reached only when `info[0]` is the chip entry.
- **Unsafe usage**: a `hwmon_chip` entry that carries `HWMON_C_REGISTER_TZ` or
  `HWMON_C_PEC` anywhere but `info[0]`; the flag is dropped, registration
  succeeds, nothing is logged.
  - Safe: chip entry first, as `lm75_info` in `drivers/hwmon/lm75.c`; the
    `info[0]` test in `__hwmon_device_register()` defines the requirement.
  - Safe: chip entry later that holds only bits named in `hwmon_chip_attrs[]`,
    as `nzxt_smart2_channel_info` in `drivers/hwmon/nzxt-smart2.c`;
    `__hwmon_create_attrs()` walks every entry.
