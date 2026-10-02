- `lockdep_assert_held_write()` on the tree lock: in `add_extent_mapping()`
  (so `btrfs_add_extent_mapping()`), `btrfs_remove_extent_mapping()`,
  `btrfs_clear_em_logging()`, `replace_extent_mapping()` and
  `btrfs_scan_inode()`.
- `btrfs_lookup_extent_mapping()` and `btrfs_search_extent_mapping()`: no
  assertion; lockdep does not catch a lookup without the lock.
- `btrfs_unpin_extent_cache()`: takes the write lock itself.
- `btrfs_split_extent_map()`: locks the file range in `inode->io_tree` with
  `btrfs_lock_extent()`, then takes the write lock; the caller holds neither.
- `btrfs_drop_extent_map_range()`: holds the write lock across the whole loop.
- Lock dropped and retaken (`cond_resched_rwlock_write()`): only in
  `drop_all_extent_maps_fast()`, reached with `start == 0`,
  `end == (u64)-1` and `skip_pinned` false.
- `btrfs_drop_extent_map_range()` calls `btrfs_alloc_extent_map()`
  (`GFP_NOFS`) twice before it locks; the caller must be able to sleep.
- Range lock in the io tree: stated in the comments above
  `btrfs_drop_extent_map_range()` and `btrfs_replace_extent_map_range()`;
  neither function checks it.
- Callers without the range lock exist on an inode being torn down, for
  example `evict_inode_truncate_pages()` (asserts `I_FREEING`) and
  `btrfs_destroy_inode()`.
