- mfd_cell_enable() and mfd_cell_disable(): not in this tree. `struct
  mfd_cell` in `include/linux/mfd/core.h` has no enable or disable hook and
  no usage count field.
- Exports: `mfd_add_devices()`, `mfd_remove_devices()`,
  `mfd_remove_devices_late()` and `devm_mfd_add_devices()` all use plain
  `EXPORT_SYMBOL()`.
