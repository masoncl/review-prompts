- The driver exists: `fsdev_dax_driver` in `drivers/dax/fsdev.c`, type
  `DAXDRV_FSDEV_TYPE`, module `fsdev_dax`, built with `CONFIG_DEV_DAX_FSDEV`
  (no prompt, depends on `DEV_DAX` and `FS_DAX`).
- Filesystem entry point: `fs_dax_get()` in `drivers/dax/super.c` takes a
  `struct dax_device` with no block device; `fs_put_dax()` releases it.
- `fs_dax_get()` returns: `-ENODEV` if the device is dead or unbound,
  `-EOPNOTSUPP` if the bound driver is not `DAXDRV_FSDEV_TYPE`, `-EBUSY` if
  another holder is set.
- `fs_dax_get()` has no caller in this tree.

| | `dev_dax_probe()` | `fsdev_dax_probe()` |
|---|---|---|
| `pgmap->type` | `MEMORY_DEVICE_GENERIC` | `MEMORY_DEVICE_FS_DAX` |
| `pgmap->vmemmap_shift` | set when `dev_dax->align` > `PAGE_SIZE` | left 0, reset to 0 on a static pgmap |
| `pgmap->ops`, `pgmap->owner` | not set | `fsdev_pagemap_ops`, the `struct dev_dax`; cleared on unbind |
| `struct dax_operations` | none | `dev_dax_ops`, installed with `dax_set_ops()`, cleared on unbind |
| character device | `dax_fops`, with `dax_mmap_prepare()` | `fsdev_fops`, no mmap handler |

- Folio reset: `fsdev_clear_folio_state()` runs `dax_folio_reset_order()` on
  every folio of every range at probe, and again on unbind as a devm action.
- `dev_dax->cached_size`: written by `fsdev_dax_probe()`, read by
  `__fsdev_dax_direct_access()` to bound the returned page count.
- `fsdev_pagemap_memory_failure()`: forwards to `dax_holder_notify_failure()`,
  so the holder set by `fs_dax_get()` receives it.
- Binding is never automatic: `dax_match_type()` only ever selects
  `DAXDRV_DEVICE_TYPE` or `DAXDRV_KMEM_TYPE`, so `dax_bus_match()` matches
  this driver only through `dax_match_id()`.
- To bind: unbind the device from its current driver, then write its name
  (form "dax%d.%d") to the `new_id` attribute of `fsdev_dax`; `do_id_store()`
  adds the name and calls `driver_attach()`.
- Driver `bind` attribute: `bind_store()` requires `dax_bus_match()` to
  succeed, so it works only after the name is in `new_id`.
- `dax_bus_type` does not set `driver_override`.
