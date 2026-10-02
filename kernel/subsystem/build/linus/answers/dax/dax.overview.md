- `struct dax_device` of a `struct dev_dax`: created with NULL ops and killed at
  once by `__devm_create_dev_dax()`. It is alive only while device_dax or fsdev
  is bound (`run_dax()`), never under kmem.
- `struct dax_device` lifetime: the refcount of its embedded inode (`igrab()`,
  `put_dax()`). `dax_read_lock()` and `DAXDEV_ALIVE` only fence operations
  against `kill_dax()`; they do not keep the object.
- `struct dev_dax` ranges: a seed device has `nr_range` 0 and `ranges` NULL;
  `dax_bus_probe()` refuses to bind it, so no driver's probe sees that state.
- `struct dax_region`: has no lock of its own. The global `dax_region_rwsem`
  and `dax_dev_rwsem` in `drivers/dax/bus.c` cover every region and device.
- Memory failure with no holder ops: `memory_failure_dev_pagemap()` falls back
  to `mf_generic_kill_procs()`, which finds the file through `folio->mapping`
  and `folio->index`.
- `iomap->addr` under `IOMAP_DAX`: a byte offset into `iomap->dax_dev`, not a
  sector. `dax_iomap_pgoff()` adds no partition offset; the filesystem adds
  the `start_off` that `fs_dax_get_by_bdev()` returned.
- `dax_layout_busy_page()`: finds a busy page, does not wait for it.
  `dax_break_layout()` waits, when given a callback.
- `DAX_PMD` entry and its folio: `fs/dax.c` builds the PMD-order folio from
  order-0 pages when the entry is associated (`dax_folio_init()`) and splits it
  when the last association goes (`dax_folio_reset_order()`).
- device_dax folios: sized once at probe from `pgmap->vmemmap_shift`.
- device_dax folios and `folio->mapping`: `dax_set_mapping()` in
  `drivers/dax/device.c` points them at the mapping of the `struct dax_device`
  inode, with no `i_pages` entry. `dax_lock_folio()` tells them from
  filesystem folios by `S_ISCHR()` on the host inode and takes no entry lock.
