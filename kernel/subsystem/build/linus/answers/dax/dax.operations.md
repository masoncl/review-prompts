- `struct dax_operations`: three members, `direct_access`, `zero_page_range`,
  `recovery_write`; it has no copy operations, and `dax_copy_from_iter()` and
  `dax_copy_to_iter()` never call the driver.
- `DAXDEV_NOCACHE` and `DAXDEV_NOMC`: the copy helpers test them on every
  device, with or without `ops`.
- NULL `dax_dev->ops`: `dax_direct_access()` and `dax_zero_page_range()` return
  `-EOPNOTSUPP`, tested after the alive test; `dax_recovery_write()` returns 0.
- `dax_recovery_write()`: no `dax_alive()` test; returns 0 for NULL
  `recovery_write`, and has no fallback copy.
- `dax_direct_access()`: a negative return from the driver comes back
  unconverted, for example `-EHWPOISON` from pmem; `dax_mem2blk_err()` is the
  caller's job, as in `dax_iomap_iter()`.
- `direct_access`: required whenever `ops` is non-NULL; nothing checks it and
  `dax_direct_access()` calls it unchecked.
- `zero_page_range`: checked only by `alloc_dax()`; `dax_set_ops()` installs
  `ops` without that check.
- `dax_set_ops()`: sets `ops` after allocation, `-EBUSY` if already set; NULL
  clears. `fsdev_dax_probe()` uses it on a device allocated with NULL `ops`.
- **Unsafe usage**: `dax_set_ops()` with NULL on a live device;
  `dax_direct_access()` and `dax_zero_page_range()` test `dax_dev->ops` and
  then read it again for the call.
  - Safe: clear after `kill_dax()` has returned; `fsdev_dax_probe()` registers
    `fsdev_clear_ops()` before `fsdev_kill()`, so devres runs the kill first.
- `_copy_from_iter_flushcache`: a macro for `_copy_from_iter_nocache` without
  `CONFIG_ARCH_HAS_UACCESS_FLUSHCACHE`; see `include/linux/uio.h`.
- `_copy_mc_to_iter`: a macro for `_copy_to_iter` without
  `CONFIG_ARCH_HAS_COPY_MC`, so `DAXDEV_NOMC` then changes nothing.
