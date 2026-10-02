- The rule is stated only in the section "sysfs attribute writes
  interpretation" of `Documentation/hwmon/sysfs-interface.rst`.
  `Documentation/hwmon/submitting-patches.rst` does not contain it.
- The section names only these cases: continuous, "tempX_max or inX_max", clamp
  with `clamp_val()`; not continuous, "tempX_type" and a fan divider with
  values 2, 4, 8, return `-EINVAL`.
- `pwmX`: not named by the section, and drivers do both.
  `drivers/hwmon/adt7470.c` clamps with `clamp_val()`;
  `drivers/hwmon/pwm-fan.c`, `drivers/hwmon/amc6821.c` and
  `drivers/hwmon/nct7904.c` return `-EINVAL` outside 0 to 255.
- `update_interval` and `samples`: drivers such as `ina238_write_chip()` and
  `lm95234_chip_write()` pick the closest supported value with
  `find_closest()` and return success. The section does not state this.
