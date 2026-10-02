- Prefix: every function declared or defined in `fs/btrfs/extent_map.h`
  carries `btrfs_`, the inline helpers and the slab setup included, for
  example `btrfs_extent_map_end()`, `btrfs_alloc_extent_map()`,
  `btrfs_free_extent_map()`, `btrfs_extent_map_init()`.
- Unprefixed spellings such as free_extent_map(), extent_map_end() or
  lock_extent() name no function in this tree; they survive only in comments.
- Unprefixed extent map functions are outside the header: the static helpers
  in `fs/btrfs/extent_map.c` (for example `try_merge_map()`,
  `lookup_extent_mapping()`) and, for example,
  `try_release_extent_mapping()` in `fs/btrfs/extent_io.c`.
- Functions in the header that take `struct extent_map_tree *`: only
  `btrfs_extent_map_tree_init()`, `btrfs_lookup_extent_mapping()` and
  `btrfs_search_extent_mapping()`.
- Functions in the header that take `struct btrfs_inode *`: every function
  that can insert or remove a map, `btrfs_add_extent_mapping()` and
  `btrfs_remove_extent_mapping()` included.
- Functions in the header that take `struct btrfs_fs_info *`: the shrinker
  entry points `btrfs_free_extent_maps()` and
  `btrfs_init_extent_map_shrinker_work()`.
