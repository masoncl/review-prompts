- `hwmon_free_attrs()`: makes no test of ownership; it does not look at the
  `show` callback or at the name.
- Ownership is by location: `hwmon_dev_release()` passes only
  `hwdev->group.attrs_const` to `hwmon_free_attrs()`.
- `hwdev->group`: the one group the core builds; it is embedded in
  `struct hwmon_device`, not allocated, and freed with the device.
- `hwmon_free_attrs()`: applies `to_hwmon_attr()` and `kfree()` to every
  entry, so every pointer in that array must come from `hwmon_genattr()`.
- `hwmon_free_attrs()`: dereferences the array without a NULL test;
  `hwmon_dev_release()` tests `hwdev->group.attrs_const` before the call.
- Attribute name: points into the `name` buffer of
  `struct hwmon_device_attribute`, except for `hwmon_chip`, where it points
  at the static string in `hwmon_chip_attrs`.
- Allocation calls: `kzalloc_obj()` in `hwmon_genattr()`, `kzalloc_objs()`
  for the array in `__hwmon_create_attrs()` and for `hwdev->groups` in
  `__hwmon_device_register()`; the core does not call `kzalloc()` or
  `kcalloc()` for these.
- Field names: the core writes `attrs_const` in `struct attribute_group`
  and `show_const` and `store_const` in `struct device_attribute`, not
  `attrs`, `show` and `store`.
