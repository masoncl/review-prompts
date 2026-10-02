- `try_merge_map()`: edits the surviving map in place; besides `start`, `len`,
  `generation` and `flags` it rewrites, for a real extent, `disk_bytenr`,
  `disk_num_bytes`, `ram_bytes` and `offset` through `merge_ondisk_extents()`.
- Merged map: `disk_bytenr` is the lower of the two, `disk_num_bytes` and
  `ram_bytes` are both the span of the two on-disk extents; two different,
  adjacent on-disk extents merge too, so the result may match no item.
- `try_merge_map()` callers: `setup_extent_mapping()` when `modified` is
  false, `btrfs_unpin_extent_cache()`, `btrfs_clear_em_logging()`.
- `btrfs_drop_extent_map_range()`: leaves the size and address members of the
  old map alone; it builds new maps and puts them in with
  `replace_extent_mapping()` or, for a tail piece after the old map was
  replaced, `add_extent_mapping()`.
- There is no split_extent_map() here; `btrfs_split_extent_map()` does that,
  and each piece gets its own `disk_bytenr`, `disk_num_bytes` and `ram_bytes`
  both equal to the piece's `len`, and `offset` 0.
- `merge_extent_mapping()`: on `-EEXIST` in `btrfs_add_extent_mapping()`,
  trims `start` and `len` of the new map to the free gap and, for a real
  extent, advances `offset`, so an inserted map can cover only part of its
  item's range.
