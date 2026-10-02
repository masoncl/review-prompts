- The copy: `pdev->mfd_cell`, made by `kmemdup()` in `mfd_add_device()`; it is
  not `pdev->dev.platform_data` and `platform_device_add_data()` plays no part
  in it.
- Comment above `struct mfd_cell` in `include/linux/mfd/core.h`: says the copy
  becomes the platform data of the child; the code does not do that.
- Free: `kfree(pa->pdev.mfd_cell)` in `platform_device_release()`;
  `struct platform_object` has no pdata member.
- Members the core reads from the copy after `mfd_add_devices()` returns:
  `level`, `swnode` (tested only), `parent_supplies` and
  `num_parent_supplies`, all in `mfd_remove_devices_fn()`.
- **Potentially unsafe usage**: a cell member that points at storage which
  ends before the child is removed.
  - Unsafe: `swnode`; `swnode_register()` stores the pointer and copies
    neither the node nor its properties.
  - Unsafe: `parent_supplies`; `regulator_register_supply_alias()` stores each
    string pointer, and `mfd_remove_devices_fn()` reads the array again
    through the copy.
  - Unsafe: `resources[i].name`; the copied `struct resource` keeps the
    pointer.
  - Unsafe: any member that code reads later through `mfd_get_cell()` or
    `pdev->mfd_cell`; the copy then holds a dangling pointer.
  - Safe: the `resources` array, `name`, and `platform_data` with nonzero
    `pdata_size`; `mfd_add_device()` copies them with
    `platform_device_add_resources()`, `platform_device_alloc()` and
    `platform_device_add_data()` before it returns. For example
    `ti_tscadc_probe()` points `platform_data` at a local variable.
  - Safe: `of_compatible` and `acpi_match`; `mfd_add_device()` and
    `mfd_acpi_add_device()` are the only core readers, and both finish before
    `mfd_add_devices()` returns.
