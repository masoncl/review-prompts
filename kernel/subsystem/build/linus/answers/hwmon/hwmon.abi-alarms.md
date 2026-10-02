- `hwmon_attr_show()` in `drivers/hwmon/hwmon.c`: prints the value the callback
  stored; the callback itself has to reduce a status bit to 0 or 1.
- `intrusionY_alarm`: RW in `Documentation/ABI/testing/sysfs-class-hwmon`; it
  sticks until 0 is written, and writing another value is unsupported.
- Regular alarm flags: the `intrusionY_alarm` ABI entry describes them as
  clearing themselves when read.
- Rule that drivers do not compare readings with thresholds: stated in the
  introduction of `Documentation/hwmon/sysfs-interface.rst`, with the reason
  that violations between readings are then caught; nothing in
  `drivers/hwmon/hwmon.c` checks it.
- `pmbus_get_boolean()` in `drivers/hwmon/pmbus/pmbus_core.c`: when the
  boolean has both sensors, compares the reading with the limit, but returns
  1 only if the chip's status bit is also set.
- Fault attribute set to 1: `Documentation/hwmon/sysfs-interface.rst` says only
  that the measurement for that channel should not be trusted; it does not
  require the read of the input attribute to fail.
- `-ENODATA`: named by `Documentation/hwmon/sysfs-interface.rst` and
  `Documentation/ABI/testing/sysfs-class-hwmon` only in the enable entries,
  such as `tempY_enable`, for the read of a sensor that is disabled;
  `tmp421_read()` in `drivers/hwmon/tmp421.c` does this.
- Invalid reading of an enabled sensor: neither document names an error code.
- Error from the callback: `hwmon_attr_show()` returns it unchanged as the
  result of the read.
- Alarm and fault names: the two documents list different sets. The channel
  alarms such as `in[0-*]_alarm`, and `temp[1-*]_fault`, are only in the
  "Alarms" section of `Documentation/hwmon/sysfs-interface.rst`; `inY_fault`,
  `humidityY_fault` and the humidity alarms are only in
  `Documentation/ABI/testing/sysfs-class-hwmon`.
