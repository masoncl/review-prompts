- Ordering rule: stated in the kerneldoc of `folio_lock()` in
  `include/linux/pagemap.h`: ascending index within one `struct
  address_space`; across two, the one at the lower address first.
- `vfs_lock_two_folios()` in `fs/remap_range.c`: compares `folio->index`
  only, never the mapping; locks once when both arguments are the same folio.
- There is no lock_two_folios() helper in this tree; `vfs_lock_two_folios()`
  is static to `fs/remap_range.c`.
- `move_pages_ptes()` in `mm/userfaultfd.c`: locks the source folio only;
  for a present PTE, `folio_trylock()` under the PTE lock, and on failure for
  a small folio drops the PTE lock, calls `folio_lock()` and retries; for a
  large folio it returns `-EAGAIN`.
- There is no unmap_and_move() here; `migrate_folio_unmap()` in
  `mm/migrate.c` locks the source folio and takes the destination with
  `folio_trylock()` only.
- `migrate_pages_batch()`: batches only for `MIGRATE_ASYNC`, where
  `migrate_folio_unmap()` gives up when `folio_trylock()` fails; for other
  modes `migrate_pages_sync()` passes one folio per call, and a
  `VM_WARN_ON_ONCE()` checks the list length.
- `migrate_folio_unmap()` under `PF_MEMALLOC`: never blocks in
  `folio_lock()`, in any mode.
- `unpin_user_pages_dirty_lock()` in `mm/gup.c`: does not call
  `folio_mark_dirty_lock()`; it open-codes lock, `folio_mark_dirty()`, unlock
  per folio, and takes no lock for a folio that is already dirty.
- **Potentially unsafe usage**: blocking in `folio_lock()` while holding the
  lock of another folio.
  - Unsafe: when another task can lock the second folio and nothing fixes
    the order in which the two are taken, as with folios from a GUP array,
    whose order is unrelated to the `folio_lock()` rule.
  - Safe: when the second folio was just allocated and never published, as
    `migrate_device_coherent_folio()` in `mm/migrate_device.c` locks the
    result of `folio_alloc()`.
  - Safe: when the two folios are always taken in one fixed order, as
    `mext_folio_double_lock()` in `fs/ext4/move_extent.c` locks the folio of
    the inode at the lower address first, for two different inodes; the
    kerneldoc of `folio_lock()` states the order.
