- There is no EXTENT_MAP_DELALLOC here; `fs/btrfs/extent_map.h` has
  `EXTENT_MAP_LAST_BYTE` `(u64)-4`, `EXTENT_MAP_HOLE` `(u64)-3` and
  `EXTENT_MAP_INLINE` `(u64)-2`.
- Compressed inline map: `btrfs_extent_item_to_extent_map()` sets the
  compression bit on an inline map, so `btrfs_extent_map_is_compressed()`
  being true does not make `disk_bytenr` a disk address.
- `EXTENT_FLAG_PREALLOC` map: passes `< EXTENT_MAP_LAST_BYTE`, yet reads
  treat it as a hole; see `btrfs_do_readpage()`, `btrfs_dio_iomap_begin()`
  and `btrfs_encoded_read()`.
- **Potentially unsafe usage**: using `em->disk_bytenr` or
  `btrfs_extent_map_block_start()` as a disk address with no sentinel test.
  - Unsafe: when the map can be a hole or inline, as any map from
    `btrfs_get_extent()` can; `btrfs_extent_map_block_start()` returns the
    sentinel unchanged and the address lands near 2^64 or wraps.
  - Safe: after `em->disk_bytenr < EXTENT_MAP_LAST_BYTE`, as
    `btrfs_get_extent_allocation_hint()` does.
  - Safe: after equality tests against both `EXTENT_MAP_HOLE` and
    `EXTENT_MAP_INLINE`; `btrfs_do_readpage()` computes the address first
    and tests both before `submit_extent_folio()`.
  - Safe: when `EXTENT_FLAG_PREALLOC` is set, as in `btrfs_zero_range()`;
    `btrfs_extent_item_to_extent_map()` returns for an item `disk_bytenr` of
    0 before it sets the flag.
