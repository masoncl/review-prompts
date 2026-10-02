- Compressed map, `offset`: can be non-zero; `btrfs_create_io_em()` accepts
  `num_bytes <= ram_bytes` with a caller-given `offset` for
  `BTRFS_ORDERED_COMPRESSED`, and `btrfs_drop_extent_map_range()` advances
  `offset` on a split.
- Merged real extent map: `disk_num_bytes == ram_bytes` always; `len` equals
  them only when the merged maps together cover the whole span.
- Hole map: `disk_num_bytes` 0 and `offset` 0; `ram_bytes` depends on the
  creator (0 for the implicit hole built in `btrfs_get_extent()`, `len` from
  `fill_holes()` and from a split, the item's value from
  `btrfs_extent_item_to_extent_map()`).
- Inline map: `len` is the sector size, `offset` 0, `ram_bytes` the item's
  value, `disk_num_bytes` never set (0); it can carry a compression bit.
