# Questions: Btrfs Subsystem Details

- guide: btrfs.md
- title: Btrfs Subsystem Details

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/btrfs-measurement.md` is the
wider set the readers were measured on and `catalogue/btrfs-measurement-results.md` says what they
got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## btrfs.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Extent map fields and sizes

## btrfs.em-purpose: Extent map purpose

- section: Extent map fields and sizes
- relevance: 4 - nothing else about the structure makes sense without it

What does a `struct extent_map` stand for, and is the set an inode holds authoritative or a cache
that can be thrown away and reloaded? Does this tree use `struct extent_map` for anything other
than the file extents of an inode? Start from `fs/btrfs/extent_map.h`.

## btrfs.em-fields: Extent map member names

- section: Extent map fields and sizes
- relevance: 5 - a reader with the older members misreads every use of an extent map

Which members of `struct extent_map` hold the disk address of the extent, its size on disk, the
offset into it and its decompressed size? Which of those can differ from the on-disk file extent
item while the map is in the tree, and which function changes them? Start from
`fs/btrfs/extent_map.h`.

## btrfs.em-sentinels: Holes and inline extents

- section: Extent map fields and sizes
- relevance: 4 - a sentinel used as an address is an out-of-range I/O

How does an extent map say that a range is a hole or an inline extent? What are the requirements
for code that uses `disk_bytenr` of an extent map as a disk address in order to assure safe usage,
and which comparison tells a real extent from a hole or an inline extent? Start from
`EXTENT_MAP_LAST_BYTE` and `btrfs_extent_item_to_extent_map()`.

## btrfs.em-flags: Extent map flags

- section: Extent map fields and sizes
- relevance: 4 - several decide whether an extent map may be merged or dropped

Which bits in the `flags` of an extent map decide whether it may be merged, dropped from the tree
or logged, and which are set and never cleared? How is the compression type of an extent map
recorded and read back? Start from `EXTENT_FLAG_PINNED` in `fs/btrfs/extent_map.h`.

## btrfs.em-block-helpers: Disk address and length

- section: Extent map fields and sizes
- relevance: 5 - the wrong address or length reads or writes the wrong blocks

What do `btrfs_extent_map_block_start()` and `extent_map_block_len()` return for a compressed
extent, for an uncompressed one and for a hole? Which code can call each of them, and how does
code that cannot call one of them get the same value?

## btrfs.em-layouts: Compressed and partial layouts

- section: Extent map fields and sizes
- relevance: 5 - the fields only differ in the cases tests rarely cover

How do `len`, `disk_num_bytes`, `ram_bytes` and `offset` of an extent map
relate to each other for a plain uncompressed extent, for a compressed extent,
and for an extent map that refers to part of a larger extent after a clone or
an overwrite of its neighbours? In which of these cases are the three sizes
equal?

## btrfs.em-invariants: Extent map invariants

- section: Extent map fields and sizes
- relevance: 5 - says which combinations of the fields are legal

What does the tree check about an extent map's fields before it goes into an
inode's tree, for a real extent and for a hole or inline one, what happens when
a check fails, and in which configurations does the check run at all? Start
from `validate_extent_map()`.

## btrfs.em-field-usage: Choosing a size field

- section: Extent map fields and sizes
- relevance: 5 - a recurring bug class that simple tests do not show

Which member of `struct extent_map` gives the file range it covers, which gives the number of
bytes to read from or write to disk, and which gives the size of a buffer that holds the
decompressed extent? Name in-tree code that shows each, for example in `fs/btrfs/compression.c`,
`fs/btrfs/tree-log.c` or `btrfs_encoded_read()`.

## btrfs.chunk-maps: Chunk mapping structure

- section: Extent map fields and sizes
- relevance: 4 - decides whether extent map code is shared with the volume layer

Which structure maps a logical chunk to its device stripes, and where are the instances kept? Does
the code that uses it use `struct extent_map` or a function from `fs/btrfs/extent_map.c`? Start
from `fs/btrfs/volumes.h`.

# The extent map tree

## btrfs.em-api: Extent map function names

- section: The extent map tree
- relevance: 4 - the names have changed and a reader's memory offers old ones

Which prefix do the functions declared in `fs/btrfs/extent_map.h` carry, and which of them do not
carry it? What decides whether one of them takes the inode or the `struct extent_map_tree`? Start
from `fs/btrfs/extent_map.h`.

## btrfs.em-locking: Extent map tree locking

- section: The extent map tree
- relevance: 5 - says what may be read or changed under which lock

Which lock protects the extent map tree of an inode, and which of the functions declared in
`fs/btrfs/extent_map.h` take it themselves and which require the caller to hold it, and in which
mode? What are the locking requirements for a caller of `btrfs_drop_extent_map_range()` or
`btrfs_replace_extent_map_range()` in order to assure safe usage? Start from `struct
extent_map_tree` and `btrfs_drop_extent_map_range()`.

## btrfs.em-refcount: Extent map references

- section: The extent map tree
- relevance: 4 - a missing put leaks, an extra one frees a tree entry

What does `btrfs_lookup_extent_mapping()` do to the reference count of the extent map it returns,
and what does `btrfs_remove_extent_mapping()` do to the count? When may code change in place the
members of an extent map that is in the tree?

## btrfs.em-lookup-result: Lookup and insert results

- section: The extent map tree
- relevance: 4 - the entry handed back need not be the one asked for

What may `btrfs_lookup_extent_mapping()` and `btrfs_search_extent_mapping()`
return relative to the range asked for, and what does
`btrfs_add_extent_mapping()` do, and leave in its argument, when the range
collides with an entry already in the tree? What must the caller check
afterwards?

## btrfs.em-creation: Creating extent maps

- section: The extent map tree
- relevance: 4 - each path fills the fields in its own way

Which function turns a file extent item into an extent map, and what does it store in `ram_bytes`
for an uncompressed extent? Which members must a path that builds an extent map without that
function set itself? Name in-tree code that shows it. Start from `btrfs_get_extent()`.

## btrfs.em-merging: Merging extent maps

- section: The extent map tree
- relevance: 4 - after a merge the fields no longer match one on-disk item

When are two adjacent extent maps merged into one, which extent maps are never
merged, and what do `disk_bytenr`, `disk_num_bytes`, `offset`, `ram_bytes` and
`generation` hold afterwards? Start from `try_merge_map()` and
`mergeable_maps()`.

## btrfs.em-drop-range: Dropping a range

- section: The extent map tree
- relevance: 4 - the split halves must keep the fields consistent

When `btrfs_drop_extent_map_range()` cuts an extent map that straddles the range, how does it
compute the members of the remaining pieces, for a real extent and for a hole, and what does it do
when it cannot allocate the pieces? What does `btrfs_split_extent_map()` require of the extent map
it splits?

## btrfs.em-pinned-logging: Pinned and modified extent maps

- section: The extent map tree
- relevance: 4 - dropping the wrong one loses data at the next fsync

When is an extent map that was created for a write pinned, and when is it unpinned? What is the
`modified_extents` list of `struct extent_map_tree` for? What are the requirements for code that
removes an extent map from that list while the file keeps the range, so that a later fsync logs
the range? Start from `btrfs_unpin_extent_cache()` and `btrfs_set_inode_full_sync()`.

## btrfs.em-shrinker: Reclaiming extent maps

- section: The extent map tree
- relevance: 4 - every reader had reclaim skip more extent maps than it does

Which extent maps do `btrfs_scan_inode()` and `try_release_extent_mapping()` each skip, and what
does each do with an extent map that is on the `modified_extents` list? Which locks does each hold
while it removes an extent map? Start from `btrfs_scan_inode()` and
`try_release_extent_mapping()`.

## btrfs.change-checklist: Other extent map users

- section: The extent map tree
- relevance: 4 - the structure has users that a change to one path does not exercise

Which code other than buffered reads and writes reads the members of a `struct extent_map`, and
what does each require of those members? Do fiemap, seeking for data and holes, and swap file
activation read extent maps or the file extent items? Start from the callers of
`btrfs_get_extent()`, `btrfs_create_io_em()` and `btrfs_lookup_extent_mapping()`.

# Ordered extents, range locks and subpage

## btrfs.em-write-target: Extent maps for new writes

- section: Ordered extents, range locks and subpage
- relevance: 4 - the asserts here state the rules for each kind of write

What structure describes the extent a write is going to create, and what does
`btrfs_create_io_em()` require of its values for an ordinary copy-on-write
write, for a compressed write and for a write into a preallocated extent? What
does it do about a write that overwrites an existing extent in place?

## btrfs.ordered-extent-fields: Ordered extent sizes and type

- section: Ordered extents, range locks and subpage
- relevance: 4 - the same names as the extent map, with their own rules

Which members of `struct btrfs_ordered_extent` have the same name as a member of `struct
extent_map` or of the on-disk file extent item, and for which of them does the meaning differ? How
does an ordered extent say what type of write it is, and how many of the type bits may be set at
once? Start from `struct btrfs_ordered_extent` in `fs/btrfs/ordered-data.h`.

## btrfs.ordered-lifecycle: Ordered extent completion

- section: Ordered extents, range locks and subpage
- relevance: 4 - the file extent item and the extent map only become final here

When an ordered extent completes, what is written into the trees and in which
order, what happens to the extent map, and what is done instead after an I/O
error or a truncate that cut it short? Start from
`btrfs_alloc_ordered_extent()` and `btrfs_finish_one_ordered()`.

## btrfs.range-locking: File range locks

- section: Ordered extents, range locks and subpage
- relevance: 4 - the order against folio locks and ordered extents is where deadlocks come from

What does `btrfs_lock_extent()` on an inode's `io_tree` protect, what does
direct I/O take, in place of it or as well, and in which order are the folio
lock, the range lock and the wait for ordered extents taken on the buffered
read, buffered write and writeback paths? Start from
`fs/btrfs/extent-io-tree.h`.

## btrfs.subpage: Subpage and per-block state

- section: Ordered extents, range locks and subpage
- relevance: 4 - folio flags alone are wrong when a folio holds several blocks

What are the requirements for code that sets, clears or tests a state flag of a folio that holds
more than one file system block, in order to assure safe usage? Which structure attached to the
folio keeps the state of each block? When does `btrfs_is_subpage()` return true? Start from
`fs/btrfs/subpage.h`.

# Zoned mode

## btrfs.zoned-overview: Zoned file systems

- section: Zoned mode
- relevance: 4 - everything else about zones rests on it

What decides that a file system is zoned, and how is a device that is not zoned handled inside a
zoned file system? Which conditions make `btrfs_check_zoned_mode()` or `btrfs_get_dev_zone_info()`
fail the mount? Start from `btrfs_is_zoned()`, `btrfs_check_zoned_mode()` and `fs/btrfs/zoned.c`.

## btrfs.zone-append: Zone append writes

- section: Zoned mode
- relevance: 4 - the disk address of a write is not known until it completes

Which writes are sent as zone append and which are not, and once such a write completes, how does
the address the device chose reach the ordered extent, the checksums and the extent map? What does
`btrfs_finish_ordered_zoned()` do when the parts of one ordered extent were written to addresses
that do not follow one another? Start from `btrfs_use_zone_append()`,
`btrfs_record_physical_zoned()` and `btrfs_finish_ordered_zoned()`.

# Active zone limits

## btrfs.active-vs-open: Active and open zones

- section: Active zone limits
- relevance: 4 - the two limits mean different things and either may be absent

Which zone conditions does btrfs count as active when it reads a device's
zones, what do `bdev_max_active_zones()` and `bdev_max_open_zones()` return for
a device that has no such limit, and may a device report one limit without the
other?

## btrfs.max-active-zones: Active zone limit computation

- section: Active zone limits
- relevance: 5 - the number every activation decision is made against

How does btrfs compute the limit on active zones that it enforces for a device from the limits
that the block device reports, and what does it use when the device reports none? Which bounds
does it apply to the result? Name the function, and give each constant it uses by its full name.
Start from `btrfs_get_dev_zone_info()`.

## btrfs.active-limit-check: Exceeding the limit at mount

- section: Active zone limits
- relevance: 5 - the difference between a warning and a file system that no longer mounts

When a device holds more active zones at mount than the limit btrfs computed, in which case does
`btrfs_get_dev_zone_info()` fail the mount and in which case does it go on? How does the rest of
`fs/btrfs/zoned.c` treat a device whose `max_active_zones` is zero? What are the requirements for
a check that compares the active zones of an existing file system with a limit that btrfs computed
and the device did not report, in order to assure safe usage?

## btrfs.zone-activation: Zone activation and finish

- section: Active zone limits
- relevance: 4 - running out of active zones shows up as ENOSPC

When does btrfs activate the zone behind a data block group, and when the zone behind a metadata
or system block group? Does btrfs keep active zones in reserve for metadata and system block
groups? In which order does `btrfs_zone_activate()` take its locks? Start from
`btrfs_zone_activate()` and `btrfs_zone_finish()`.

# Transactions, paths and on-disk items

## btrfs.trans-abort: Transaction abort

- section: Transactions, paths and on-disk items
- relevance: 4 - the rule reviewers ask for most often

Where in an error path does the tree say to put the call to `btrfs_abort_transaction()`, relative
to the call that failed? What must the caller still do with the transaction handle afterwards?
When does code call `btrfs_handle_fs_error()` and not `btrfs_abort_transaction()`? Start from the
comment above `btrfs_abort_transaction()` in `fs/btrfs/transaction.h`.

## btrfs.path-and-search: Paths and search results

- section: Transactions, paths and on-disk items
- relevance: 4 - a leaked path or a misread return value is the commonest small bug

How does new code allocate and free a `struct btrfs_path`, and what does `btrfs_release_path()` do
that `btrfs_free_path()` does not? What does `btrfs_search_slot()` return when it finds the key,
when it does not find it, and on an error? Start from `fs/btrfs/ctree.h`.

## btrfs.search-slot-position: Path position after a search

- section: Transactions, paths and on-disk items
- relevance: 4 - the caller reads the item at the slot the search left behind

Where does `btrfs_search_slot()` leave the path when it does not find the key, and what must the
caller check before it reads the item at that slot? Start from `btrfs_search_slot()` in
`fs/btrfs/ctree.c`.

## btrfs.on-disk-format: On-disk format changes

- section: Transactions, paths and on-disk items
- relevance: 4 - a new field without a check is a crash on a crafted image

What are the requirements for code that reads or writes a member of an on-disk structure in an
extent buffer, in order to assure safe usage? Which files must a change that adds an item type or
a member also change, so that the tree checker rejects a corrupted or crafted image and the leaf
printer can print it? Start from `include/uapi/linux/btrfs_tree.h`, `fs/btrfs/accessors.h` and
`fs/btrfs/tree-checker.c`.

# Model gaps

## btrfs.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.
