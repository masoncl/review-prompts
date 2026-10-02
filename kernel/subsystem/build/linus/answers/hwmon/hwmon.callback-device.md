- `pec_store()`: the sysfs file sits on the I2C client, yet `write` still
  receives the hwmon device, with `hwmon_chip` and `hwmon_chip_pec`.
