- `hwmon_energy64` is a sensor type in `enum hwmon_sensor_types` with no
  attribute enum and no macros of its own; it is described with the
  `HWMON_E_` macros of `enum hwmon_energy_attributes`.
- `HWMON_CHANNEL_INFO(energy64, HWMON_E_INPUT)` is the correct form, for
  example in `drivers/hwmon/ina238.c`.
- `hwmon_curr` uses the prefix `HWMON_C_`, the same as `hwmon_chip`; no macro
  name is shared, but some differ by little.
- `HWMON_C_ALARM` and `HWMON_C_RESET_HISTORY` are curr bits;
  `HWMON_C_ALARMS` and `HWMON_C_CURR_RESET_HISTORY` are chip bits.
- A macro of another type whose bit number has no template in the described
  type: `hwmon_genattrs()` in `drivers/hwmon/hwmon.c` skips the bit; no
  attribute, no error, no message.
