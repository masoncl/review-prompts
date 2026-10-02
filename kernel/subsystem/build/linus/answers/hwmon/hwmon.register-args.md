- `chip == NULL`: `ERR_PTR(-EINVAL)` from `hwmon_device_register_with_info()`,
  and so from the devm form, whether or not `extra_groups` is given.
- `chip` non-NULL: `-EINVAL` unless `chip->ops`, `chip->info`, and one of
  `chip->ops->visible` or `chip->ops->is_visible` are set.
- NULL `name`, `hwmon_device_register_with_info()`: `ERR_PTR(-EINVAL)`.
- NULL `name`, `devm_hwmon_device_register_with_info()`: accepted; the name
  becomes `devm_hwmon_sanitize_name(dev, dev_name(dev))`, so it differs per
  instance.
- Failure of that sanitize call: returned through `ERR_CAST()`; PTR_ERR_CAST
  is not in this tree.
- In-tree caller that passes a NULL name to the devm form: for example
  `tja11xx_hwmon_register()` in `drivers/net/phy/nxp-tja11xx.c`.
