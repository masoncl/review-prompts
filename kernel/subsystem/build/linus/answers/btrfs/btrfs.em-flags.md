- Flag set: seven bits in `fs/btrfs/extent_map.h`, including
  `EXTENT_FLAG_MERGED`; there is no EXTENT_FLAG_FILLING and no
  EXTENT_FLAG_COMPRESSED.
- Merge: `can_merge_extent_map()` refuses `EXTENT_FLAG_PINNED`, any
  compression bit, `EXTENT_FLAG_LOGGING`, and a map on `modified_extents`;
  `mergeable_maps()` needs equal `flags` apart from `EXTENT_FLAG_MERGED`.
- Drop: `EXTENT_FLAG_PINNED` is the only `flags` bit that, when set, makes a
  dropper leave a map in the tree: `btrfs_drop_extent_map_range()` with
  `skip_pinned` true, `btrfs_scan_inode()` and
  `try_release_extent_mapping()`.
- `btrfs_drop_extent_map_range()` with `skip_pinned` false: drops pinned maps
  too.
- `EXTENT_FLAG_LOGGING`: does not protect a map from removal; on removal it
  only makes `btrfs_remove_extent_mapping()` and `replace_extent_mapping()`
  leave `em->list` alone; `try_release_extent_mapping()` removes such a map on
  purpose.
- There is no remove_extent_mapping() here; `btrfs_remove_extent_mapping()`
  does that, and warns on a pinned map.
- `drop_all_extent_maps_fast()`: clears both `EXTENT_FLAG_PINNED` and
  `EXTENT_FLAG_LOGGING` before removal.
- Logged or not: no flag alone decides it; `btrfs_log_changed_extents()` takes
  maps from `modified_extents`, skips `generation < trans->transid` and
  prealloc maps at or beyond `i_size`, and sets `EXTENT_FLAG_LOGGING` on the
  rest.
- Never cleared on a map: the three compression bits,
  `EXTENT_FLAG_PREALLOC` and `EXTENT_FLAG_MERGED`.
- Write into a prealloc range: the map is replaced by a new one from
  `btrfs_create_io_em()`, which does not set `EXTENT_FLAG_PREALLOC`.
- `EXTENT_FLAG_MERGED`: tested only by `defrag_lookup_extent()`, which
  discards the map and rebuilds one from the item with `defrag_get_extent()`.
- Compression helpers: `btrfs_extent_map_set_compression()`,
  `btrfs_extent_map_compression()` and `btrfs_extent_map_is_compressed()`
  all carry the `btrfs_` prefix.
