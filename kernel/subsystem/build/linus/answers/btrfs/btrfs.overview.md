- Roots found from the superblock, not from a root item: the tree root, the
  chunk root, the log root tree and the remap root; see
  `load_important_roots()`, `load_super_root()` and `btrfs_replay_log()` in
  `fs/btrfs/disk-io.c`.
- Extent, csum and free-space roots: not fields of `struct btrfs_fs_info`;
  they live in `fs_info->global_root_tree` and are fetched with
  `btrfs_extent_root()` and `btrfs_csum_root()`, which take a bytenr, and
  `btrfs_free_space_root()`, which takes a block group.
- Block group items: in `fs_info->block_group_root` when the
  `BTRFS_FEATURE_COMPAT_RO_BLOCK_GROUP_TREE` bit is set, otherwise in the
  extent root; see `btrfs_block_group_root()` in `fs/btrfs/block-group.c`.
- `struct btrfs_transaction`: more than one can exist at a time, linked on
  `fs_info->trans_list`.
- `fs_info->running_transaction`: set to NULL at `TRANS_STATE_UNBLOCKED` in
  `btrfs_commit_transaction()`, before tree blocks and superblocks are
  written, so transaction N+1 can run while N is still being written out.
- Commit: starts only when something calls `btrfs_commit_transaction()`;
  `btrfs_end_transaction()` drops the handle and wakes a waiting committer,
  it never commits.
- Roots modified in a transaction: tracked on `struct btrfs_fs_info` until
  the commit moves them to `switch_commits` of `struct btrfs_transaction`.
  Subvolume roots get `BTRFS_ROOT_TRANS_TAG` in `fs_info->fs_roots_radix`
  (`record_root_in_trans()`); roots with `BTRFS_ROOT_TRACK_DIRTY` go on
  `fs_info->dirty_cowonly_roots` (`add_root_to_dirty_list()` in
  `fs/btrfs/ctree.c`).
- Delayed refs: one `struct btrfs_delayed_ref_root` embedded in each
  `struct btrfs_transaction`; heads are in its `head_refs` xarray.
- `struct btrfs_delayed_ref_node`: the only ref node type; tree and data refs
  are a union of `struct btrfs_tree_ref` and `struct btrfs_data_ref` inside
  it.
- `struct btrfs_space_info`: one per type, not per profile; profiles are the
  `block_groups[]` lists inside it.
- Zoned filesystems: the data space_info has a `BTRFS_SUB_GROUP_DATA_RELOC`
  child and the metadata one a `BTRFS_SUB_GROUP_TREELOG` child, linked by
  `parent` and `sub_group[]`; see `create_space_info()` in
  `fs/btrfs/space-info.c`.
- Remap tree (`fs_info->remap_root`, `BTRFS_FEATURE_INCOMPAT_REMAP_TREE`,
  supported only under `CONFIG_BTRFS_EXPERIMENTAL`): adds a
  logical-to-logical step before chunk mapping. `btrfs_map_block()` calls
  `btrfs_translate_remap()` when the chunk map has
  `BTRFS_BLOCK_GROUP_REMAPPED`, then looks up the chunk map of the new
  address.
- With the remap tree: relocation of all but `BTRFS_BLOCK_GROUP_SYSTEM` and
  `BTRFS_BLOCK_GROUP_METADATA_REMAP` block groups goes through it
  (`should_relocate_using_remap_tree()` in `fs/btrfs/relocation.h`), there is
  a fourth space_info for `BTRFS_BLOCK_GROUP_METADATA_REMAP`, and
  `fs_info->data_reloc_root` stays NULL; `btrfs_read_roots()` fails the mount
  if a data reloc tree exists.
- RAID stripe tree (`fs_info->stripe_root`): for reads of data chunks where
  `btrfs_need_stripe_tree_update()` is true, `set_io_stripe()` in
  `fs/btrfs/volumes.c` takes the physical offset from
  `btrfs_get_raid_extent_offset()`, not from the chunk map stripe.
- `struct extent_buffer`: indexed in the xarray `fs_info->buffer_tree`, which
  also carries the dirty and writeback marks.
- `EXTENT_BUFFER_UNMAPPED` extent buffers, from `btrfs_clone_extent_buffer()`
  and `alloc_dummy_extent_buffer()`: private folios, not in the btree inode
  mapping and not in `fs_info->buffer_tree`, except that the self tests
  insert one with `alloc_test_extent_buffer()`.
- COW of a tree block: outside the self tests, skipped only if the block has
  this transaction's generation and has not been written
  (`BTRFS_HEADER_FLAG_WRITTEN`), plus the `BTRFS_ROOT_FORCE_COW` and reloc
  checks in `should_cow_block()` in `fs/btrfs/ctree.c`.
- `struct btrfs_trans_handle` pins extent buffers:
  `btrfs_inhibit_eb_writeback()` records in the handle the new copy made by
  `btrfs_force_cow_block()` and the buffer for which `should_cow_block()`
  skips COW (not for a `BTRFS_TREE_RELOC_OBJECTID` root or a self-test
  fs_info), at most `BTRFS_INHIBITED_EBS_SLOTS` at once, and holds a
  reference until the slot is reused for another buffer or
  `btrfs_uninhibit_all_eb_writeback()` runs. This blocks only writeback that
  is not `WB_SYNC_ALL`; see `lock_extent_buffer_for_io()`.
- `struct extent_io_tree`: a generic byte-range state tree, not only
  per-inode. It is also embedded in, for example,
  `struct btrfs_transaction` (`dirty_pages`, `pinned_extents`),
  `struct btrfs_root` (`dirty_log_pages`, `log_csum_range`),
  `struct btrfs_device` (`alloc_state`) and `struct btrfs_fs_info`
  (`excluded_extents`).
- `struct extent_io_tree` back pointer: a union of `fs_info` and `inode`;
  `inode` is valid only when `owner` is `IO_TREE_INODE_IO`, so use
  `btrfs_extent_io_tree_to_inode()` and `btrfs_extent_io_tree_to_fs_info()`.
- `struct btrfs_inode`: the extent map tree is the embedded
  `struct extent_map_tree extent_tree`; the ordered extents are a bare
  `struct rb_root ordered_tree` under `ordered_tree_lock`.
- `struct btrfs_bio`: submitted with `btrfs_submit_bbio()`; the static
  `btrfs_submit_bio()` in `fs/btrfs/bio.c` is the step after mapping.
