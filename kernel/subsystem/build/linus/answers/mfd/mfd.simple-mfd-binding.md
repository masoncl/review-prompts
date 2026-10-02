- `simple_pm_bus_of_match` in `drivers/bus/simple-pm-bus.c`: contains
  `simple-mfd` with `.data = ONLY_BUS`, so the `simple-pm-bus` platform driver
  matches a platform device whose compatible list contains `simple-mfd` at any
  position.
- Decline test in `simple_pm_bus_probe()`: only whether the matched string is
  at index 0 of `compatible`; it does not look for another driver.
- `"syscon", "simple-mfd"`: declined with `-ENODEV`, like any list where
  `simple-mfd` is not first.
- `of_match_device()` returns the entry that matches earliest in the node's
  compatible list; the index test runs only when that entry has `.data` set.
- Entries without `.data`: `simple-pm-bus` and six `fsl,` entries; a node whose
  best match is one of them takes the full clock, runtime PM and
  `of_platform_populate()` path even with `simple-mfd` later in its list.
- Driver override: tested with `device_has_driver_override()` from
  `include/linux/device.h`; `struct platform_device` has no `driver_override`
  member in this tree.
- Probe with a driver override set: returns 0 before any match lookup and
  calls neither `of_platform_populate()` nor `pm_runtime_enable()`.
- Build: `obj-$(CONFIG_OF) += simple-pm-bus.o` in `drivers/bus/Makefile`;
  there is no Kconfig symbol for the driver, and `CONFIG_OF` is bool, so the
  driver is built in whenever `CONFIG_OF` is set.
