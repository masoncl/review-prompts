- `BLOCK_GROUP_FLAG_SEQUENTIAL_ZONE`: set by
  `btrfs_load_block_group_zone_info()` when at least one stripe is not on a
  conventional zone, so `btrfs_use_zone_append()` can be true for a block
  group that also has conventional stripes.
- `btrfs_submit_chunk()`: stores the result of `btrfs_use_zone_append()` in
  `bbio->can_use_append` and limits the length with
  `btrfs_append_map_length()`; it does not change the bio op.
- `btrfs_submit_dev_bio()`: sets `REQ_OP_ZONE_APPEND`, and only when
  `bbio->can_use_append` and `btrfs_dev_is_sequential()` both hold for that
  device; otherwise the bio stays `REQ_OP_WRITE`.
- Direct I/O writes: no separate rule; `btrfs_dio_submit_io()` calls
  `btrfs_submit_bbio()`, so `btrfs_use_zone_append()` decides.
- `bbio->orig_physical`: written only in `btrfs_submit_bio()` on the
  single-device path (no `bioc`).
- `btrfs_record_physical_zoned()`: called only from `simple_end_io_work()`,
  the completion of that same path; it reads `bbio->orig_physical` and
  shifts `bbio->sums->logical` by the difference.
- Checksums: `add_pending_csums()` in `fs/btrfs/inode.c` inserts with
  `sum->logical`; nothing rewrites the sums at ordered completion.
- Writes with a `bioc` (not RAID56): `orig_write_end_io_work()` and
  `clone_write_end_io_work()` store the address in `stripe->physical`; for a
  `bioc` with `use_rst`, which `btrfs_submit_chunk()` puts on
  `ordered->bioc_list`, `btrfs_insert_raid_extent()` records it; the logical
  address is unchanged.
- `btrfs_finish_ordered_io()`: calls `btrfs_finish_ordered_zoned()` only when
  the fs is zoned, `BTRFS_ORDERED_IOERR` is clear and `ordered->bioc_list` is
  empty.
- `btrfs_finish_ordered_zoned()`: returns at once for `BTRFS_ORDERED_TRUNCATED`
  with `truncated_len == 0`, asserting that `ordered->csum_list` is empty.
- The sums list is `ordered->csum_list`; `struct btrfs_ordered_extent` has no
  `list` member for it.
- `btrfs_finish_ordered_zoned()` asserts `ordered->csum_list` is non-empty for
  every other non-`BTRFS_ORDERED_PREALLOC` ordered extent it is called for,
  including writes that did not use append.
- `btrfs_alloc_dummy_sum()`: called by `btrfs_submit_chunk()` when no checksum
  is computed and either `bbio->can_use_append` is set or the fs is zoned and
  the inode has `BTRFS_INODE_NODATASUM`.
- `btrfs_split_extent_map()` in `fs/btrfs/extent_map.c`: sets the front
  piece's `disk_bytenr` to the new logical address.
- At a discontinuity, `btrfs_zoned_split_ordered()`: splits off the
  contiguous front, sets `new->disk_bytenr`, and completes it at once with
  `btrfs_finish_one_ordered()`; `btrfs_split_ordered_extent()` moves the
  front's sums to the new ordered extent.
- `btrfs_rewrite_logical_zoned()`: runs at most once, for the piece left
  after all splits, and only if `ordered->disk_bytenr` differs; it writes
  `ordered->disk_bytenr` and the extent map's `disk_bytenr`, not the sums.
- Split failure: `btrfs_mark_ordered_extent_error()` sets
  `BTRFS_ORDERED_IOERR` and the mapping error; the remaining piece is not
  rewritten, and dummy sums are still freed.
- `ordered->disk_bytenr` of an in-flight zoned data write is provisional;
  `btrfs_sync_file()` in `fs/btrfs/file.c` calls `btrfs_wait_ordered_range()`
  on a zoned fs instead of logging from in-flight ordered extents.
