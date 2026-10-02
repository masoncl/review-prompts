- `Documentation/ABI/testing/sysfs-class-hwmon`: the authority on the unit and
  the RO/RW mode of the standard attributes it lists; it is in the
  `MAINTAINERS` entry "HARDWARE MONITORING".
- `Documentation/hwmon/sysfs-interface.rst`: gives the names, the channel
  numbering, the alarm semantics and how to interpret written values; it gives
  a `Unit:` line for only four power and energy entries and points to the ABI
  file for the rest.
- Attribute spelling differs between the two: `in[0-*]_min` in
  `sysfs-interface.rst`, `/sys/class/hwmon/hwmonX/inY_min` in the ABI file.
- `Documentation/hwmon/hwmon-kernel-api.rst`: its copy of `struct hwmon_ops`
  lists only `is_visible`, `read` and `write`; `visible` and `read_string` are
  described only in the kerneldoc in `include/linux/hwmon.h`.
- There is no writing-drivers.rst under `Documentation/hwmon/`;
  `hwmon-kernel-api.rst` and `submitting-patches.rst` cover that ground.
- `Documentation/hwmon/` is flat: drivers under `drivers/hwmon/pmbus/`,
  `drivers/hwmon/occ/` and `drivers/hwmon/peci/` are documented there too, for
  example `Documentation/hwmon/occ.rst`.
- Per-driver file name: not always the source file name; for example
  `Documentation/hwmon/inspur-ipsps1.rst` documents
  `drivers/hwmon/pmbus/inspur-ipsps.c`.
