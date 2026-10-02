# Questions: Btrfs (measurement set)

- guide: btrfs.md
- title: Btrfs Subsystem Details

A wide set of questions about btrfs, used to measure what a model already
knows before deciding what the built guide should spend its words on. The
hand-written guide it will replace is 744 words and covers two topics, the
fields of an extent map and the limit on active zones in zoned mode, so the set
is widest there and thinner on the rest of the file system. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## btrfs.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

Which files hold extent maps, the file extent items and checksums, ordered
extents, the per-inode and per-tree range locks, buffered read and writeback,
direct I/O, compression, the bio layer, chunk and device mapping, block groups
and space accounting, transactions, the tree log, tree locking, the
tree checker, zoned mode and the self-tests? A table. Start from `fs/btrfs/`.

## btrfs.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

For each job (get the extent map for a file range, read a folio, write back a
delalloc range, finish an ordered extent, fsync a file, start a direct I/O,
clone a range, punch a hole, map a logical address to devices, load a device's
zone information), which function do you start reading from? A table.

## btrfs.docs-and-tests: Documentation and tests

- section: Finding your way
- relevance: 3 - says what can be run before sending a change
- words: 70

What documentation for btrfs is in the kernel tree and what is kept elsewhere,
where are the in-kernel self-tests, how are they built and when do they run,
and which external test suite do the developers expect a change to pass? Start
from `Documentation/filesystems/btrfs.rst` and `fs/btrfs/tests/`.

## btrfs.debug-config: Debug and experimental options

- section: Finding your way
- relevance: 3 - a check that only runs under one option is not a guarantee
- words: 80

What does each of `CONFIG_BTRFS_DEBUG`, `CONFIG_BTRFS_ASSERT`,
`CONFIG_BTRFS_EXPERIMENTAL` and `CONFIG_BTRFS_FS_RUN_SANITY_TESTS` turn on, and
which on-disk features can only be mounted with the experimental option? Start
from `fs/btrfs/Kconfig` and `BTRFS_FEATURE_INCOMPAT_SUPP` in `fs/btrfs/fs.h`.

# Extent maps

## btrfs.em-purpose: Extent map purpose

- section: The extent map structure
- relevance: 4 - nothing else about the structure makes sense without it
- words: 80

What is a `struct extent_map`, where do instances live, what on-disk item does
one stand for, and is the set an inode holds authoritative or a cache that can
be thrown away and reloaded? Say what it is not used for in this tree as well.
Start from `fs/btrfs/extent_map.h`.

## btrfs.em-fields: Extent map fields

- section: The extent map structure
- relevance: 5 - every use of an extent map reads these
- words: 120

Give a table of the fields of `struct extent_map` in this tree: what each
holds, and which member of `struct btrfs_file_extent_item` or of the item's key
it matches for a regular extent. Say which fields keep matching the on-disk
item for the whole life of the extent map and which may stop matching.

## btrfs.em-block-helpers: Disk address and length

- section: The extent map structure
- relevance: 5 - the wrong address or length reads or writes the wrong blocks
- words: 100

How does code get the disk address at which I/O for an extent map starts, and
the number of bytes on disk that it covers: are they members of the structure
or computed, by what, and what do they return for a compressed and for an
uncompressed extent? Say for each whether it is visible outside
`fs/btrfs/extent_map.c`, and how code elsewhere gets a value whose helper is
not.

## btrfs.em-layouts: Compressed and partial layouts

- section: The extent map structure
- relevance: 5 - the fields only differ in the cases tests rarely cover
- words: 110

How do `len`, `disk_num_bytes`, `ram_bytes` and `offset` of an extent map
relate to each other for a plain uncompressed extent, for a compressed extent,
and for an extent map that refers to part of a larger extent after a clone or
an overwrite of its neighbours? In which of these cases are the three sizes
equal?

## btrfs.em-sentinels: Holes and inline extents

- section: The extent map structure
- relevance: 4 - a sentinel used as an address is an out-of-range I/O
- words: 80

How does an extent map say that a range is a hole or an inline extent, what do
its other fields hold in each case, and what comparison does code use to tell a
real extent from these? Start from `EXTENT_MAP_LAST_BYTE` and
`btrfs_extent_item_to_extent_map()`.

## btrfs.em-flags: Extent map flags

- section: The extent map structure
- relevance: 4 - several decide whether an extent map may be merged or dropped
- words: 90

Give a table of the bits in the `flags` of an extent map, what sets and clears
each, and how the compression type is recorded and read back. Start from
`EXTENT_FLAG_PINNED` in `fs/btrfs/extent_map.h`.

## btrfs.em-invariants: Extent map invariants

- section: The extent map structure
- relevance: 5 - says which combinations of the fields are legal
- words: 100

What does the tree check about an extent map's fields before it goes into an
inode's tree, for a real extent and for a hole or inline one, what happens when
a check fails, and in which configurations does the check run at all? Start
from `validate_extent_map()`.

## btrfs.em-field-usage: Choosing a size field

- section: Using the fields
- relevance: 5 - a recurring bug class that simple tests do not show
- words: 120

Which field of an extent map is the right one for the file range it covers, for
the number of bytes to read from or write to disk, and for the size of a buffer
that holds the decompressed extent? What usage of these fields is unsafe, and
what that looks similar is correct? Name in-tree code that shows the correct
use, for example in `fs/btrfs/compression.c`, `fs/btrfs/tree-log.c` or
`btrfs_encoded_read()`.

## btrfs.em-write-target: Describing a new write

- section: Using the fields
- relevance: 4 - the asserts here state the rules for each kind of write
- words: 100

What structure describes the extent a write is going to create, and what does
`btrfs_create_io_em()` require of its values for an ordinary copy-on-write
write, for a compressed write and for a write into a preallocated extent? What
does it do about a write that overwrites an existing extent in place?

## btrfs.ordered-extent-fields: Ordered extent fields

- section: Using the fields
- relevance: 4 - the same names as the extent map, with their own rules
- words: 100

Which fields of `struct btrfs_ordered_extent` describe the file range and the
extent on disk, how do they correspond to the on-disk file extent item, and
which flag bits say what type of write it is? How many type bits may be set at
once? Start from `fs/btrfs/ordered-data.h`.

## btrfs.em-api: Extent map interface

- section: The extent map tree
- relevance: 4 - the names have changed and a reader's memory offers old ones
- words: 110

List the functions this tree exports for extent maps: allocate and free, look
up, add, remove, replace a range, drop a range, split, unpin. For each give the
name as it is spelled in `fs/btrfs/extent_map.h`, what it takes and what it
returns.

## btrfs.em-locking: Extent map tree locking

- section: The extent map tree
- relevance: 5 - says what may be read or changed under which lock
- words: 100

Which lock protects an inode's extent map tree, which of the exported functions
take it themselves and which expect the caller to hold it and in which mode,
and what other lock over the file range must a caller hold before it drops or
replaces extent maps? Start from `struct extent_map_tree` and
`btrfs_drop_extent_map_range()`.

## btrfs.em-refcount: Extent map references

- section: The extent map tree
- relevance: 4 - a missing put leaks, an extra one frees a tree entry
- words: 90

Who holds references on an extent map, what does a lookup return with respect
to the count, what does removing one from the tree do to the count, and when
may the fields of an extent map that is in the tree be changed in place?

## btrfs.em-lookup-result: Lookup and insert results

- section: The extent map tree
- relevance: 4 - the entry handed back need not be the one asked for
- words: 100

What may `btrfs_lookup_extent_mapping()` and `btrfs_search_extent_mapping()`
return relative to the range asked for, and what does
`btrfs_add_extent_mapping()` do, and leave in its argument, when the range
collides with an entry already in the tree? What must the caller check
afterwards?

## btrfs.em-merging: Merging extent maps

- section: The extent map tree
- relevance: 4 - after a merge the fields no longer match one on-disk item
- words: 100

When are two adjacent extent maps merged into one, which extent maps are never
merged, and what do `disk_bytenr`, `disk_num_bytes`, `offset`, `ram_bytes` and
`generation` hold afterwards? Start from `try_merge_map()` and
`mergeable_maps()`.

## btrfs.em-creation: Creating extent maps

- section: The extent map tree
- relevance: 4 - each path fills the fields in its own way
- words: 100

Which code paths create extent maps (from an item in the subvolume tree, for a
hole, for a new write, for preallocation, for relocation), and which helper
turns a file extent item into one? What does that helper do with `ram_bytes`
for an uncompressed extent? Start from `btrfs_get_extent()`.

## btrfs.em-pinned-logging: Pinned and modified extent maps

- section: Extent maps and fsync
- relevance: 4 - dropping the wrong one loses data at the next fsync
- words: 110

What is the life of an extent map created for a write, from creation to the
end of the ordered extent: when is it pinned and unpinned, what is the list of
modified extents for, and what must code that removes an extent map from that
list do so that a later fsync is still correct? Start from
`btrfs_unpin_extent_cache()` and `btrfs_set_inode_full_sync()`.

## btrfs.em-drop-range: Dropping part of an extent map

- section: Extent maps and fsync
- relevance: 4 - the split halves must keep the fields consistent
- words: 100

When `btrfs_drop_extent_map_range()` cuts an extent map that straddles the
range, how are the fields of the remaining pieces computed, for a real extent
and for a hole, and what does it do when it cannot allocate the pieces? How
does `btrfs_split_extent_map()` differ, and who uses it?

## btrfs.em-shrinker: Extent map shrinker

- section: Extent maps and fsync
- relevance: 3 - runs at any time against any inode
- words: 90

How are extent maps reclaimed under memory pressure: what starts it, in which
context does it run, which roots, inodes and extent maps does it skip, and
which locks does it take and how? Start from `btrfs_free_extent_maps()`.

## btrfs.em-selftests: Extent map self-tests

- section: Around extent maps
- relevance: 3 - the code is also built into a test that has no real file system
- words: 70

Which self-tests exercise the extent map code, what stands in for the file
system and the inode when they run, and what must extent map code do so that it
still works there? Start from `fs/btrfs/tests/extent-map-tests.c` and
`btrfs_is_testing()`.

## btrfs.chunk-maps: Chunk mapping structure

- section: Around extent maps
- relevance: 4 - decides whether extent map code is shared with the volume layer
- words: 80

Which structure describes the mapping from a logical chunk to its device
stripes in this tree, where are the instances kept, which lock protects them
and which function looks one up? Does it share anything with
`struct extent_map`? Start from `fs/btrfs/volumes.h`.

## btrfs.fiemap-source: Fiemap data source

- section: Around extent maps
- relevance: 3 - decides whether a change to extent maps can change what fiemap reports
- words: 70

Where does fiemap get the extents it reports for a file in this tree: the
inode's extent maps, the items in the subvolume tree, the ranges waiting for
writeback, or some mix? Which locks does it hold while it does? Start from
`fs/btrfs/fiemap.c`.

# Zoned mode

## btrfs.zoned-overview: Zoned mode

- section: Zoned mode
- relevance: 4 - everything else in the section rests on it
- words: 90

What is zoned mode in btrfs, what decides that a file system is zoned, how are
devices that are not zoned handled inside a zoned file system, and which zone
sizes are accepted? Start from `btrfs_is_zoned()`, `btrfs_check_zoned_mode()`
and `fs/btrfs/zoned.c`.

## btrfs.zone-info: Per-device zone information

- section: Zoned mode
- relevance: 3 - the limits and the bitmaps the rest of the code reads
- words: 90

What does `struct btrfs_zoned_device_info` hold, when is it filled in and
freed, and what do its three bitmaps and its two counters of active zones mean?
Start from `fs/btrfs/zoned.h`.

## btrfs.zoned-bg-state: Zoned block group state

- section: Zoned mode
- relevance: 3 - allocation in a zoned block group is a write pointer, not a free space map
- words: 90

Which members and runtime flags of `struct btrfs_block_group` exist for zoned
mode, what does each mean, and how is free space in such a block group found
and given back? Start from `alloc_offset` and `btrfs_load_block_group_zone_info()`.

## btrfs.zoned-restrictions: Features refused in zoned mode

- section: Zoned mode
- relevance: 3 - a new feature has to say what it does on a zoned file system
- words: 80

Which mount options, file attributes, profiles and operations does zoned mode
refuse or change, and where is each checked? Start from
`btrfs_check_mountopts_zoned()` and `btrfs_check_zoned_mode()`.

## btrfs.active-vs-open: Active and open zones

- section: Active zone limits
- relevance: 4 - the two limits mean different things and either may be absent
- words: 90

In the block layer's model of a zoned device, what is an active zone and what
is an open zone, which zone conditions count as each, what do
`bdev_max_active_zones()` and `bdev_max_open_zones()` return when the device
has no such limit, and may a device report one limit without the other?

## btrfs.max-active-zones: Active zone limit computation

- section: Active zone limits
- relevance: 5 - the number every activation decision is made against
- words: 100

How does this tree arrive at the per-device limit on active zones that it
enforces: which limits of the block device go into it and how are they
combined, what is used when the device reports none, and is there a floor or a
minimum number of zones? Name the function. Start from
`btrfs_get_dev_zone_info()`.

## btrfs.active-limit-mount: Exceeding the limit at mount

- section: Active zone limits
- relevance: 5 - the difference between a warning and a file system that no longer mounts
- words: 100

When a device is found at mount to have more active zones than the limit btrfs
computed for it, what does the code do: when does the mount fail and with which
error, and when does it go on and in what state? What does the rest of the
zoned code do for a device whose limit ended up as zero?

## btrfs.zone-limit-usage: Validating against a derived limit

- section: Active zone limits
- relevance: 5 - a check added later must not reject file systems that were valid before
- words: 100

What usage of a zone limit that btrfs derived itself, from several device
limits or from a default, is unsafe when an existing file system is checked at
mount, and what that looks similar is correct? Name the in-tree code that
shows the correct form.

## btrfs.zone-activation: Zone activation and finish

- section: Active zone limits
- relevance: 4 - running out of active zones shows up as ENOSPC
- words: 110

When is the zone behind a block group activated and when is it finished, what
counts the active zones that are left, how many are held back for metadata and
system block groups and for whom, and in which order are the locks taken? Start
from `btrfs_zone_activate()` and `btrfs_zone_finish()`.

## btrfs.zone-append: Zone append writes

- section: Zoned writes
- relevance: 4 - the disk address of a write is not known until it completes
- words: 110

Which writes are sent as zone append and which are not, and once such a write
completes, how does the address the device chose reach the ordered extent, the
checksums and the extent map? What happens when one ordered extent ends up in
several places? Start from `btrfs_use_zone_append()`,
`btrfs_record_physical_zoned()` and `btrfs_finish_ordered_zoned()`.

## btrfs.zoned-meta-write: Metadata write order

- section: Zoned writes
- relevance: 3 - metadata is written with plain writes and must still be sequential
- words: 90

How does zoned mode keep tree block writes in order within a block group: what
is checked before an extent buffer is written, which lock serialises it, and
what happens to a buffer that is not at the write pointer? Start from
`btrfs_check_meta_write_pointer()` and `zoned_meta_io_lock`.

## btrfs.zoned-dedicated-bgs: Dedicated block groups

- section: Zoned writes
- relevance: 3 - allocations of different kinds must not share a zone
- words: 90

Which block groups does zoned mode set aside for the tree log and for data
relocation, how does the allocator keep other allocations out of them, and how
does space accounting tell them apart? Start from `treelog_bg`, `data_reloc_bg`
and `enum btrfs_space_info_sub_group`.

# Conventions and locks

## btrfs.trans-abort: Transaction abort

- section: Conventions
- relevance: 4 - the rule reviewers ask for most often
- words: 100

When must a transaction be aborted, where in the error path does the
maintainers' convention put the call, what must the error argument be, and what
does the caller still have to do with the handle afterwards? How does
`btrfs_abort_transaction()` differ from `btrfs_handle_fs_error()`?

## btrfs.assert: Assertions

- section: Conventions
- relevance: 3 - decides between an assert, a warning and an error return
- words: 90

Which forms does the `ASSERT()` macro in `fs/btrfs/messages.h` accept, what does
it do when it fails and when `CONFIG_BTRFS_ASSERT` is off, and when should code
return `-EUCLEAN` or warn instead of asserting?

## btrfs.path-and-search: Paths and search results

- section: Conventions
- relevance: 4 - a leaked path or a misread return value is the commonest small bug
- words: 110

How is a `struct btrfs_path` allocated and freed in new code, including the
scope-based forms, what does releasing one do, and what do the return values of
`btrfs_search_slot()` mean, including where the path points when the key was
not found? Start from `fs/btrfs/ctree.h`.

## btrfs.on-disk-format: On-disk format changes

- section: Conventions
- relevance: 4 - a new field without a check is a crash on a crafted image
- words: 100

Where are the on-disk structures defined, how must code read and write their
members, and which other places must a change that adds an item type or a field
touch so that a corrupted or crafted image is rejected and can be printed?
Start from `include/uapi/linux/btrfs_tree.h`, `fs/btrfs/accessors.h` and
`fs/btrfs/tree-checker.c`.

## btrfs.tree-locking: Tree block locks

- section: Locks and ordering
- relevance: 3 - lockdep catches most of it
- words: 90

What kind of lock protects an extent buffer, what are the nesting values
passed to `btrfs_tree_lock_nested()` for, what does the search code guarantee
about the order in which blocks are locked, and what is a `btrfs_drew_lock`?
Start from `fs/btrfs/locking.h`.

## btrfs.range-locking: File range locks

- section: Locks and ordering
- relevance: 4 - the order against folio locks and ordered extents is where deadlocks come from
- words: 110

What does `btrfs_lock_extent()` on an inode's `io_tree` protect, which bit does
direct I/O use instead, and in which order are the folio lock, the range lock
and the wait for ordered extents taken on the buffered read, buffered write and
writeback paths? Start from `fs/btrfs/extent-io-tree.h`.

## btrfs.inode-locks: Inode locks

- section: Locks and ordering
- relevance: 3 - each flag selects a different lock
- words: 80

Which locks does `btrfs_inode_lock()` take for each of its flags, what is
`i_mmap_lock` in `struct btrfs_inode` for, and in which order are they taken
with respect to each other and to a transaction?

## btrfs.ordered-lifecycle: Ordered extent life cycle

- section: Locks and ordering
- relevance: 4 - the file extent item and the extent map only become final here
- words: 110

What is the life of an ordered extent, from the function that allocates it to
the one that removes it: what does completion write into the trees, in which
order, what does it do to the extent map, and what happens on an I/O error or a
truncate? Start from `btrfs_alloc_ordered_extent()` and
`btrfs_finish_one_ordered()`.

## btrfs.subpage: Blocks and folios

- section: Locks and ordering
- relevance: 4 - folio flags alone are wrong when a folio holds several blocks
- words: 100

How does this tree track uptodate, dirty and writeback state when a folio holds
more than one file system block, which helpers must code use instead of the
folio flag functions, what is the structure attached to the folio called, and
what limits the size of a folio? Start from `fs/btrfs/subpage.h` and
`btrfs_is_subpage()`.

# Changing the implementation

## btrfs.change-checklist: Changing extent map code

- section: What a change must preserve
- relevance: 4 - the structure has users that a change to one path does not exercise
- words: 100

What must a change to `struct extent_map` or to the code in
`fs/btrfs/extent_map.c` keep working besides buffered reads and writes? List
the other code that reads or fills in the fields and say what each depends on.
Start from the callers of `btrfs_get_extent()`, `btrfs_create_io_em()` and
`btrfs_lookup_extent_mapping()`.
