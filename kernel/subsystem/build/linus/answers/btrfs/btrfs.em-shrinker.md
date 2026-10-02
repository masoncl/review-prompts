- `btrfs_scan_inode()` skips only pinned maps; it does not test
  `EXTENT_FLAG_LOGGING`.
- `btrfs_scan_inode()`, map on a list with `generation` not below
  `btrfs_get_fs_generation()`: calls `btrfs_set_inode_full_sync()`, then
  removes the map.
- `try_release_extent_mapping()`: never sets full sync; a listed map with
  current `generation` and no `EXTENT_FLAG_LOGGING` stays in the tree.
- `try_release_extent_mapping()` stops the walk at a pinned map or at
  `em->start != start`; it steps over a map whose range has `EXTENT_LOCKED`.
- `try_release_extent_mapping()` does not lock the range; it only tests the
  bit with `btrfs_test_range_bit_exists()`. There is no
  test_range_bit_exists() here.
- `try_release_extent_mapping()` has no gate on the gfp mask or on file size;
  `mask` only decides, on `need_resched()`, between `cond_resched()` and
  stopping.
- Tree lock for `btrfs_scan_inode()`: taken by `find_first_inode_to_shrink()`
  with `write_trylock()`, released by `btrfs_scan_root()`;
  `btrfs_scan_inode()` asserts it and never drops it, it stops scanning.
- `i_mmap_lock` in `btrfs_scan_inode()`: `down_read_trylock()` because the
  spinning tree lock is already held; on failure the inode is skipped.
- `btrfs_scan_inode()` runs in `btrfs_extent_map_shrinker_worker()`, a work
  item on `system_dfl_wq`, not in the reclaiming task;
  `btrfs_free_extent_maps()` only queues it.
