- There is no btrfs_extent_map_block_len() here; `extent_map_block_len()` is
  static in `fs/btrfs/extent_map.c`, called only by
  `extent_map_block_end()` for `mergeable_maps()`.
- `btrfs_extent_map_block_start()` on a compressed map: returns `disk_bytenr`
  without `offset`; `offset` can be non-zero there and counts decompressed
  bytes.
- `extent_map_block_len()` on a hole or uncompressed inline map: returns
  `len`.
- `extent_map_block_len()` on a compressed inline map: returns
  `disk_num_bytes`, which `btrfs_extent_item_to_extent_map()` never sets for
  inline, so 0.
- Code outside `fs/btrfs/extent_map.c`: open-codes the length with
  `btrfs_extent_map_is_compressed()`, as `log_extent_csums()` in
  `fs/btrfs/tree-log.c` does.
