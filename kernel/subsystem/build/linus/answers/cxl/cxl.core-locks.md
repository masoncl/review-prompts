- Root decoder's regions: the lock is `regions_lock`, a `struct mutex` in
  `struct cxl_root_decoder` (`drivers/cxl/cxl.h`). There is no range_lock in
  `drivers/cxl`.
- `regions_lock` protects: the `regions` xarray (regions by id) and the `dead`
  flag of the root decoder, and serializes region creation, deletion,
  auto-discovery and `kill_regions()`; it is taken only in
  `drivers/cxl/core/region.c`.
- `cxlmd->cxlds`: protected by `cxl_memdev_rwsem`, a static rwsem in
  `drivers/cxl/core/memdev.c`, not by `cxl_rwsem.region`.
- `cxl_memdev_rwsem` read side: `cxl_memdev_ioctl()` is the only holder; other
  code that dereferences `cxlmd->cxlds` does not take it.
- `cxl_memdev_rwsem` write side: also covers the `exclusive_cmds` bitmap of
  `struct cxl_mailbox`, see `set_exclusive_cxl_commands()`.
- `cxl_rwsem`: the object is defined in `drivers/cxl/core/hdm.c`, which is
  built without `CONFIG_CXL_REGION`; `drivers/cxl/core/region.c` is not.
- `mbox_mutex`: `cxl_pci_mbox_send()` in `drivers/cxl/pci.c` takes it with
  `mutex_lock()`; nothing in `drivers/cxl` calls `mutex_lock_io()`.
- `feat_mutex`: a second mutex in `struct cxl_mailbox`; `cxl_get_feature()`
  and `cxl_set_feature()` hold it across a multi-part transfer, so it nests
  outside `mbox_mutex`.
- `cxl_region_attach()`: has no lockdep assertion of its own;
  `cxl_port_attach_region()` asserts `cxl_rwsem.region` for write and
  `cxl_region_perf_data_calculate()` asserts `cxl_rwsem.dpa`.
