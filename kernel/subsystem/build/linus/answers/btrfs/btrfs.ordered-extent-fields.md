- Names shared with the file extent item: `num_bytes`, `ram_bytes`,
  `disk_bytenr`, `disk_num_bytes`, `offset`.
- Size and type names shared with `struct extent_map`: the last four of
  those, and `flags`.
- `file_offset` and `compress_type`: no member of the same name; the extent
  map has `start` and `len`, the item has `compression`.
- `flags`: bit numbers in an `unsigned long`, tested with `test_bit()`;
  `em->flags` holds `ENUM_BIT()` masks in a `u32`.
- Mask form of `ordered->flags`: `1U << BTRFS_ORDERED_COMPRESSED`, as in
  `btrfs_split_ordered_extent()`.
- NOCOW and PREALLOC: `btrfs_alloc_ordered_extent()` stores `disk_bytenr` as
  the extent's `disk_bytenr + offset`, `offset` as 0, and `disk_num_bytes` and
  `ram_bytes` as `num_bytes`.
- Comment above the five fields in `struct btrfs_ordered_extent` ("directly
  correspond"): holds only for REGULAR and COMPRESSED.
- Extent map of the same PREALLOC write: keeps the unshifted `disk_bytenr` and
  the `offset`, so `em->disk_bytenr` and `ordered->disk_bytenr` differ when
  `offset` is non-zero.
- `btrfs_split_ordered_extent()`: the new piece gets `offset` 0 and
  `disk_num_bytes = ram_bytes = num_bytes = len`.
- Remainder after a split: `disk_bytenr` advances by `len`; `num_bytes`,
  `disk_num_bytes` and `ram_bytes` shrink by `len`.
- Enum of the flag bits: anonymous, in `fs/btrfs/ordered-data.h`.
- `BTRFS_ORDERED_EXCLUSIVE_FLAGS`: REGULAR, NOCOW, PREALLOC, COMPRESSED;
  `alloc_ordered_extent()` asserts exactly one with `has_single_bit_set()`.
- `BTRFS_ORDERED_TYPE_FLAGS`: those four plus `BTRFS_ORDERED_DIRECT` and
  `BTRFS_ORDERED_ENCODED`; `btrfs_alloc_ordered_extent()` asserts no other
  bit is passed.
- `BTRFS_ORDERED_ENCODED`: only together with `BTRFS_ORDERED_COMPRESSED`.
- `BTRFS_ORDERED_DIRECT`: never with `BTRFS_ORDERED_COMPRESSED` or
  `BTRFS_ORDERED_ENCODED`.
- Most type bits set at once: two, one exclusive bit and one modifier.
- All of these checks are `ASSERT()`, active only with `CONFIG_BTRFS_ASSERT`.
