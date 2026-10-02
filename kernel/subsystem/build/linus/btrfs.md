# Btrfs Subsystem Details

## Main structures

### Objects and how they relate

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

## Extent map fields and sizes

**Extent map purpose**

- Map on `modified_extents` that a fast fsync still has to log: can still be
  dropped; `btrfs_log_changed_extents()` logs only maps on that list, so
  `btrfs_scan_inode()` compensates with `btrfs_set_inode_full_sync()`.
- `btrfs_drop_extent_map_range()`: removes a listed map that lies wholly in
  the range without setting full sync; it sets full sync when a listed map
  that is still in the tree crosses the range boundary and no split map could
  be allocated.
- Callers that fail to allocate a replacement map: drop the range and call
  `btrfs_set_inode_full_sync()`, for example `fill_holes()` in
  `fs/btrfs/file.c` and `btrfs_cont_expand()`.
- Data relocation inode: `setup_relocation_extent_mapping()` inserts a pinned
  map whose `disk_bytenr` is `rc->cluster.start`, the extents being read,
  while the inode's file extent items (from `prealloc_file_extent_cluster()`)
  are prealloc extents elsewhere; this map cannot be rebuilt from the items.

**Extent map member names**

- `try_merge_map()`: edits the surviving map in place; besides `start`, `len`,
  `generation` and `flags` it rewrites, for a real extent, `disk_bytenr`,
  `disk_num_bytes`, `ram_bytes` and `offset` through `merge_ondisk_extents()`.
- Merged map: `disk_bytenr` is the lower of the two, `disk_num_bytes` and
  `ram_bytes` are both the span of the two on-disk extents; two different,
  adjacent on-disk extents merge too, so the result may match no item.
- `try_merge_map()` callers: `setup_extent_mapping()` when `modified` is
  false, `btrfs_unpin_extent_cache()`, `btrfs_clear_em_logging()`.
- `btrfs_drop_extent_map_range()`: leaves the size and address members of the
  old map alone; it builds new maps and puts them in with
  `replace_extent_mapping()` or, for a tail piece after the old map was
  replaced, `add_extent_mapping()`.
- There is no split_extent_map() here; `btrfs_split_extent_map()` does that,
  and each piece gets its own `disk_bytenr`, `disk_num_bytes` and `ram_bytes`
  both equal to the piece's `len`, and `offset` 0.
- `merge_extent_mapping()`: on `-EEXIST` in `btrfs_add_extent_mapping()`,
  trims `start` and `len` of the new map to the free gap and, for a real
  extent, advances `offset`, so an inserted map can cover only part of its
  item's range.

**Holes and inline extents**

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

**Extent map flags**

- Flag set: seven bits in `fs/btrfs/extent_map.h`, including
  `EXTENT_FLAG_MERGED`; there is no EXTENT_FLAG_FILLING and no
  EXTENT_FLAG_COMPRESSED.
- Merge: `can_merge_extent_map()` refuses `EXTENT_FLAG_PINNED`, any
  compression bit, `EXTENT_FLAG_LOGGING`, and a map on `modified_extents`;
  `mergeable_maps()` needs equal `flags` apart from `EXTENT_FLAG_MERGED`.
- Drop: `EXTENT_FLAG_PINNED` is the only `flags` bit that, when set, makes a
  dropper leave a map in the tree: `btrfs_drop_extent_map_range()` with
  `skip_pinned` true, `btrfs_scan_inode()` and
  `try_release_extent_mapping()`.
- `btrfs_drop_extent_map_range()` with `skip_pinned` false: drops pinned maps
  too.
- `EXTENT_FLAG_LOGGING`: does not protect a map from removal; on removal it
  only makes `btrfs_remove_extent_mapping()` and `replace_extent_mapping()`
  leave `em->list` alone; `try_release_extent_mapping()` removes such a map on
  purpose.
- There is no remove_extent_mapping() here; `btrfs_remove_extent_mapping()`
  does that, and warns on a pinned map.
- `drop_all_extent_maps_fast()`: clears both `EXTENT_FLAG_PINNED` and
  `EXTENT_FLAG_LOGGING` before removal.
- Logged or not: no flag alone decides it; `btrfs_log_changed_extents()` takes
  maps from `modified_extents`, skips `generation < trans->transid` and
  prealloc maps at or beyond `i_size`, and sets `EXTENT_FLAG_LOGGING` on the
  rest.
- Never cleared on a map: the three compression bits,
  `EXTENT_FLAG_PREALLOC` and `EXTENT_FLAG_MERGED`.
- Write into a prealloc range: the map is replaced by a new one from
  `btrfs_create_io_em()`, which does not set `EXTENT_FLAG_PREALLOC`.
- `EXTENT_FLAG_MERGED`: tested only by `defrag_lookup_extent()`, which
  discards the map and rebuilds one from the item with `defrag_get_extent()`.
- Compression helpers: `btrfs_extent_map_set_compression()`,
  `btrfs_extent_map_compression()` and `btrfs_extent_map_is_compressed()`
  all carry the `btrfs_` prefix.

**Disk address and length**

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

**Compressed and partial layouts**

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

**Extent map invariants**

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

**Choosing a size field**

- There is no extent_map_end() here; `btrfs_extent_map_end()` gives the end
  of the file range.
- `btrfs_submit_compressed_read()`: reads `em->disk_num_bytes` directly for
  the compressed length and never reads `ram_bytes`; the decompressed length
  it handles is the size of the original bio, and `cb->start` is
  `em->start - em->offset`.
- `ram_bytes` readers outside `fs/btrfs/extent_map.c`: only
  `btrfs_encoded_read()` (as `unencoded_len`) and `log_one_extent()`.

**Chunk mapping structure**

- `struct btrfs_chunk_map`: has no `io_align` or `io_width` member; in
  `fs/btrfs/volumes.h` those belong to `struct btrfs_device`.
- `type` and `on_disk_type`: `on_disk_type` is the chunk item's value;
  `btrfs_chunk_alloc_add_chunk_item()` writes it to the chunk item and
  `fill_dummy_bgs()` copies it to the block group flags; `type` is what
  mapping code uses.
- `set_real_chunk_type()` in `fs/btrfs/volumes.c`: for a RAID5 or RAID6
  chunk with one data stripe, sets `type` to RAID1 or RAID1C3 instead.
- There is no btrfs_clone_chunk_map() here; a zoned block group keeps a
  counted pointer to the in-tree map in `physical_map`, taken with
  `btrfs_find_chunk_map()` in `btrfs_load_block_group_zone_info()`.

## The extent map tree

**Extent map function names**

- Prefix: every function declared or defined in `fs/btrfs/extent_map.h`
  carries `btrfs_`, the inline helpers and the slab setup included, for
  example `btrfs_extent_map_end()`, `btrfs_alloc_extent_map()`,
  `btrfs_free_extent_map()`, `btrfs_extent_map_init()`.
- Unprefixed spellings such as free_extent_map(), extent_map_end() or
  lock_extent() name no function in this tree; they survive only in comments.
- Unprefixed extent map functions are outside the header: the static helpers
  in `fs/btrfs/extent_map.c` (for example `try_merge_map()`,
  `lookup_extent_mapping()`) and, for example,
  `try_release_extent_mapping()` in `fs/btrfs/extent_io.c`.
- Functions in the header that take `struct extent_map_tree *`: only
  `btrfs_extent_map_tree_init()`, `btrfs_lookup_extent_mapping()` and
  `btrfs_search_extent_mapping()`.
- Functions in the header that take `struct btrfs_inode *`: every function
  that can insert or remove a map, `btrfs_add_extent_mapping()` and
  `btrfs_remove_extent_mapping()` included.
- Functions in the header that take `struct btrfs_fs_info *`: the shrinker
  entry points `btrfs_free_extent_maps()` and
  `btrfs_init_extent_map_shrinker_work()`.

**Extent map tree locking**

- `lockdep_assert_held_write()` on the tree lock: in `add_extent_mapping()`
  (so `btrfs_add_extent_mapping()`), `btrfs_remove_extent_mapping()`,
  `btrfs_clear_em_logging()`, `replace_extent_mapping()` and
  `btrfs_scan_inode()`.
- `btrfs_lookup_extent_mapping()` and `btrfs_search_extent_mapping()`: no
  assertion; lockdep does not catch a lookup without the lock.
- `btrfs_unpin_extent_cache()`: takes the write lock itself.
- `btrfs_split_extent_map()`: locks the file range in `inode->io_tree` with
  `btrfs_lock_extent()`, then takes the write lock; the caller holds neither.
- `btrfs_drop_extent_map_range()`: holds the write lock across the whole loop.
- Lock dropped and retaken (`cond_resched_rwlock_write()`): only in
  `drop_all_extent_maps_fast()`, reached with `start == 0`,
  `end == (u64)-1` and `skip_pinned` false.
- `btrfs_drop_extent_map_range()` calls `btrfs_alloc_extent_map()`
  (`GFP_NOFS`) twice before it locks; the caller must be able to sleep.
- Range lock in the io tree: stated in the comments above
  `btrfs_drop_extent_map_range()` and `btrfs_replace_extent_map_range()`;
  neither function checks it.
- Callers without the range lock exist on an inode being torn down, for
  example `evict_inode_truncate_pages()` (asserts `I_FREEING`) and
  `btrfs_destroy_inode()`.

**Extent map references**

- `btrfs_remove_extent_mapping()`: changes no reference count; the caller
  drops the tree's reference with a separate `btrfs_free_extent_map()`, as
  `try_release_extent_mapping()` and `btrfs_scan_inode()` do.
- `flags` and `generation` of an in-tree map: written under the tree write
  lock with no test of `refs`, for example in `btrfs_unpin_extent_cache()`,
  `btrfs_clear_em_logging()` and `btrfs_log_changed_extents()`.
- `start`, `len`, `disk_bytenr`, `disk_num_bytes`, `offset`, `ram_bytes` of an
  in-tree map: `try_merge_map()` writes them, and only when
  `refcount_read(&em->refs) <= 2`.
- `btrfs_rewrite_logical_zoned()` in `fs/btrfs/zoned.c`: writes `disk_bytenr`
  of the map of an ordered extent in place, under the write lock, no `refs`
  test.
- Holders of a reference read members without the tree lock, for example
  `btrfs_do_readpage()`; the `refs` test in `try_merge_map()` is what keeps a
  merge from changing them.

**Lookup and insert results**

- `btrfs_search_extent_mapping()`: takes `(tree, start, len)`; `strict` is a
  parameter of the static `lookup_extent_mapping()` only.
- `btrfs_search_extent_mapping()` order: the map that contains `start`, else
  the next map after `start`, else the previous map; `NULL` only for an empty
  tree.
- `btrfs_add_extent_mapping()` precondition: `*em_in` contains `start`;
  `btrfs_get_extent()` tests this before the call and returns `-EIO`.
- Without that precondition, on `-EEXIST` `merge_extent_mapping()` can return
  `-EINVAL`, which trips `ASSERT(ret == 0 || ret == -EEXIST)`.
- `btrfs_add_extent_mapping()` inserts as not modified, so `try_merge_map()`
  runs: on success `*em_in` may cover more than the caller filled in and
  carry `EXTENT_FLAG_MERGED`.
- `btrfs_add_extent_mapping()` failure: the map is already freed and
  `*em_in` is `NULL`; the caller must not free the pointer it passed in.
- After the call `btrfs_get_extent()` tests only the return value.
- After a lookup the caller tests that the map contains the offset it wants:
  `btrfs_get_extent()` drops a map with `em->start > start`;
  `btrfs_unpin_extent_cache()` returns `-EUCLEAN` if `em->start != start`.

**Creating extent maps**

- `btrfs_extent_item_to_extent_map()`, uncompressed regular or prealloc
  extent: `ram_bytes` is overwritten with `disk_num_bytes`; the item's
  `ram_bytes` is kept only for compressed, hole and inline items.
- `btrfs_alloc_extent_map()` uses `kmem_cache_zalloc()`; in-tree builders
  leave members that are 0 unset.
- For example `btrfs_cont_expand()` and `fill_holes()` do not set `offset`;
  `setup_relocation_extent_mapping()` sets neither `offset` nor `generation`.
- `btrfs_get_extent()` builds by hand only the implicit hole: `start`, `len`
  and `disk_bytenr = EXTENT_MAP_HOLE`, the rest 0; inline maps come from
  `btrfs_extent_item_to_extent_map()`.
- Hole maps added as modified set `ram_bytes = len`, as `fill_holes()` does;
  `log_one_extent()` copies `em->ram_bytes` into the logged item.
- Write maps: `btrfs_create_io_em()` sets `generation = -1` with
  `EXTENT_FLAG_PINNED`; `defrag_collect_targets()` reads
  `generation == (u64)-1` as under writeback and skips the map.
- `validate_extent_map()` on any real extent: `offset + len <= ram_bytes`,
  non-zero `disk_num_bytes`, and sector alignment of `start`, `len`,
  `disk_bytenr`, `disk_num_bytes`, `offset` and `ram_bytes`.

**Merging extent maps**

- After a merge of real extents (`merge_ondisk_extents()`):

| Member | Value |
|---|---|
| `disk_bytenr` | minimum of the two |
| `disk_num_bytes` | larger disk end of the two, minus new `disk_bytenr` |
| `offset` | `prev->disk_bytenr + prev->offset`, minus new `disk_bytenr` |
| `ram_bytes` | new `disk_num_bytes` |
| `generation` | maximum of the two |

- Merged hole: only `start`, `len`, `generation` and `flags` change;
  `ram_bytes` is not updated.
- `EXTENT_FLAG_MERGED` is set on the surviving map;
  `defrag_lookup_extent()` in `fs/btrfs/defrag.c` discards such a map and
  rebuilds from the file extent item.
- `refs > 2` test in `try_merge_map()`: covers only the map that survives.
- Absorbed neighbour: removed from the tree whatever its `refs`, members
  untouched; a holder detects it with `btrfs_extent_map_in_tree()`, as
  `get_extent_map()` in `fs/btrfs/extent_io.c` does.
- `try_merge_map()` is reached through `setup_extent_mapping()` with
  `modified` false, from `add_extent_mapping()` and from
  `replace_extent_mapping()`.
- `btrfs_unpin_extent_cache()`: merges nothing while the map is still on
  `modified_extents`, which is where `btrfs_create_io_em()` put it.

**Dropping a range**

- Tail piece, any real extent, compressed included:
  `offset = em->offset + end - em->start`; `disk_bytenr`, `disk_num_bytes`,
  `ram_bytes` copied.
- Hole or inline piece: `disk_bytenr` copied, `disk_num_bytes = 0`,
  `offset = 0`, `ram_bytes` = length of the piece.
- Flags of the pieces: the old flags without `EXTENT_FLAG_LOGGING`;
  `EXTENT_FLAG_PINNED` is inherited.
- Old map: loses `EXTENT_FLAG_PINNED`, keeps `EXTENT_FLAG_LOGGING`.
- Pieces go on `modified_extents` when `em->list` of the old map was not
  empty, which is also true of a map with `EXTENT_FLAG_LOGGING` that still
  waits on the private list of `btrfs_log_changed_extents()`.
- No spare map for a map still in the tree: the whole map is removed;
  `btrfs_set_inode_full_sync()` is called only if the map was on a list and
  reached outside the range.
- `btrfs_split_extent_map()` requires a map that is pinned, on
  `modified_extents`, without `EXTENT_FLAG_LOGGING`, uncompressed, a real
  extent, with `em->len == len`, and `0 < pre < len`.
- All of those are `ASSERT()`, compiled out without `CONFIG_BTRFS_ASSERT`.
- `btrfs_split_extent_map()` runtime errors: `-ENOMEM`, and `-EIO` only when
  the lookup finds no map.
- Callers skip `btrfs_split_extent_map()` for `BTRFS_ORDERED_NOCOW` ordered
  extents; see `btrfs_extract_ordered_extent()`.

**Pinned and modified extent maps**

- Pure NOCOW write: no map is created or pinned; `btrfs_finish_one_ordered()`
  leaves before `btrfs_unpin_extent_cache()` for `BTRFS_ORDERED_NOCOW`.
- Pinned map on the list: `generation` is `-1`, so the
  `em->generation < trans->transid` test in `btrfs_log_changed_extents()`
  does not skip it; a fast fsync can log it while it is still pinned.
- `btrfs_remove_extent_mapping()` and `replace_extent_mapping()`: warn on a
  pinned map; `btrfs_drop_extent_map_range()` clears the flag first.
- `btrfs_log_changed_extents()`: leaves `modified_extents` empty, whether it
  logs a map or not.
- `btrfs_log_inode()`: a full fsync with `LOG_INODE_ALL` empties the list
  without logging from it.
- `EXTENT_FLAG_LOGGING` set: `em->list` links the map into the private list
  of `btrfs_log_changed_extents()`, or is empty once the map is taken off
  that list for `log_one_extent()`; it is never on `modified_extents`.
- `btrfs_log_changed_extents()` drops the tree lock around each
  `log_one_extent()`; the map can leave the tree meanwhile, hence the
  `btrfs_extent_map_in_tree()` test in `btrfs_clear_em_logging()`.
- **Potentially unsafe usage**: taking a map that is on `modified_extents`
  off the list, or out of the tree, while the file keeps the extent.
  - Unsafe: `generation` is not below `btrfs_get_fs_generation()`, full sync
    is not set, no replacement is added as modified and the map lacks
    `EXTENT_FLAG_LOGGING`; `btrfs_log_changed_extents()` logs only maps on
    the list, so a fast fsync omits the extent.
  - Safe: `generation` below the current one, as
    `try_release_extent_mapping()` tests; `btrfs_log_changed_extents()` skips
    such maps anyway.
  - Safe: call `btrfs_set_inode_full_sync()` while holding `i_mmap_lock`, as
    `btrfs_scan_inode()` does for read; `btrfs_sync_file()` holds it for
    write from reading the flag until the inode is logged.
  - Safe: add the replacement as modified, as `btrfs_drop_extent_map_range()`
    does for the pieces and `btrfs_replace_extent_map_range()` with
    `modified` true.
  - Safe: the map has `EXTENT_FLAG_LOGGING`, as `try_release_extent_mapping()`
    tests; the logger holds its own reference.

**Reclaiming extent maps**

- `btrfs_scan_inode()` skips only pinned maps; it does not test
  `EXTENT_FLAG_LOGGING`.
- `btrfs_scan_inode()`, map on a list with `generation` not below
  `btrfs_get_fs_generation()`: calls `btrfs_set_inode_full_sync()`, then
  removes the map.
- `try_release_extent_mapping()`: never sets full sync; a listed map with
  current `generation` and no `EXTENT_FLAG_LOGGING` stays in the tree.
- `try_release_extent_mapping()` stops the walk at a pinned map or at
  `em->start != start`; it steps over a map whose range has `EXTENT_LOCKED`.
- `try_release_extent_mapping()` does not lock the range; it only tests the
  bit with `btrfs_test_range_bit_exists()`. There is no
  test_range_bit_exists() here.
- `try_release_extent_mapping()` has no gate on the gfp mask or on file size;
  `mask` only decides, on `need_resched()`, between `cond_resched()` and
  stopping.
- Tree lock for `btrfs_scan_inode()`: taken by `find_first_inode_to_shrink()`
  with `write_trylock()`, released by `btrfs_scan_root()`;
  `btrfs_scan_inode()` asserts it and never drops it, it stops scanning.
- `i_mmap_lock` in `btrfs_scan_inode()`: `down_read_trylock()` because the
  spinning tree lock is already held; on failure the inode is skipped.
- `btrfs_scan_inode()` runs in `btrfs_extent_map_shrinker_worker()`, a work
  item on `system_dfl_wq`, not in the reclaiming task;
  `btrfs_free_extent_maps()` only queues it.

**Other extent map users**

- Fiemap (`extent_fiemap()` in `fs/btrfs/fiemap.c`) and seek
  (`find_desired_extent()` in `fs/btrfs/file.c`): read file extent items, not
  extent maps; there is no btrfs_get_extent_fiemap().
- `btrfs_swap_activate()`: reads file extent items with `btrfs_search_slot()`.
- Compressed readahead is `add_ra_bio_folios()` in `fs/btrfs/compression.c`;
  there is no add_ra_bio_pages().
- `add_ra_bio_folios()` adds a folio only when
  `btrfs_extent_map_block_start()` of the map it looks up equals the sector
  of the original bio, that is, the map points to the same compressed extent.
- Direct I/O: `btrfs_dio_iomap_begin()` and
  `btrfs_get_blocks_direct_write()` in `fs/btrfs/direct-io.c`; there is no
  btrfs_get_blocks_direct().
- `defrag_get_extent()`: builds a map from the file extent item and never
  inserts it; the tree reader is `defrag_lookup_extent()`.
- `log_one_extent()`: writes `trans->transid` as the item's generation, not
  `em->generation`; `em->generation` only decides whether the map is logged.
- `btrfs_get_extent_allocation_hint()`: uses
  `btrfs_search_extent_mapping()`, so the map may not overlap the range; it
  needs only a real `disk_bytenr`.
- `btrfs_find_new_delalloc_bytes()`: sets `EXTENT_DELALLOC_NEW` over ranges
  whose map has `disk_bytenr == EXTENT_MAP_HOLE`.
- `btrfs_rewrite_logical_zoned()`: requires `em->offset == 0` (`ASSERT()`)
  and writes `disk_bytenr`.
- Other readers: search for callers of `btrfs_get_extent()`,
  `btrfs_lookup_extent_mapping()` and `btrfs_search_extent_mapping()`.

## Ordered extents, range locks and subpage

**Extent maps for new writes**

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

**Ordered extent sizes and type**

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

**Ordered extent completion**

- Order in `btrfs_finish_one_ordered()` after the transaction is joined:
  1. `btrfs_insert_raid_extent()`
  2. file extent: `btrfs_mark_extent_written()` for PREALLOC, otherwise
     `insert_ordered_extent_file_extent()`
  3. `btrfs_unpin_extent_cache()`
  4. `add_pending_csums()`
  5. clear `EXTENT_DELALLOC_NEW` with `EXTENT_ADD_INODE_BYTES`
  6. `btrfs_inode_safe_disk_i_size_write()` and
     `btrfs_update_inode_fallback()`
- Checksums go into the csum tree after the file extent item, not before.
- `btrfs_add_ordered_sum()`: only queues on `csum_list`.
- `add_pending_csums()`: inserts with `btrfs_insert_data_csums()`; there is no
  btrfs_csum_file_blocks here.
- NOCOW: step 1 still runs; then only step 6.
- NOCOW with a non-empty `csum_list`: an `ASSERT()`, then `-EINVAL` and a
  transaction abort.
- There is no unpin_extent_cache() here; `btrfs_unpin_extent_cache()` in
  `fs/btrfs/extent_map.c` does that.
- `btrfs_unpin_extent_cache()`: clears `EXTENT_FLAG_PINNED`, sets
  `generation`, tries to merge the map with its neighbours.
- `btrfs_unpin_extent_cache()` failure: `-ENOENT` (no map) or `-EUCLEAN`
  (wrong start) aborts the transaction.
- Truncated with `truncated_len > 0`: only the item's `num_bytes` becomes
  `truncated_len`; `ram_bytes` and `disk_num_bytes` stay, and unpin uses the
  full `num_bytes`.
- Truncated with `truncated_len > 0` and no error: the extent maps from
  `file_offset + truncated_len` on are dropped; no reserved space is freed.
- `btrfs_free_reserved_extent()`: the only way space is returned, on error or
  `truncated_len` 0, not for NOCOW or PREALLOC, and not after
  `insert_ordered_extent_file_extent()` succeeded; there is no pinning on
  this path.
- Error marking: `btrfs_mark_ordered_extent_error()` sets
  `BTRFS_ORDERED_IOERR` and, if the bit was clear, calls
  `mapping_set_error()`; no folio flag is set.
- Extent map drop on error or truncate: skipped for the free space inode.

**File range locks**

- `find_lock_delalloc_range()`: locks the folios, takes the range lock only to
  re-test `EXTENT_DELALLOC`, and drops it before returning.
- Range lock on writeback: taken by `cow_one_range()` (after
  `btrfs_reserve_extent()`), `nocow_one_range()` and
  `submit_one_async_extent()`, around the creation of the extent map and
  ordered extent.
- Release on writeback: `extent_clear_unlock_delalloc()`.
- There is no btrfs_find_lock_delalloc_range() and no
  lock_and_cleanup_extent_if_need() here; the names are
  `find_lock_delalloc_range()` and `lock_and_cleanup_extent()`.
- Buffered write, per folio in `copy_one_range()`: reserve space,
  `prepare_one_folio()`, then `lock_and_cleanup_extent()`, which always takes
  the range lock (a trylock with `nowait`).
- Buffered read: `lock_extents_for_read()` in `fs/btrfs/extent_io.c`, not
  `btrfs_lock_and_flush_ordered_range()`.
- Buffered read wait: the range is unlocked but the folio stays locked; it
  calls `btrfs_start_ordered_extent_nowriteback()` so its own range is not
  written back.
- `can_skip_ordered_extent()`: lets the read keep the range lock and not wait
  when the folio has private data and the block is dirty or uptodate.
- `btrfs_read_folio()`: unlocks the range after `btrfs_do_readpage()`, not at
  end of I/O; the folio is unlocked at end of I/O.
- `btrfs_finish_one_ordered()`: locks with
  `EXTENT_LOCKED | EXTENT_FINISHING_ORDERED`; takes no range lock for NOCOW.
- `try_release_extent_state()`: releases a folio whose range is locked, if
  `EXTENT_FINISHING_ORDERED` is set.
- Direct I/O order, in `lock_extent_direct()`: `EXTENT_DIO_LOCKED` first, then
  `EXTENT_LOCKED`, then the ordered extent lookup.
- Direct I/O wait: drops only `EXTENT_LOCKED`.
- `EXTENT_DIO_LOCKED`: conflicts only with itself, and only
  `fs/btrfs/direct-io.c` takes it, so it excludes other direct I/O and not
  buffered paths.
- `EXTENT_LOCKED` in direct I/O: cleared at the end of
  `btrfs_dio_iomap_begin()`, for reads and writes.
- `EXTENT_DIO_LOCKED` in direct I/O: writes clear it at the end of
  `btrfs_dio_iomap_begin()`; reads in `btrfs_dio_end_io()`, in
  `btrfs_dio_iomap_end()` for the part not submitted, or at the end of
  `btrfs_dio_iomap_begin()` for the part past the mapped length.
- Direct read that finds an ordered extent without `BTRFS_ORDERED_DIRECT`:
  returns `-ENOTBLK` (`-EAGAIN` with `IOMAP_NOWAIT`), does not wait.
- Direct write that finds page cache in the range: returns `-ENOTBLK`, or
  `-EAGAIN` with `IOMAP_NOWAIT`; no retry.

**Subpage and per-block state**

- `struct btrfs_folio_state` in `fs/btrfs/subpage.h`: the per-block state;
  there is no struct btrfs_subpage.
- Members: `lock`, a union of `eb_refs` (metadata) and `nr_locked` (data),
  and `bitmaps[]`.
- Bitmaps: uptodate, dirty, writeback, fixup, numbered up to
  `btrfs_bitmap_nr_max`.
- No ordered, checked or locked bitmap, no ordered helper and no ordered folio
  flag exist.
- `btrfs_invalidate_folio()`: uses `btrfs_folio_test_dirty()` to find the
  blocks of an ordered extent that were never submitted.
- `btrfs_is_subpage()`: `fs_info->sectorsize < folio_size(folio)`, so true for
  a large folio when block size equals page size; asserts a data inode.
- `btrfs_meta_is_subpage()`: `fs_info->nodesize < PAGE_SIZE`, for metadata.
- Fixup bit: a block dirtied with no space reservation; `writepage_fixup()`
  withholds it and `btrfs_writepage_fixup_worker()` reserves for it.
- `folio_test_fixup_pending()` in `fs/btrfs/fs.h`: the whole fixup state of a
  single-block folio; set on a multi-block folio while any fixup bit is set.
- `nr_locked`: a count only. `btrfs_folio_end_lock()` and
  `btrfs_folio_end_lock_bitmap()` subtract what the caller passes, so the
  blocks must be the ones `btrfs_folio_set_lock()` counted.
- **Potentially unsafe usage**: `folio_mark_dirty()` on a data folio.
  - Unsafe: from a path that reserved space. It reaches
    `btrfs_data_dirty_folio()`, which marks every clean block up to `i_size`
    dirty and fixup (on a multi-block folio only if the folio is uptodate);
    writeback withholds them and the worker sets delalloc again, or under
    `CONFIG_BTRFS_DEBUG` hits `DEBUG_WARN()` and clears the bit.
  - Safe: `btrfs_folio_set_dirty()` after the reservation, as
    `btrfs_page_mkwrite()` does; it clears the fixup bits and calls
    `filemap_dirty_folio()`.
  - Safe: a dirtier with no reservation, such as the GUP pin release in
    `unpin_user_pages_dirty_lock()`; `btrfs_data_dirty_folio()` exists for
    it, and `writepage_fixup()` needs the fixup bit to withhold the block.
- **Unsafe usage**: clearing a fixup bit and leaving the block dirty with no
  reservation.
  - Safe: `btrfs_folio_clear_fixup()` after delalloc is set, as
    `btrfs_writepage_fixup_worker()` does.
  - Safe: `btrfs_folio_clear_fixup_dirty()` when the data is discarded, as
    `btrfs_invalidate_folio()` does; it drops only blocks fully inside the
    range.
- **Potentially unsafe usage**: `folio_test_uptodate()` or
  `folio_test_dirty()` on a folio with several blocks.
  - Unsafe: to decide about one block; the flag is for the whole folio.
  - Safe: a whole-folio test, as `prepare_uptodate_folio()` in
    `fs/btrfs/file.c`; `btrfs_subpage_set_uptodate()` sets the flag only when
    every block is uptodate.
  - Safe: `btrfs_folio_test_dirty()` with the block's range, as
    `btrfs_invalidate_folio()` does.

## Zoned mode

**Zoned file systems**

- `btrfs_is_zoned()` in `fs/btrfs/fs.h`: `IS_ENABLED(CONFIG_BLK_DEV_ZONED)`
  and `fs_info->zone_size > 0`; there is no BTRFS_FS_ZONED flag, and
  `device->zone_info` does not decide it.
- `btrfs_fs_incompat(fs_info, ZONED)`: the gate for both
  `btrfs_get_dev_zone_info()` and `btrfs_check_zoned_mode()`; device type
  never turns zoned mode on, and without the flag `btrfs_check_zoned_mode()`
  returns `-EINVAL` if any device is zoned.
- `fs_info->zone_size` has two writers: `btrfs_check_zoned_mode()` and
  `calculate_emulated_zone_size()`.
- `calculate_emulated_zone_size()` runs from `btrfs_get_dev_zone_info()` for
  a non-zoned device while `fs_info->zone_size` is 0, so with such a device
  `btrfs_is_zoned()` is already true before `btrfs_check_zoned_mode()` runs
  in `open_ctree()`.
- Emulated zone size: the length of a dev extent from `fs_info->dev_root`;
  there is no BTRFS_EMULATED_ZONE_SIZE and no fixed default.
- Zoned and non-zoned devices in one fs: accepted only if the dev extent
  length equals the zoned devices' zone size; otherwise
  `btrfs_check_zoned_mode()` fails on unequal zone sizes.
- Host-aware and host-managed: fs/btrfs does not distinguish them; the only
  device test is `bdev_is_zoned()`.
- Device with no `bdev` (missing): skipped by
  `btrfs_get_dev_zone_info_all_devices()` and by the loop in
  `btrfs_check_zoned_mode()`.
- Device added or used as replace target after mount:
  `btrfs_check_device_zone_type()` in `fs/btrfs/zoned.h` admits any non-zoned
  device on a zoned fs, and a zoned one only with equal zone size.
- Without `CONFIG_BLK_DEV_ZONED`: `btrfs_get_dev_zone_info()` and
  `btrfs_check_zoned_mode()` are stubs in `fs/btrfs/zoned.h`; the
  `-EOPNOTSUPP` in the `btrfs_check_zoned_mode()` stub is behind
  `btrfs_is_zoned()`, which is constant false there.
- `btrfs_check_zoned_mode()` failures besides unequal zone sizes,
  `MIXED_GROUPS` and `NODATACOW`: `blk_validate_limits()` on the stacked
  limits; zone size not aligned to `BTRFS_STRIPE_LEN`; the `SPACE_CACHE`
  mount option (`btrfs_check_mountopts_zoned()`).
- `btrfs_check_zoned_mode()` tests no feature flag other than `ZONED` and
  `MIXED_GROUPS`, and no active-zone limit.
- Zone size not a power of two: `btrfs_get_dev_zone_info()` has only
  `ASSERT(is_power_of_two_u64(zone_sectors))`, no error return; for a zoned
  device `btrfs_sb_log_location_bdev()` returns `-EINVAL`, which fails
  `btrfs_read_disk_super()`.
- Device size not a multiple of the zone size: not rejected; `nr_zones` is
  rounded up to count the last partial zone.
- Zone report for a zoned device: `btrfs_get_dev_zones()` calls
  `blkdev_report_zones_cached()`, not `blkdev_report_zones()`; a report of
  zero zones returns `-EIO`.
- Superblock log check: skipped for a mirror whose zone pair does not fit in
  `nr_zones`, and when the first zone of the pair is conventional.
- Superblock log check otherwise: any `sb_write_pointer()` error except
  `-ENOENT` becomes `-EUCLEAN`; the invalid states are in the table comment
  in `sb_write_pointer()`.
- `calculate_emulated_zone_size()` errors also fail
  `btrfs_get_dev_zone_info()`: `-ENOMEM`, a tree search error, or `-EUCLEAN`
  when no item is found.

**Zone append writes**

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

## Active zone limits

**Active and open zones**

- Conditions counted as active: four, not three. The switch in
  `btrfs_get_dev_zone_info()` also has `BLK_ZONE_COND_ACTIVE`.
- `BLK_ZONE_COND_ACTIVE`: the case that is hit on a zoned device.
  `btrfs_get_dev_zones()` reads through `blkdev_report_zones_cached()`, which
  reports implicitly open, explicitly open and closed zones under this one
  condition.
- `bdev_max_open_zones()` and `bdev_max_active_zones()`: return what the block
  layer stored, which may differ from what the device reported. See
  `disk_update_zone_resources()` in `block/blk-zoned.c`.
- Device with neither limit, a zone write plug pool and more than
  `BLK_ZONE_WPLUG_DEFAULT_POOL_SIZE` (128) sequential zones:
  `bdev_max_open_zones()` returns 128, `bdev_max_active_zones()` returns 0.
- Limit that is >= the number of sequential zones:
  `disk_update_zone_resources()` resets it to 0 although the device reported
  a limit; when both limits are then 0, the bullet above applies to
  `bdev_max_open_zones()`.
- `blk_validate_zoned_limits()` in `block/blk-settings.c`: returns `-EINVAL`
  for `max_open_zones > max_active_zones`, only when `max_active_zones` is
  non-zero.

**Active zone limit computation**

- `btrfs_get_max_active_zones()` in `fs/btrfs/zoned.c` does the computation.
  `btrfs_get_dev_zone_info()` calls it before the zone scan.
- Both limits non-zero: the smaller one is used (`min_not_zero()`), not the
  active limit.
- Neither limit reported: `min(zone_info->nr_zones / 4,
  BTRFS_DEFAULT_MAX_ACTIVE_ZONES)`, whatever the number of zones.
- Lower bound: the result is raised to `BTRFS_MIN_ACTIVE_ZONES` with `max()`.
  A small limit does not fail the mount.
- Result of `btrfs_get_max_active_zones()`: never 0, so every device starts
  with a limit.
- Raised limit: `zone_info->max_active_zones` can be larger than the limit the
  device reported.
- `-EINVAL` from `btrfs_get_max_active_zones()`: only for
  `zone_info->nr_zones < BTRFS_MIN_ACTIVE_ZONES`, with the message "not enough
  zones to mount filesystem".
- Non-zoned device with emulated zones: takes the same path and gets a
  non-zero limit. `emulate_report_zones()` reports no active zone, so
  `BTRFS_FS_ACTIVE_ZONE_TRACKING` is set.

**Exceeding the limit at mount**

- `nactive > zone_info->max_active_zones` with `bdev_max_active_zones(bdev) > 0`:
  `btrfs_get_dev_zone_info()` returns `-EIO`.
- Same excess with `bdev_max_active_zones(bdev)` equal to 0: it sets
  `zone_info->max_active_zones` to 0 and goes on. This covers a limit taken
  from `bdev_max_open_zones()`, from the default, or from the clamp.
- `zone_info->max_active_zones` equal to 0: arises only from that fallback.
- `btrfs_get_dev_zone_info()` has no local copy of the limit; it uses
  `zone_info->max_active_zones` only.
- `zone_info->active_zones`: always allocated and filled by the scan, also for
  a device that ends with a zero limit. On such a device it is not updated
  afterwards.
- `call_zone_finish()` on a zero-limit device: returns 0 before
  `REQ_OP_ZONE_FINISH`. `do_zone_finish()` still marks the block group full
  and inactive, so the zone on the device is not finished.
- `btrfs_load_zone_info()` on a zero-limit device: marks the stripe active
  before it looks at the zone, so a block group whose stripes are all on such
  devices has `BLOCK_GROUP_FLAG_ZONE_IS_ACTIVE` from load or creation, even on
  an empty zone.
- `BTRFS_FS_ACTIVE_ZONE_TRACKING`: a flag for the whole file system, set by
  any device that passes the check. Without it,
  `btrfs_check_meta_write_pointer()` does not call `check_bg_is_active()` and
  `btrfs_check_active_zone_reservation()` sets no reserve.
- **Unsafe usage**: failing when the active zones of an existing file system
  exceed the limit btrfs computed while `bdev_max_active_zones()` is 0.
  - Safe: fail only when `bdev_max_active_zones()` is non-zero; otherwise set
    `zone_info->max_active_zones` to 0 and set neither `active_zones_left` nor
    `BTRFS_FS_ACTIVE_ZONE_TRACKING`, as `btrfs_get_dev_zone_info()` does.
- **Unsafe usage**: taking a non-zero `bdev_max_open_zones()`, or the value of
  `zone_info->max_active_zones`, as proof that the device reported a limit.
  - Unsafe: `disk_update_zone_resources()` sets `max_open_zones` itself on a
    device with no limits, and `btrfs_get_max_active_zones()` stores a
    non-zero limit for a device that reported none.
  - Safe: test `bdev_max_active_zones()` at the time of the check, as
    `btrfs_get_dev_zone_info()` does.

**Zone activation and finish**

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

## Transactions, paths and on-disk items

**Transaction abort**

- Error state: there is no BTRFS_FS_STATE_ERROR bit in this tree;
  `__btrfs_handle_fs_error()` stores the errno in `fs_info->fs_error`, tested
  with `BTRFS_FS_ERROR()` in `fs/btrfs/fs.h`.
- `btrfs_abort_should_print_stack()` in `fs/btrfs/transaction.h` (there is no
  abort_should_print_stack()): false for exactly `-EIO`, `-EROFS`, `-ENOMEM`.
- `btrfs_handle_fs_error()`: touches no transaction; it does not set
  `trans->aborted` or `BTRFS_FS_STATE_TRANS_ABORTED` and wakes no transaction
  waiters.
- `btrfs_handle_fs_error()` call sites: none in `fs/btrfs/transaction.c` or
  `fs/btrfs/disk-io.c`; `btrfs_commit_transaction()` calls
  `btrfs_abort_transaction()` when `btrfs_write_and_wait_transaction()` fails.
- Choosing between the two: see `process_one_buffer()` in
  `fs/btrfs/tree-log.c`, which aborts when `trans` is non-NULL and calls
  `btrfs_handle_fs_error()` otherwise; it is also used where no handle is
  held, for example in `rollback_verity()` in `fs/btrfs/verity.c` when
  starting the transaction failed.
- Helper that aborts: returns the error without ending the handle, as
  `btrfs_update_root()` in `fs/btrfs/root-tree.c` does; the function that
  started or joined the handle ends it.
- `btrfs_commit_transaction()`: frees the handle on every return path,
  including errors, so no `btrfs_end_transaction()` may follow it.
- **Unsafe usage**: passing a value that can be zero or positive to
  `btrfs_abort_transaction()`, such as an unconverted `1` from
  `btrfs_search_slot()`.
  - Unsafe: the sign carries "first abort" into
    `__btrfs_abort_transaction()`, so a positive value inverts it and is
    stored negated; zero is stored in `trans->aborted` and
    `fs_info->fs_error`, so `TRANS_ABORTED()` and `BTRFS_FS_ERROR()` are false
    afterwards.
  - Unsafe: `VERIFY_NEGATIVE_ERROR()` in `fs/btrfs/transaction.h` breaks the
    build only for a compile-time constant that is not negative; a variable
    is checked only under `CONFIG_BTRFS_DEBUG`, by `DEBUG_WARN()`.
  - Safe: convert first, as `__btrfs_update_delayed_inode()` in
    `fs/btrfs/delayed-inode.c` does with `if (ret > 0) ret = -ENOENT;`.

**Paths and search results**

- `BTRFS_PATH_AUTO_RELEASE()` in `fs/btrfs/ctree.h`: declares an on-stack,
  zeroed `struct btrfs_path` that gets `btrfs_release_path()` at scope exit;
  no allocation, pass `&path`; see `fs/btrfs/scrub.c` for a user.
- `btrfs_search_slot()` returning `< 0`: the path holds nothing taken by the
  search (`btrfs_release_path()` runs at `done:`), unless
  `p->skip_release_on_error` is set, or the error is `-ENOMEM` from
  `finish_need_commit_sem_search()` (`p->need_commit_sem` set).
- `p->skip_release_on_error`: the path can still hold its extent buffers and
  locks after the error and the caller must release it; set for example
  before `btrfs_insert_empty_item()` in `fs/btrfs/inode-item.c` and
  `fs/btrfs/tree-log.c`.
- Reusing a path: `btrfs_search_slot()` only does
  `WARN_ON(p->nodes[0] != NULL)` at entry, it does not release, so the caller
  must call `btrfs_release_path()` between searches.

**Path position after a search**

- `btrfs_prev_leaf()`: `static` in `fs/btrfs/ctree.c`, not callable from other
  files; at `path->slots[0] == 0` use `btrfs_previous_item()`,
  `btrfs_previous_extent_item()`, `btrfs_search_backwards()`, or
  `btrfs_search_slot_for_read()` with `find_higher` 0.
- `btrfs_next_item()`: increments `path->slots[0]` before it tests against
  `btrfs_header_nritems()`, so straight after a not-found search it skips the
  item at the insert slot; `btrfs_get_next_valid_item()` tests without
  incrementing.
- `btrfs_next_leaf()`: releases the path and searches again, so a leaf pointer
  saved before the call is stale; reload it from `path->nodes[0]`, as
  `btrfs_lookup_csums_list()` in `fs/btrfs/file-item.c` does.
- `btrfs_next_leaf()` returning 0: the slot can be a later slot of the same
  leaf, not slot 0 of a new one, when items were added while the path was
  released; see `btrfs_next_old_leaf()`.

**On-disk format changes**

- Buffer bounds: `btrfs_get_64()` and its siblings in `fs/btrfs/accessors.c`,
  `read_extent_buffer()` and `write_extent_buffer()` check against `eb->len`
  themselves and return no error: a get returns 0, a set is dropped, a read
  zero-fills, each with a `btrfs_warn()`.
- Item bounds: nothing in the accessors checks them; an offset past
  `btrfs_item_size()` but inside the buffer reads a neighbouring item, so the
  caller must bound it.
- `btrfs_mark_buffer_dirty()` after setting members: not required for a leaf
  from `btrfs_search_slot()` with `cow` set; `btrfs_update_root()` in
  `fs/btrfs/root-tree.c` writes and returns without it, and
  `btrfs_force_cow_block()` marks the copy dirty.
- `btrfs_mark_buffer_dirty()`: asserts the buffer is write-locked (lockdep,
  only under `CONFIG_BTRFS_DEBUG`) and aborts the transaction with `-EUCLEAN`
  if the header generation is not the running one.
- **Unsafe usage**: passing a pointer from `btrfs_item_ptr()` to an accessor
  generated by `BTRFS_SETGET_STACK_FUNCS()`, which dereferences it.
  - Unsafe: the type does not catch it, and not every such accessor has
    `stack_` in its name: `btrfs_root_generation()`, `btrfs_super_flags()`
    and `btrfs_disk_key_objectid()` take plain memory.
  - Safe: the extent buffer form for `struct btrfs_root_item` is
    `btrfs_disk_root_bytenr()` and siblings, as `btrfs_print_leaf()` uses.
  - Safe: copy with `read_extent_buffer()` into a local, then use the stack
    accessor, as `check_root_item()` in `fs/btrfs/tree-checker.c` does.
- `fs/btrfs/accessors.c`: holds only the generic sized helpers and
  `btrfs_node_key()`; per-member accessors go in `fs/btrfs/accessors.h` only.
- `fs/btrfs/print-tree.c`: a new key type needs an entry in `key_to_str[]` in
  `key_type_string()` as well as a case in `btrfs_print_leaf()`; without the
  entry the key prints as `UNKNOWN.<n>`.
- `include/trace/events/btrfs.h`: has no table of item key types;
  `show_ref_type()` names four backref keys and `__show_root_type()` names
  tree objectids.
- `check_leaf_item()`: has no `default:` case, so a key type without a case
  gets no content check; `__btrfs_check_leaf()` still checks key order and
  item offset and size for it.
- Key types with no case in `check_leaf_item()`: for example
  `BTRFS_ORPHAN_ITEM_KEY`, `BTRFS_QGROUP_INFO_KEY` and `BTRFS_DEV_REPLACE_KEY`;
  code that reads these must validate size and members itself.
- Write-time check: `btree_csum_one_bio()` in `fs/btrfs/disk-io.c` runs
  `btrfs_check_leaf()` or `btrfs_check_node()` on a tree block before it is
  written, and fails the write with "write time tree block corruption
  detected".
- New member or size: the checker must accept every layout the kernel itself
  writes, or writeback fails; gate the expected size on `btrfs_fs_incompat()`
  as `check_block_group_item()` does for
  `struct btrfs_block_group_item_v2`.
- Supported feature masks: in `fs/btrfs/fs.h`; `BTRFS_FEATURE_INCOMPAT_SUPP`
  is `BTRFS_FEATURE_INCOMPAT_SUPP_STABLE` plus extra bits only under
  `CONFIG_BTRFS_EXPERIMENTAL`.

## Model gaps

### Other mistakes models make

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
