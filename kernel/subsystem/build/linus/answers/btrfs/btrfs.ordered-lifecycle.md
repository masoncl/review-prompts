- Order in `btrfs_finish_one_ordered()` after the transaction is joined:
  1. `btrfs_insert_raid_extent()`
  2. file extent: `btrfs_mark_extent_written()` for PREALLOC, otherwise
     `insert_ordered_extent_file_extent()`
  3. `btrfs_unpin_extent_cache()`
  4. `add_pending_csums()`
  5. clear `EXTENT_DELALLOC_NEW` with `EXTENT_ADD_INODE_BYTES`
  6. `btrfs_inode_safe_disk_i_size_write()` and
     `btrfs_update_inode_fallback()`
- Checksums go into the csum tree after the file extent item, not before.
- `btrfs_add_ordered_sum()`: only queues on `csum_list`.
- `add_pending_csums()`: inserts with `btrfs_insert_data_csums()`; there is no
  btrfs_csum_file_blocks here.
- NOCOW: step 1 still runs; then only step 6.
- NOCOW with a non-empty `csum_list`: an `ASSERT()`, then `-EINVAL` and a
  transaction abort.
- There is no unpin_extent_cache() here; `btrfs_unpin_extent_cache()` in
  `fs/btrfs/extent_map.c` does that.
- `btrfs_unpin_extent_cache()`: clears `EXTENT_FLAG_PINNED`, sets
  `generation`, tries to merge the map with its neighbours.
- `btrfs_unpin_extent_cache()` failure: `-ENOENT` (no map) or `-EUCLEAN`
  (wrong start) aborts the transaction.
- Truncated with `truncated_len > 0`: only the item's `num_bytes` becomes
  `truncated_len`; `ram_bytes` and `disk_num_bytes` stay, and unpin uses the
  full `num_bytes`.
- Truncated with `truncated_len > 0` and no error: the extent maps from
  `file_offset + truncated_len` on are dropped; no reserved space is freed.
- `btrfs_free_reserved_extent()`: the only way space is returned, on error or
  `truncated_len` 0, not for NOCOW or PREALLOC, and not after
  `insert_ordered_extent_file_extent()` succeeded; there is no pinning on
  this path.
- Error marking: `btrfs_mark_ordered_extent_error()` sets
  `BTRFS_ORDERED_IOERR` and, if the bit was clear, calls
  `mapping_set_error()`; no folio flag is set.
- Extent map drop on error or truncate: skipped for the free space inode.
