- Condition for the copy: `mfd_add_device()` tests `cell->pdata_size`, not
  `cell->platform_data`.
- `pdata_size` zero: `dev_get_platdata()` in the child returns `NULL`; it does
  not return the cell copy.
- `pdata_size` nonzero with `platform_data` `NULL`:
  `platform_device_add_data()` stores `NULL` and returns 0, so the child gets
  `NULL` and the add does not fail.
- **Potentially unsafe usage**: `platform_data = &ptr` with
  `pdata_size = sizeof(ptr)`, which copies the pointer value and not the
  object.
  - Unsafe: when the child casts `dev_get_platdata()` to the object type;
    `platform_device_add_data()` allocated only `pdata_size` bytes, so the
    child reads past the allocation.
  - Unsafe: when the object `ptr` refers to is freed before the child is
    removed.
  - Safe: when the child reads one pointer back, as `ti_tscadc_dev_get()` in
    `include/linux/mfd/ti_am335x_tscadc.h` does, and the object is devm memory
    of the parent whose remove calls `mfd_remove_devices()`, as
    `ti_tscadc_probe()` and `ti_tscadc_remove()` do.
