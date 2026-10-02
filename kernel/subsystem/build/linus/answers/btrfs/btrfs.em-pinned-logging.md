- Pure NOCOW write: no map is created or pinned; `btrfs_finish_one_ordered()`
  leaves before `btrfs_unpin_extent_cache()` for `BTRFS_ORDERED_NOCOW`.
- Pinned map on the list: `generation` is `-1`, so the
  `em->generation < trans->transid` test in `btrfs_log_changed_extents()`
  does not skip it; a fast fsync can log it while it is still pinned.
- `btrfs_remove_extent_mapping()` and `replace_extent_mapping()`: warn on a
  pinned map; `btrfs_drop_extent_map_range()` clears the flag first.
- `btrfs_log_changed_extents()`: leaves `modified_extents` empty, whether it
  logs a map or not.
- `btrfs_log_inode()`: a full fsync with `LOG_INODE_ALL` empties the list
  without logging from it.
- `EXTENT_FLAG_LOGGING` set: `em->list` links the map into the private list
  of `btrfs_log_changed_extents()`, or is empty once the map is taken off
  that list for `log_one_extent()`; it is never on `modified_extents`.
- `btrfs_log_changed_extents()` drops the tree lock around each
  `log_one_extent()`; the map can leave the tree meanwhile, hence the
  `btrfs_extent_map_in_tree()` test in `btrfs_clear_em_logging()`.
- **Potentially unsafe usage**: taking a map that is on `modified_extents`
  off the list, or out of the tree, while the file keeps the extent.
  - Unsafe: `generation` is not below `btrfs_get_fs_generation()`, full sync
    is not set, no replacement is added as modified and the map lacks
    `EXTENT_FLAG_LOGGING`; `btrfs_log_changed_extents()` logs only maps on
    the list, so a fast fsync omits the extent.
  - Safe: `generation` below the current one, as
    `try_release_extent_mapping()` tests; `btrfs_log_changed_extents()` skips
    such maps anyway.
  - Safe: call `btrfs_set_inode_full_sync()` while holding `i_mmap_lock`, as
    `btrfs_scan_inode()` does for read; `btrfs_sync_file()` holds it for
    write from reading the flag until the inode is logged.
  - Safe: add the replacement as modified, as `btrfs_drop_extent_map_range()`
    does for the pieces and `btrfs_replace_extent_map_range()` with
    `modified` true.
  - Safe: the map has `EXTENT_FLAG_LOGGING`, as `try_release_extent_mapping()`
    tests; the logger holds its own reference.
