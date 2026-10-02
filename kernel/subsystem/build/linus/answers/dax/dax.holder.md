- `fs_dax_get_by_bdev()` with a NULL holder: takes the reference, claims
  nothing, ignores `ops`; `ext4_alloc_sbi()` and `open_table_device()` in
  `drivers/md/dm.c` do this.
- `fs_dax_get_by_bdev()` with a non-NULL holder when a holder is already set:
  returns NULL, the same value as for a queue without DAX.
- Holder with NULL ops: allowed; `xfs_alloc_buftarg()` passes its mount, the
  `struct xfs_mount`, as the holder, with NULL ops without
  `CONFIG_MEMORY_FAILURE`, and `dax_holder_notify_failure()` returns
  `-EOPNOTSUPP` for NULL `holder_ops`.
- Non-NULL ops: `notify_failure` must be set; `dax_holder_notify_failure()`
  calls it unchecked.
- `fs_dax_get()`: defined in `drivers/dax/super.c` under `CONFIG_FS_DAX`, with
  no caller in this tree. See its body for the returns; easy to miss is that
  `-EOPNOTSUPP` means the bound driver is not `DAXDRV_FSDEV_TYPE`, and that the
  claim is made after `dax_read_unlock()`.
- **Unsafe usage**: `fs_dax_get()` with a NULL holder; it has no holder test,
  stores `hops` with `holder_data` still NULL, and `fs_put_dax()` with NULL
  never clears it.
  - Safe: NULL holder with NULL ops to `fs_dax_get_by_bdev()`, which skips the
    claim, as `ext4_alloc_sbi()` does.
- **Unsafe usage**: `fs_dax_get()` on a device whose private data is not a
  `struct dev_dax`; it casts `dax_get_private()` and locks `dev_dax->dev`.
  - Safe: a device made by `__devm_create_dev_dax()` in `drivers/dax/bus.c`,
    which passes the `struct dev_dax` to `alloc_dax()`.
- `fs_put_dax()` `holder` argument: the holder that was claimed, or NULL if
  none was; with NULL it only calls `put_dax()`, which is why
  `close_table_device()` can call `put_dax()` directly.
- Pagemap operations that reach `dax_holder_notify_failure()`:
  `pmem_pagemap_memory_failure()` in `fsdax_pagemap_ops`
  (`drivers/nvdimm/pmem.c`) and `fsdev_pagemap_memory_failure()` in
  `fsdev_pagemap_ops` (`drivers/dax/fsdev.c`); none is in `drivers/dax/super.c`.
- `dax_holder_notify_failure()`: runs `notify_failure` inside its own
  `dax_read_lock()` section; there is no holder lock, and nothing named
  dax_holder_lock.
