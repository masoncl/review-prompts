- `struct btrfs_file_extent` in `fs/btrfs/ordered-data.h`: describes the extent
  to be created; `btrfs_create_io_em()` builds the `struct extent_map` from it.
- Insertion: `btrfs_replace_extent_map_range(inode, em, true)`, not
  `btrfs_add_extent_mapping()`.
- `BTRFS_ORDERED_COMPRESSED`: the only checks in `btrfs_create_io_em()` itself
  are `compression != BTRFS_COMPRESS_NONE` and `num_bytes <= ram_bytes`.
- `offset` for a compressed write: may be non-zero; inside
  `btrfs_create_io_em()` tested only by `validate_extent_map()`
  (`offset + len <= ram_bytes`, alignment) under `CONFIG_BTRFS_DEBUG`;
  `btrfs_do_encoded_write()` passes `encoded->unencoded_offset`.
- `disk_num_bytes` for a compressed write: not compared with `ram_bytes`.
- `BTRFS_ORDERED_NOCOW`: rejected by the first `ASSERT()`; nothing returns an
  error for it.
- Callers keep NOCOW out: `nocow_one_range()` calls only when `is_prealloc`;
  `btrfs_create_dio_extent()` skips the call for `BTRFS_ORDERED_NOCOW`.
- **Unsafe usage**: passing `BTRFS_ORDERED_NOCOW` to `btrfs_create_io_em()`.
  - Unsafe: without `CONFIG_BTRFS_ASSERT` the checks generate no code, so a
    map with `EXTENT_FLAG_PINNED` replaces the existing one; the NOCOW branch
    of `btrfs_finish_one_ordered()` never calls `btrfs_unpin_extent_cache()`.
  - Safe: create only the ordered extent and reuse the existing map, as
    `nocow_one_range()` does when `is_prealloc` is false.
