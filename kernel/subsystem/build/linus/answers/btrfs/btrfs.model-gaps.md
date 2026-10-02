- Models take data folios to carry a checked state; `fs/btrfs` has no checked
  helper and never calls `folio_set_checked()` or `folio_test_checked()`.
- Models take a dirty data folio without private to be fixed up at writeback;
  `extent_writepage()` returns `-EUCLEAN` for it.
- Models take `btrfs_handle_fs_error()` to force read-only every time;
  `__btrfs_handle_fs_error()` in `fs/btrfs/messages.c` returns before that
  while the super block lacks `SB_BORN`.
- Models take the csum and extent roots to exist always; `btrfs_csum_root()`
  and `btrfs_extent_root()` return NULL when `btrfs_global_root()` finds none.
  Callers such as `log_extent_csums()` and `calculate_alloc_pointer()` return
  `-EUCLEAN`.
- Models take NOCOW completion to touch only the inode item; in
  `btrfs_finish_one_ordered()`, `btrfs_zone_finish_endio()` runs before the
  NOCOW branch, and a failure of it or of `btrfs_insert_raid_extent()` goes
  to cleanup.
- Models take swap activation to read extent maps; `btrfs_swap_activate()`
  takes the device and physical address of each extent from
  `struct btrfs_chunk_map`.
- Models take a block group to stay in the `struct btrfs_space_info` of its
  type; on a zoned fs `btrfs_zoned_reserve_data_reloc_bg()` moves an empty
  data block group to sub-group `BTRFS_SUB_GROUP_DATA_RELOC`.
- Models take `ASSERT()` to take one argument; `fs/btrfs/messages.h` accepts
  a format string and arguments after the condition.
- Models take an aborted transaction to be the only fatal state;
  `btrfs_is_shutdown()` in `fs/btrfs/fs.h` tests
  `BTRFS_FS_STATE_EMERGENCY_SHUTDOWN`, set without forcing read-only.
- Models take a block to fit in one page; `assert_bbio_alignment()` in
  `fs/btrfs/bio.c` asserts, under `CONFIG_BTRFS_ASSERT`, that each bio vector
  is aligned only to `min(blocksize, PAGE_SIZE)`.
