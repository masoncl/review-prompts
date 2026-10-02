- `drivers/mfd/mfd-core.c` exports four functions: `mfd_add_devices()`,
  `devm_mfd_add_devices()`, `mfd_remove_devices()` and
  `mfd_remove_devices_late()`.
- `mfd_add_hotplug_devices()` and `mfd_get_cell()`: `static inline` in
  `include/linux/mfd/core.h`, not in `drivers/mfd/mfd-core.c`.
- Children of a `simple-mfd` node: created by `of_platform_default_populate()`
  in `drivers/of/platform.c`; "simple-mfd" is an entry of its function-local
  `match_table[]`. No file under `drivers/mfd/` matches that string.
- `drivers/bus/simple-pm-bus.c`: for a node whose best match in
  `simple_pm_bus_of_match` is "simple-mfd", `simple_pm_bus_probe()` returns 0
  and binds when that string is the first `compatible` entry of the node, and
  `-ENODEV` otherwise. It creates no children in either case.
- `include/linux/mfd/core.h`: its header comment names
  drivers/mfd/mfd-core.h; no such file exists.
