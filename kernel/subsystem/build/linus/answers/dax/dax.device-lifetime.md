- `run_dax()`: revives a device that `kill_dax()` killed. Declared in
  `drivers/dax/dax-private.h`, called from `dev_dax_probe()` and
  `fsdev_dax_probe()`.
- `DAXDEV_ALIVE` is not one-way: `__devm_create_dev_dax()` calls `kill_dax()`
  right after `alloc_dax()`, probe sets the bit, `kill_dev_dax()` clears it on
  unbind and again from `unregister_dev_dax()`.
- `kill_dax()` on every call: clears `holder_ops` and `holder_data` with plain
  stores after `synchronize_srcu()`; there is no holder lock.
- `dax_get_private()`: returns NULL while `DAXDEV_ALIVE` is clear, and has no
  lock assertion.
- `dax_alive()`: the `lockdep_assert_held()` on `dax_srcu` compiles to no check
  without lockdep; see `include/linux/lockdep.h`.
- `dax_srcu`: one domain for all devices, and sections nest. A
  `dax_direct_access()` call with no `dax_read_lock()` in the same function
  relies on the caller's section, as `dax_memzero()` and, through
  `dax_zero_page_range()`, `virtio_fs_zero_page_range()` do under the section
  that `dax_zero_iter()` opens.
- **Unsafe usage**: dereferencing a `kaddr` from `dax_direct_access()` after
  the `dax_read_unlock()` that ends the section it was obtained in;
  `kill_dax()` waits only for sections still open before the driver unmaps.
  - Safe: one section across the lookup and every access, as
    `copy_cow_page_dax()` and `dax_iomap_iter()` in `fs/dax.c` do.
  - Safe: `dax_iomap_direct_access()` unlocks before it returns `*kaddr`; the
    caller takes its own section around the call and the access, as
    `dax_unshare_iter()` and `dax_range_compare_iter()` do.
  - Safe: using only the returned page count after unlock, with NULL `kaddr`
    and NULL `pfn`, as `fuse_dax_mem_range_init()` does.
