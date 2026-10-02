- Failure: `dump_extent_map()` prints with `btrfs_crit()` and runs
  `ASSERT(0)`; `validate_extent_map()` returns void and no error reaches the
  caller.
- `CONFIG_BTRFS_DEBUG` without `CONFIG_BTRFS_ASSERT`: message only, and the
  map is still inserted; `fs/btrfs/Kconfig` does not make one select the
  other.
- Without `CONFIG_BTRFS_DEBUG`: both `validate_extent_map()` and
  `dump_extent_map()` return at once.
- Every map: `start` and `len` must be aligned to `fs_info->sectorsize`.
- Real extent, alignment: `disk_bytenr`, `disk_num_bytes`, `offset` and
  `ram_bytes` must be sector aligned too.
- Compressed map: no check of its own; it is only exempt from the two
  uncompressed checks, and `offset == 0` or `disk_num_bytes <= ram_bytes` is
  not required.
- Not checked for any map: that `len` is non-zero.
- Hole or inline map: only `offset == 0` plus the `start`/`len` alignment;
  `disk_num_bytes` and `ram_bytes` are not looked at.
- Call sites: `add_extent_mapping()` before `tree_insert()`,
  `replace_extent_mapping()`, and `try_merge_map()` after each merge.
- `btrfs_add_extent_mapping()`: separately asserts `em->start == 0` for an
  `EXTENT_MAP_INLINE` map.
