- `find_lock_delalloc_range()`: locks the folios, takes the range lock only to
  re-test `EXTENT_DELALLOC`, and drops it before returning.
- Range lock on writeback: taken by `cow_one_range()` (after
  `btrfs_reserve_extent()`), `nocow_one_range()` and
  `submit_one_async_extent()`, around the creation of the extent map and
  ordered extent.
- Release on writeback: `extent_clear_unlock_delalloc()`.
- There is no btrfs_find_lock_delalloc_range() and no
  lock_and_cleanup_extent_if_need() here; the names are
  `find_lock_delalloc_range()` and `lock_and_cleanup_extent()`.
- Buffered write, per folio in `copy_one_range()`: reserve space,
  `prepare_one_folio()`, then `lock_and_cleanup_extent()`, which always takes
  the range lock (a trylock with `nowait`).
- Buffered read: `lock_extents_for_read()` in `fs/btrfs/extent_io.c`, not
  `btrfs_lock_and_flush_ordered_range()`.
- Buffered read wait: the range is unlocked but the folio stays locked; it
  calls `btrfs_start_ordered_extent_nowriteback()` so its own range is not
  written back.
- `can_skip_ordered_extent()`: lets the read keep the range lock and not wait
  when the folio has private data and the block is dirty or uptodate.
- `btrfs_read_folio()`: unlocks the range after `btrfs_do_readpage()`, not at
  end of I/O; the folio is unlocked at end of I/O.
- `btrfs_finish_one_ordered()`: locks with
  `EXTENT_LOCKED | EXTENT_FINISHING_ORDERED`; takes no range lock for NOCOW.
- `try_release_extent_state()`: releases a folio whose range is locked, if
  `EXTENT_FINISHING_ORDERED` is set.
- Direct I/O order, in `lock_extent_direct()`: `EXTENT_DIO_LOCKED` first, then
  `EXTENT_LOCKED`, then the ordered extent lookup.
- Direct I/O wait: drops only `EXTENT_LOCKED`.
- `EXTENT_DIO_LOCKED`: conflicts only with itself, and only
  `fs/btrfs/direct-io.c` takes it, so it excludes other direct I/O and not
  buffered paths.
- `EXTENT_LOCKED` in direct I/O: cleared at the end of
  `btrfs_dio_iomap_begin()`, for reads and writes.
- `EXTENT_DIO_LOCKED` in direct I/O: writes clear it at the end of
  `btrfs_dio_iomap_begin()`; reads in `btrfs_dio_end_io()`, in
  `btrfs_dio_iomap_end()` for the part not submitted, or at the end of
  `btrfs_dio_iomap_begin()` for the part past the mapped length.
- Direct read that finds an ordered extent without `BTRFS_ORDERED_DIRECT`:
  returns `-ENOTBLK` (`-EAGAIN` with `IOMAP_NOWAIT`), does not wait.
- Direct write that finds page cache in the range: returns `-ENOTBLK`, or
  `-EAGAIN` with `IOMAP_NOWAIT`; no retry.
