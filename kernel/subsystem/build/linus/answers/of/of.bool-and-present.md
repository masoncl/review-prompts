- `of_property_read_bool()` on a property with nonzero `length`: prints with
  plain `pr_warn()` on every call; not `WARN()`, not once-only, not rate
  limited.
- `fwnode_property_read_bool()` and `device_property_read_bool()` on an OF
  node: reach `of_property_read_bool()` through
  `of_fwnode_property_read_bool()` in `drivers/of/property.c`, so they print
  the same warning.
- `fwnode_property_present()` and `device_property_present()` on an OF node:
  reach `of_property_present()` through `of_fwnode_property_present()`; no
  warning.
