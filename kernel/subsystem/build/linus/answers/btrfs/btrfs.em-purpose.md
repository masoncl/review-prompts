- Map on `modified_extents` that a fast fsync still has to log: can still be
  dropped; `btrfs_log_changed_extents()` logs only maps on that list, so
  `btrfs_scan_inode()` compensates with `btrfs_set_inode_full_sync()`.
- `btrfs_drop_extent_map_range()`: removes a listed map that lies wholly in
  the range without setting full sync; it sets full sync when a listed map
  that is still in the tree crosses the range boundary and no split map could
  be allocated.
- Callers that fail to allocate a replacement map: drop the range and call
  `btrfs_set_inode_full_sync()`, for example `fill_holes()` in
  `fs/btrfs/file.c` and `btrfs_cont_expand()`.
- Data relocation inode: `setup_relocation_extent_mapping()` inserts a pinned
  map whose `disk_bytenr` is `rc->cluster.start`, the extents being read,
  while the inode's file extent items (from `prealloc_file_extent_cluster()`)
  are prealloc extents elsewhere; this map cannot be rebuilt from the items.
