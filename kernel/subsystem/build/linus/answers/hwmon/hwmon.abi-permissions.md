- "Attribute access" in `Documentation/hwmon/sysfs-interface.rst`: states the
  rule in words, with no octal mode: standard attributes are world readable,
  and writeable ones are writeable only for privileged users.
- RO, RW and WO tags per attribute: in
  `Documentation/ABI/testing/sysfs-class-hwmon`;
  `Documentation/hwmon/sysfs-interface.rst` defines the three abbreviations
  and tags only a few entries.
- Octal modes: `Documentation/hwmon/hwmon-kernel-api.rst` gives 0, 0444 and
  0644 as typical `is_visible` results.
- 0200: named by `Documentation/hwmon/hwmon-kernel-api.rst` only for
  `SENSOR_DEVICE_ATTR_WO()` and `SENSOR_DEVICE_ATTR_2_WO()` in
  `include/linux/hwmon-sysfs.h`.
- Mode with read bits and no matching callback: `hwmon_genattr()` returns
  `-EINVAL` and the registration fails; there is no warning.
- Matching read callback: `read_string` for an attribute that
  `is_string_attr()` matches (the label of each type), `read` for any other.
- Mode with write bits and no `write`: `hwmon_genattr()` returns `-EINVAL`.
- `visible` in `struct hwmon_ops`, in-tree example: `.visible = 0444` in
  `drivers/hwmon/i5500_temp.c`; "Attribute visibility" says how the core uses
  the member.
- Mode bits outside 0664: `create_files()` in `fs/sysfs/group.c` prints a
  `WARN()` and drops them, so 0666 becomes 0664.
