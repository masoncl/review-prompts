- `__hwmon_device_register()`: the walk starts at the driver's device and
  follows `parent` upward until a device has an `of_node`, not one level.
- Only `of_node` is tested and copied; the assignment is to `hdev->of_node`
  directly.
- `drivers/hwmon/hwmon.c` does not call `device_set_node()` and does not set
  `fwnode`; an ACPI or software node of the parent is not inherited.
- `label`: read with `device_property_present()` and
  `device_property_read_string()` on the driver's device, before the walk; an
  ancestor's `label` is not used.
- `hdev->of_node` NULL: `HWMON_C_REGISTER_TZ` and `HWMON_C_PEC` are both
  ignored without a message and registration succeeds.
