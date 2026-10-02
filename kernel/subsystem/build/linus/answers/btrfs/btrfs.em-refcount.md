- `btrfs_remove_extent_mapping()`: changes no reference count; the caller
  drops the tree's reference with a separate `btrfs_free_extent_map()`, as
  `try_release_extent_mapping()` and `btrfs_scan_inode()` do.
- `flags` and `generation` of an in-tree map: written under the tree write
  lock with no test of `refs`, for example in `btrfs_unpin_extent_cache()`,
  `btrfs_clear_em_logging()` and `btrfs_log_changed_extents()`.
- `start`, `len`, `disk_bytenr`, `disk_num_bytes`, `offset`, `ram_bytes` of an
  in-tree map: `try_merge_map()` writes them, and only when
  `refcount_read(&em->refs) <= 2`.
- `btrfs_rewrite_logical_zoned()` in `fs/btrfs/zoned.c`: writes `disk_bytenr`
  of the map of an ordered extent in place, under the write lock, no `refs`
  test.
- Holders of a reference read members without the tree lock, for example
  `btrfs_do_readpage()`; the `refs` test in `try_merge_map()` is what keeps a
  merge from changing them.
