- `drivers/hwmon/` has exactly three subdirectories: `drivers/hwmon/occ/`,
  `drivers/hwmon/peci/` and `drivers/hwmon/pmbus/`; each has its own `Kconfig`
  and `Makefile`.
- `drivers/hwmon/occ/`: `common.c` and `sysfs.c` link into one module,
  `occ-hwmon-common`, under `CONFIG_SENSORS_OCC`; `common.h` is its header.
- `drivers/hwmon/peci/`: has no shared C file; `common.h` holds two structs
  and two inline helpers.
- `CONFIG_SENSORS_PECI`: builds no object; its only use in a Makefile is
  `obj-$(CONFIG_SENSORS_PECI) += peci/` in `drivers/hwmon/Makefile`.
- `hwmon_lock()` and `hwmon_unlock()`: defined and exported in
  `drivers/hwmon/hwmon.c`; `DEFINE_GUARD()` in `include/linux/hwmon.h` makes
  `guard(hwmon_lock)(dev)` available.
- `CONFIG_HWMON_DEBUG_CHIP`: no C file tests it; its only use is
  `ccflags-$(CONFIG_HWMON_DEBUG_CHIP) := -DDEBUG` in `drivers/hwmon/Makefile`,
  and none of the three subdirectory `Makefile`s sets ccflags.
