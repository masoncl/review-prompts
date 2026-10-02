- `level`: read only by `mfd_remove_devices_fn()`, which skips a cell when
  `cell->level > *level`.

| Caller | Level passed | Removes |
|---|---|---|
| `mfd_remove_devices()` | `MFD_DEP_LEVEL_NORMAL` | normal cells only |
| `mfd_remove_devices_late()` | `MFD_DEP_LEVEL_HIGH` | every MFD child still registered, normal cells too |
| `devm_mfd_dev_release()` | calls `mfd_remove_devices()` | normal cells only |
| failure path of `mfd_add_devices()` | calls `mfd_remove_devices()` | normal cells only |

- `MFD_DEP_LEVEL_HIGH` in this tree: set by one cell, `madera-ldo1` in
  `madera_ldo1_devs`. It is a regulator that can supply DCVDD, which the
  parent holds through `regulator_get()`.
- `drivers/mfd/arizona-core.c`: sets no `level` and does not call
  `mfd_remove_devices_late()`.
- `mfd_remove_devices_late()`: its only caller is `madera_dev_exit()`.
- **Unsafe usage**: a cell with `MFD_DEP_LEVEL_HIGH` on a path that removes
  children only through `mfd_remove_devices()`, the devres release or the
  failure path of `mfd_add_devices()`; the child stays registered after the
  parent driver is gone.
  - Safe: call `mfd_remove_devices()`, release what the parent took from the
    HIGH child, then call `mfd_remove_devices_late()`, as `madera_dev_exit()`
    does. The level test in `mfd_remove_devices_fn()` defines the
    requirement.
