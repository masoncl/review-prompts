- `Documentation/ABI/testing/sysfs-class-hwmon`: holds the `Unit:` lines; some
  entries have none, for example `pwmY` and the alarm flags.
- Name prefix: does not fix the unit; for example `powerY_accuracy` is in
  percent and `powerY_average_interval` in milliseconds.
- `update_interval_us`: microsecond; the ABI entry says a driver that has it
  should also implement `update_interval`.
- Temperature files of chips that measure through a thermistor and an ADC and
  report the measurement as a voltage: hold millivolt, not millidegree
  Celsius; see "Temperatures" in `Documentation/hwmon/sysfs-interface.rst`.
- `hwmon_energy64`: is in `enum hwmon_sensor_types`; it creates the same
  `energy%d_input` file in microJoule and uses the `HWMON_E_INPUT` bits.
- Names with no stated unit: for example `power%d_min` and `power%d_lcrit` in
  `hwmon_power_attr_templates` have no entry in
  `Documentation/ABI/testing/sysfs-class-hwmon` or in
  `Documentation/hwmon/sysfs-interface.rst`.
- `hwmon_thermal_get_temp()` and `hwmon_thermal_set_trips()` in
  `drivers/hwmon/hwmon.c`: pass `hwmon_temp_input`, `hwmon_temp_min` and
  `hwmon_temp_max` values between the driver and thermal with no scaling.
