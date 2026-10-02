- Failing cell is cell 0 of the call: `mfd_add_devices()` removes nothing;
  the cleanup is under `if (i)`. Children from earlier calls stay registered.
- Failing cell is a later one: the cleanup is `mfd_remove_devices()`, so
  children with `MFD_DEP_LEVEL_HIGH` stay registered, from this call and from
  earlier ones.
- **Potentially unsafe usage**: returning the error of `mfd_add_devices()`
  with no removal call in the error path.
  - Unsafe: when an earlier plain `mfd_add_devices()` call added children to
    the same parent, which stay registered when the failing cell is cell 0,
    or when a cell already registered has `MFD_DEP_LEVEL_HIGH`; those
    children stay registered while the driver core releases the parent's
    devres.
  - Safe: when it is the only call on the parent and no cell sets `level`,
    as in `dln2_probe()`; the `if (i)` branch already removed what the call
    added.
  - Safe: when the earlier children were added with `devm_mfd_add_devices()`,
    as in `bcm2835_pm_probe()`; `devm_mfd_dev_release()` removes them when
    the probe fails.
