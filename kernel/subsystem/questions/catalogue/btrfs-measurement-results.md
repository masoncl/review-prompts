# What the btrfs measurement found

Three models were asked the 48 questions in `btrfs-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels 6.15 to 6.18), reader A close behind it (6.12 to 6.17), and
reader B older (6.10 to 6.12) with the extent map structure itself out of date.
The hand-written guide was never checked against current sources, so
differences between it and the built guide are expected and are noted near the
end.

Readers A and C know what the hand-written guide teaches about extent maps: the
fields, the two helpers, which size is which, and even the escape hatch in the
active zone check at mount. Reader B answers every extent map question in terms
of members that are gone. What all three get wrong is how the active zone limit
is computed now, what happens to extent maps on the list of modified extents,
and a long tail of names that gained a `btrfs_` prefix.

## What all three readers got wrong

- **The active zone limit.** All three put the computation inline in
  `btrfs_get_dev_zone_info()`, said a device with no limit gets 128 only if it
  has more than 128 zones and is otherwise unlimited, and said a limit below
  the minimum fails the mount. The tree has `btrfs_get_max_active_zones()`:
  `min_not_zero()` of the active and open limits; if that is zero,
  `min(nr_zones / 4, BTRFS_DEFAULT_MAX_ACTIVE_ZONES)`; then raised with `max()`
  to `BTRFS_MIN_ACTIVE_ZONES`. `-EINVAL` is only for a device with fewer zones
  than that minimum. The limit is zero only after the mount check clears it.
- **`BLK_ZONE_COND_ACTIVE`** is counted as active beside implicitly open,
  explicitly open and closed. No reader listed it.
- **Zone activation.** The reserve set by
  `btrfs_check_active_zone_reservation()` is two zones for metadata (one for
  the tree log), four with DUP, and one for system, two with DUP; readers said
  one each. Data block groups are activated at allocation in
  `do_allocation_zoned()` and at chunk allocation, metadata and system at write
  time in `check_bg_is_active()`. `btrfs_zone_activate()` takes
  `zone_active_bgs_lock` before the block group lock.
- **Extent maps on the list of modified extents are not protected from the
  shrinker.** Each reader had it skip more than it does: maps on the list, maps
  being logged, maps with extra references. `btrfs_scan_inode()` skips only
  `EXTENT_FLAG_PINNED`; it removes a listed map and calls
  `btrfs_set_inode_full_sync()` when its generation is current. It try-locks
  the tree's `lock` for write and then `i_mmap_lock` for read, and takes no
  range lock. `try_release_extent_mapping()` has the opposite rule: it keeps a
  listed map of the current generation and so never needs the full sync.
- **Fiemap does not read extent maps.** `fs/btrfs/fiemap.c` never touches
  `struct extent_map`; it walks file extent items and finds delalloc through
  the io tree bits and ordered extents. Every reader had it depend on extent
  maps in at least one answer, and a comment in `btrfs_fiemap()` still says so.
- **Merging.** Compressed maps and maps still on the modified list are never
  merged, so a map just unpinned is merged only after it is logged. The
  `refs > 2` test applies to the map being processed, not to its neighbour.
  After a merge `ram_bytes` equals the merged `disk_num_bytes`.
- **Locking.** `btrfs_add_extent_mapping()` and the lookup functions take no
  lock; drop, replace, unpin and split take the write lock themselves;
  `add_extent_mapping()`, `btrfs_remove_extent_mapping()` and
  `btrfs_clear_em_logging()` assert it. Eviction drops the whole tree without a
  range lock.
- **`btrfs_split_extent_map()`** builds two new maps with `offset` 0 and a new
  `disk_bytenr` for the front one; its only callers are
  `btrfs_extract_ordered_extent()` and `btrfs_zoned_split_ordered()`, and it
  can return `-EIO`.
- **Unprefixed names.** Each reader offered at least one of create_io_em(),
  unpin_extent_cache(), split_extent_map(), extent_map_set_compression(),
  lock_extent() or free_extent_map(). All have a `btrfs_` prefix now.
- **Folio state.** The bitmaps are uptodate, dirty, writeback and fixup;
  locked blocks are the counter `nr_locked`. All three listed ordered, checked
  and locked bitmaps. The structure is `struct btrfs_folio_state`, and
  `btrfs_is_subpage()` compares the block size with the folio's size.
- **Direct I/O range lock.** `lock_extent_direct()` takes `EXTENT_DIO_LOCKED`
  and then `EXTENT_LOCKED` as well, not one instead of the other. Buffered
  reads go through `lock_extents_for_read()`, and writeback takes the range
  lock in `cow_one_range()` and `nocow_one_range()`.
- **Zoned metadata writes.** `btrfs_check_meta_write_pointer()` only checks;
  `write_meta_extent_buffer()` advances the pointer. A buffer not at the
  pointer gives `-EBUSY` and is skipped; `-EAGAIN` ends `btree_writepages()`.
  Readers named btrfs_redirty_list_add() and btree_write_cache_pages(), which
  are not in the tree.
- **Zone append.** The operation is set in `btrfs_submit_dev_bio()`;
  `btrfs_record_physical_zoned()` shifts `sum->logical`;
  `btrfs_finish_ordered_zoned()` is called from `btrfs_finish_ordered_io()` and
  rewrites `ordered->disk_bytenr` and `em->disk_bytenr`.
- The on-disk features that need `CONFIG_BTRFS_EXPERIMENTAL`: raid stripe
  tree, extent tree v2 and remap tree. Each reader was unsure of at least one.

## What only some readers got wrong

Reader B, and nobody else:

- `struct extent_map` has block_start, block_len, orig_start, orig_block_len
  and compress_type, and flags EXTENT_FLAG_COMPRESSED, EXTENT_FLAG_FILLING and
  EXTENT_FLAG_FS_MAPPING. None exists. The members are `disk_bytenr`,
  `disk_num_bytes`, `offset` and `ram_bytes`, compression is three bits in
  `flags`, and chunk maps are `struct btrfs_chunk_map`. This ran through ten of
  its answers.
- The whole interface unprefixed and with old signatures; the write path builds
  an extent map itself where the tree passes a `struct btrfs_file_extent` to
  `btrfs_create_io_em()`.
- A failed `validate_extent_map()` warns and carries on. Its failure path,
  `dump_extent_map()`, ends in `ASSERT(0)`.
- The shrinker walks a per-file-system list of inodes in reclaim context. It is
  a work item that walks the roots and each root's inode xarray.
- At mount the active zone check depends on read-only against read-write. It
  depends only on whether `bdev_max_active_zones()` is non-zero.
- `btrfs_handle_fs_error()` forces read-only and an abort does not; an abort
  calls it. Token helpers for on-disk access, which are gone.

Readers A and B:

- `btrfs_create_io_em()` asserts `disk_num_bytes < ram_bytes` for a compressed
  write and relations between the disk sizes for a preallocated one. It asserts
  `num_bytes <= ram_bytes` for both, a compression type for the first, and no
  more.
- Siblings in a tree are locked left to right. `push_leaf_left()` locks the
  left leaf while holding the right one; the rule is that the parent is held.
- `struct btrfs_subpage`; it is `struct btrfs_folio_state`.

Reader A alone: holes always have `ram_bytes == len` (only some paths set it);
`EXTENT_FLAG_PREALLOC` and `EXTENT_FLAG_MERGED` are cleared (nothing clears
either); `data_reloc_bg` is under a lock of its own (it is
`relocation_bg_lock`); block_start still used in two answers.

Readers B and C: a disabled `ASSERT()` expands to nothing or to a void cast of
its condition. It is `BUILD_BUG_ON_INVALID()`, which compiles the condition and
does not evaluate it.

Reader C alone: `disk_num_bytes < ram_bytes` holds for every compressed extent
(only the write paths enforce it); `btrfs_replace_extent_map_range()` can
return an error (it loops on `-EEXIST` and returns 0); a zoned file system
fails to mount without `CONFIG_BLK_DEV_ZONED` (the stub check passes).

## What the readers already knew

Readers A and C: the fields of `struct extent_map` and what each matches on
disk, `btrfs_extent_map_block_start()` and the file-private
`extent_map_block_len()`, the compressed and partial layouts, the exported
function names, `struct btrfs_chunk_map`, what a lookup may hand back, and the
rule for the mount check (fail only on a limit the device itself reports).
All three: where the files are, the entry points, that the active and open
limits are different things and either may be zero, how a path is allocated
and what `btrfs_search_slot()` returns, when to abort a transaction. These are
dropped from the build set or kept short; the field table stays because reader
B has the old structure.

## Where the hand-written guide is stale

- Its code for the active zone check is not in the tree. The limit is computed
  in `btrfs_get_max_active_zones()`, which also applies a default of a quarter
  of the zones capped at 128 and a floor of `BTRFS_MIN_ACTIVE_ZONES`, neither
  of which the guide mentions. The mount check fails when
  `bdev_max_active_zones()` is non-zero and otherwise sets the limit to zero
  without setting `BTRFS_FS_ACTIVE_ZONE_TRACKING`; there is no label to jump
  to.
- Its invariants leave out the alignment checks and do not say that
  `validate_extent_map()` does nothing without `CONFIG_BTRFS_DEBUG`.
- Its table gives `disk_num_bytes` as the number of bytes to read or write and
  `len` as the mistake. That holds for a compressed extent only. For an
  uncompressed one the map's I/O covers `len` bytes from `disk_bytenr + offset`
  and `disk_num_bytes` is the whole extent, which is what
  `extent_map_block_len()` encodes.
- It says `disk_num_bytes` is smaller than `len` for compressed extents.
  Nothing relates the two; a map may cover a small part of a large compressed
  extent.
- It says the fields correspond to the file extent item. After a merge they do
  not, and for uncompressed extents `ram_bytes` is overwritten with
  `disk_num_bytes` when the item is read.
- Correct and kept as questions: what each field holds, the two helpers and
  which is private, the layouts, the confusion between the three sizes, that
  active and open zones differ, and that a derived limit must not fail the
  mount of an existing file system.

## Left out of the build set

The hand-written guide is 744 words, so the build set holds 13 of the 48
questions, with 670 words of budget and none under 40, and stays on the guide's
two topics. With titles and headings that comes to about 810 words, inside the
595 to 892 allowed. A first build set had 16 questions in 600 words, ten of
them under 40, and about one bullet in five of the guides built from it was a
fragment that meant nothing without its question. Most of these questions ask
for three to five things, so the room went to their answers, and three
questions the readers answer well were dropped instead: the table of files (all
three readers know where things are), the list of interface names (readers A
and C know them, and the answers on locking, fsync and the change checklist
spell the functions a reader is likely to misname), and active against open
zones (all three know that the two limits differ and that either may be absent;
what they missed, `BLK_ZONE_COND_ACTIVE`, is in the `switch` in
`btrfs_get_dev_zone_info()` and in any patch that touches the count). Six are
worded differently from the measurement set: the field table also names the
flag bits in full, the helpers question also covers holes, the limit
computation asks for its constants by name, the activation question asks
whether any zones are held back before asking how many, and the two questions
on changing the code name fiemap and the code that removes listed maps. Left
out although a reader got them wrong: holes and inline extents, the
flags table, references, lookup results, creating maps and the asserts on a new
write, ordered extent fields, dropping a range, the shrinker's own question and
the self-tests (the question on modified maps carries the shrinker's main
fact); the rest of zoned mode (zone information, block group state, refused
features, zone append, metadata write order, dedicated block groups), each
confined to `fs/btrfs/zoned.c` and open in any patch that touches it; and the
general conventions (abort, assert, paths, on-disk format, tree, range and
inode locks, the ordered extent life cycle, folio state, the config options),
which belong to a wider btrfs guide than this one has room for.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 125 corrections, 34% rewritten on average
reader B: 151 corrections, 78% rewritten on average
reader C: 118 corrections, 25% rewritten on average

question                         reader A      reader B      reader C
btrfs.core-files                  0% ( 0)      24% ( 3)       0% ( 2)
btrfs.entry-points                0% ( 0)      20% ( 4)       8% ( 2)
btrfs.docs-and-tests              0% ( 0)      82% ( 3)      32% ( 3)
btrfs.debug-config               24% ( 3)      88% ( 4)      47% ( 4)
btrfs.em-purpose                 28% ( 5)      76% ( 3)      16% ( 2)
btrfs.em-fields                  15% ( 1)      63% ( 2)      35% ( 2)
btrfs.em-block-helpers            0% ( 0)      91% ( 1)      11% ( 1)
btrfs.em-layouts                 10% ( 1)      71% ( 1)      25% ( 2)
btrfs.em-sentinels               43% ( 3)      85% ( 4)       9% ( 2)
btrfs.em-flags                   38% ( 4)      67% ( 3)      10% ( 3)
btrfs.em-invariants              33% ( 2)      87% ( 2)      24% ( 3)
btrfs.em-field-usage             33% ( 5)      81% ( 7)       5% ( 1)
btrfs.em-write-target             7% ( 1)      91% ( 4)       5% ( 1)
btrfs.ordered-extent-fields      33% ( 3)      79% ( 3)      32% ( 3)
btrfs.em-api                      5% ( 3)      80% ( 9)       2% ( 2)
btrfs.em-locking                 38% ( 4)      77% ( 3)      30% ( 2)
btrfs.em-refcount                16% ( 1)      80% ( 3)      24% ( 2)
btrfs.em-lookup-result           45% ( 2)      78% ( 2)       4% ( 0)
btrfs.em-merging                 20% ( 3)      85% ( 3)      23% ( 1)
btrfs.em-creation                17% ( 3)      66% ( 5)       6% ( 0)
btrfs.em-pinned-logging          36% ( 6)      80% ( 4)      33% ( 3)
btrfs.em-drop-range              48% ( 3)      87% ( 3)      17% ( 2)
btrfs.em-shrinker                63% ( 3)      90% ( 4)      34% ( 1)
btrfs.em-selftests               52% ( 2)      87% ( 1)       9% ( 2)
btrfs.chunk-maps                 15% ( 1)      83% ( 2)       6% ( 2)
btrfs.fiemap-source              63% ( 3)      80% ( 2)      40% ( 4)
btrfs.zoned-overview             59% ( 4)      82% ( 6)      24% ( 5)
btrfs.zone-info                  38% ( 4)      79% ( 4)      33% ( 3)
btrfs.zoned-bg-state             43% ( 3)      85% ( 4)      16% ( 1)
btrfs.zoned-restrictions         61% ( 3)      94% ( 5)      34% ( 3)
btrfs.active-vs-open             30% ( 1)      63% ( 1)      13% ( 2)
btrfs.max-active-zones           53% ( 1)      83% ( 2)      61% ( 3)
btrfs.active-limit-mount         34% ( 1)      81% ( 1)      27% ( 2)
btrfs.zone-limit-usage           11% ( 1)      87% ( 1)      12% ( 1)
btrfs.zone-activation            61% ( 1)      84% ( 1)      55% ( 2)
btrfs.zone-append                60% ( 5)      75% ( 5)      31% ( 6)
btrfs.zoned-meta-write           76% ( 4)      77% ( 3)      37% ( 2)
btrfs.zoned-dedicated-bgs        48% ( 3)      87% ( 2)      40% ( 1)
btrfs.trans-abort                 7% ( 1)      66% ( 2)      30% ( 4)
btrfs.assert                     10% ( 1)      83% ( 1)      32% ( 4)
btrfs.path-and-search            15% ( 1)      77% ( 1)      19% ( 2)
btrfs.on-disk-format             22% ( 5)      72% ( 1)      41% ( 4)
btrfs.tree-locking               43% ( 4)      80% ( 3)      54% ( 3)
btrfs.range-locking              33% ( 3)      71% ( 4)      42% ( 4)
btrfs.inode-locks                56% ( 2)      86% ( 3)       6% ( 1)
btrfs.ordered-lifecycle          37% ( 5)      84% ( 3)      33% ( 4)
btrfs.subpage                    67% ( 3)      90% ( 5)      43% ( 4)
btrfs.change-checklist           88% ( 7)      92% ( 8)      47% ( 5)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `btrfs.zoned-overview`, `btrfs.zone-append`, `btrfs.subpage`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `btrfs.em-sentinels`, `btrfs.em-flags`, `btrfs.em-write-target`, `btrfs.ordered-extent-fields`, `btrfs.em-api`, `btrfs.em-refcount`, `btrfs.em-lookup-result`, `btrfs.em-creation`, `btrfs.em-drop-range`, `btrfs.chunk-maps`, `btrfs.active-vs-open`, `btrfs.trans-abort`, `btrfs.path-and-search`, `btrfs.on-disk-format`, `btrfs.range-locking`, `btrfs.ordered-lifecycle`.
Put back because a guide has to say what each main structure is before anything else: `btrfs.em-purpose`.

## Questions reorganised

35 questions before and 35 after, by subject: extent map fields and sizes (9), the extent map
tree (10), writes and ordered extents (5), zoned mode (2), active zone limits (4), and
transactions, paths and on-disk items (3). Merged: `btrfs.active-limit-mount` and
`btrfs.zone-limit-usage` into `btrfs.active-limit-check`; the mount check is the correct form the
hazard asks for. Split: what reclaim may remove left `btrfs.em-pinned-logging` for
`btrfs.em-shrinker`, since every reader had reclaim skip more than it does. Nothing dropped.
Inventories reworded to ask what a reviewer gets wrong: `btrfs.em-fields`, `btrfs.em-flags`,
`btrfs.em-api`, `btrfs.em-creation`, `btrfs.ordered-extent-fields`, `btrfs.change-checklist`.
