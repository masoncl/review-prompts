- Data block group: activated in `do_allocation_zoned()` in
  `fs/btrfs/extent-tree.c`, when an extent is allocated from it.
- `btrfs_chunk_alloc()`: activates the new block group only for data and only
  for `CHUNK_ALLOC_FORCE_FOR_EXTENT`. It ignores a failure.
- Metadata and system block groups: not activated by `do_allocation_zoned()`.
  `check_bg_is_active()` activates them at write-out, from
  `btrfs_check_meta_write_pointer()`.
- Without `BTRFS_FS_ACTIVE_ZONE_TRACKING`: `btrfs_check_meta_write_pointer()`
  returns 0 before `check_bg_is_active()`, so no metadata or system block
  group is activated at write-out.
- `btrfs_zoned_activate_one_bg()`: returns 0 at once for a data `space_info`.
  Its callers are `btrfs_inc_block_group_ro()` and `reserve_chunk_space()` in
  `fs/btrfs/block-group.c`. `fs/btrfs/space-info.c` does not call it and there
  is no ACTIVATE_ZONE flush state.
- `do_finish` argument of `btrfs_zoned_activate_one_bg()`: allows it to call
  `btrfs_zone_finish_one_bg()` when activation failed. It is not a metadata
  flag and holds nothing in reserve.
- `check_bg_is_active()` pivot: finishes the previous `active_meta_bg` or
  `active_system_bg` with `do_zone_finish()` before it activates the new one,
  not after a failure.
- `check_bg_is_active()` tree-log branch: the only one that retries after
  `btrfs_zone_finish_one_bg()`, which picks data block groups only.
- Reserve: `reserved_active_zones` in `struct btrfs_zoned_device_info`, set at
  mount by `btrfs_check_active_zone_reservation()`. `btrfs_zone_activate()`
  and `btrfs_can_activate_zone()` apply it to data only.
- Lock order in `btrfs_zone_activate()`: `fs_info->zone_active_bgs_lock`, then
  `block_group->lock`. It does not take `space_info->lock`.
- Per-device accounting: no lock of its own. `btrfs_dev_set_active_zone()`
  uses `atomic_dec_if_positive()` on `active_zones_left` and
  `test_and_set_bit()` on `active_zones`.
- **Unsafe usage**: calling `btrfs_zone_activate()` on a data block group that
  may be full.
  - Unsafe: `btrfs_zone_activate()` hits `WARN_ON_ONCE()` and returns false
    for a full data block group.
  - Safe: test `btrfs_zoned_bg_is_full()` under `block_group->lock` first, as
    `do_allocation_zoned()` does.
  - Safe: a block group that was just created, as in `btrfs_chunk_alloc()`;
    `btrfs_load_block_group_zone_info()` with `new` true leaves a new block
    group with `alloc_offset` 0, so `btrfs_zoned_bg_is_full()` is false.
- **Unsafe usage**: calling `btrfs_zone_activate()` on an inactive metadata or
  system block group that was already written.
  - Unsafe: `btrfs_zone_activate()` hits `WARN_ON_ONCE()` when
    `meta_write_pointer` differs from `start`, and activates anyway.
  - Safe: a block group not written since it was loaded, as in
    `check_bg_is_active()`: with `BTRFS_FS_ACTIVE_ZONE_TRACKING` set,
    `write_meta_extent_buffer()` advances `meta_write_pointer` only after
    `btrfs_check_meta_write_pointer()` returned 0, so the first write finds
    `meta_write_pointer` equal to `start`.
