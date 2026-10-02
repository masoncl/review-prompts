# Questions: DAX

- guide: dax.md
- title: DAX Subsystem Details

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/dax-measurement.md` is the wider
set the readers were measured on and `catalogue/dax-measurement-results.md` says what they got
wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## dax.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## dax.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to file: the filesystem DAX fault, read/write, writeback and
truncate helpers; the `struct dax_device` core; the DAX bus with its regions and sysfs
attributes; the character device driver; the driver that hands a range to the page allocator;
any other driver that binds to a device on the DAX bus; the glue that creates DAX regions for
persistent memory, CXL and firmware-reserved memory; the public and the private headers; the
tracepoints; the documentation; the test build that shares these sources. Start from
`fs/dax.c`, `drivers/dax/` and `tools/testing/nvdimm/`.

## dax.flavours: Kinds of DAX

- section: Finding your way
- relevance: 4 - rules for one kind are wrong for another

Which kinds of DAX does this tree have, which value of `enum memory_type` does the `dev_pagemap`
of each kind use, and how does code tell the kinds apart given a VMA, an inode or a folio? Answer
as a table. Start from `vma_is_fsdax()`, `enum dax_driver_type` and `enum memory_type`.

# Page cache entries

## dax.entry-encoding: Entry encoding

- section: Page cache entries
- relevance: 5 - every function in the file reads these bits

What does filesystem DAX store in a file's `i_pages` xarray: what is in the value of an entry,
which kinds of entry do its flag bits tell apart, and which state that a reader may expect in
the entry is kept as an xarray mark instead? Start from `dax_make_entry()` in `fs/dax.c`.

## dax.entry-locking: Entry locking

- section: Page cache entries
- relevance: 5 - the entry lock is what serialises faults, writeback and truncate

Which lock must the caller hold for each of `get_next_unlocked_entry()`,
`wait_entry_unlocked_exclusive()`, `put_unlocked_entry()`, `dax_lock_entry()` and
`dax_unlock_entry()`, and which of them drop it inside? How does `dax_entry_waitqueue()` find the
wait queue for an entry that is PMD sized, and which of the values of `enum dax_wake_mode` is used
when?

## dax.entry-lock-usage: Entry unlock and wake rules

- section: Page cache entries
- relevance: 5 - a missed wakeup or a stale xa_state hangs or corrupts, and no diff shows it

What are the requirements for an entry returned by `get_next_unlocked_entry()` or
`grab_mapping_entry()` in `fs/dax.c` in order to assure safe usage? What does the code require of
an `xa_state` that is used again after the `i_pages` lock was dropped? Name in-tree code that
shows each.

## dax.order-conflicts: PMD and PTE entry conflicts

- section: Page cache entries
- relevance: 4 - decides when a huge fault falls back

What happens when a fault of one size finds an entry of the other size at that index: a PTE
fault that finds a PMD entry of each kind, and a PMD fault that finds PTE entries in its range?
How does `grab_mapping_entry()` report an error or a fallback to its caller? Start from
`dax_is_conflict()`.

## dax.change-checklist: Entry invariants and their checks

- section: Page cache entries
- relevance: 4 - the invariants live in comments, not asserts

What do `dax_insert_entry()`, `dax_disassociate_entry()` and `__dax_invalidate_entry()` require to
stay true when an entry is inserted, replaced or removed? Which of these requirements does a
`WARN_ON_ONCE` in `fs/dax.c` check, and which does nothing check? Give the names of the marks and
wake modes in full.

# Faults

## dax.fault-entry-points: Fault entry points

- section: Faults
- relevance: 5 - the locking is the filesystem's job and nothing asserts it

What does `dax_iomap_fault()` require its caller to hold or to have checked, and from which of its
`vm_operations_struct` handlers does a filesystem call it? In one line, in what order does
`dax_iomap_pte_fault()` do its steps between taking the entry and releasing it? Use one in-tree
filesystem as the example.

## dax.vma-flags: VMA flags and insert helpers

- section: Faults
- relevance: 4 - the documentation describes a different scheme

Which VMA flags does a filesystem set on a DAX file mapping in this tree, and with which
functions does `fs/dax.c` put a pfn into a PTE or a PMD? Does `dax_fault_iter()` take a
reference around the insertion, and which? Give the flag names in full. Say if
`Documentation/filesystems/dax.rst` describes something else.

## dax.pmd-fallback: Huge fault fallback

- section: Faults
- relevance: 4 - each condition has been a bug

Under which conditions does a PMD-sized fault on a DAX file fall back and where is each tested,
what does the fallback path do to the page table before it returns, and which fault orders does
`dax_iomap_fault()` accept at all? Start from `dax_fault_check_fallback()`.

## dax.sync-faults: Synchronous faults

- section: Faults
- relevance: 4 - the durability promise of MAP_SYNC rests on this

What decides that a write fault on a `MAP_SYNC` mapping is synchronous, what does
`dax_iomap_fault()` then return and leave undone, and what must the filesystem call to finish
it? Which check refuses a `MAP_SYNC` mapping at mmap time? Start from
`dax_fault_is_synchronous()` and `daxdev_mapping_supported()`.

## dax.holes-and-cow: Holes, COW and shared extents

- section: Faults
- relevance: 4 - three cases that look alike and are handled differently

How does the fault path handle a read of a hole, a write fault on a private mapping that has a
`cow_page`, and a write to an extent the filesystem reports with `IOMAP_F_SHARED`? Say which
entry kind and which xarray marks each leaves behind. Start from `dax_load_hole()`,
`dax_fault_cow_page()` and `dax_iomap_copy_around()`.

# Page references and breaking layouts

## dax.page-refcount: Idle and busy pages

- section: Page references and breaking layouts
- relevance: 5 - the idle count changed, and every truncate decision rests on it

What reference count does an idle page of filesystem DAX memory have in this tree, and an idle
page of a device DAX device? How does `fs/dax.c` decide that a page is still in use by someone
other than page tables, and what happens, and who is woken, when the last reference is dropped?
Start from `dax_page_is_idle()`, `dax_busy_page()` and `free_zone_device_folio()`.

## dax.folio-association: Folio association and sharing

- section: Page references and breaking layouts
- relevance: 4 - fs/dax.c builds and tears down compound folios by hand

What do `dax_associate_entry()` and `dax_disassociate_entry()` write into the folio behind an
entry? When is a folio shared between files, and who then finds the owners? Start from
`dax_associate_entry()` and `dax_folio_put()`.

## dax.break-layout: Breaking layouts

- section: Page references and breaking layouts
- relevance: 5 - freeing blocks under a page that DMA still targets corrupts data

What has `dax_break_layout()` done to the file's entries by the time it returns, what is its
callback for, and what does it do when its caller passes no callback? Which function does a
filesystem call at inode eviction instead? Start from `dax_break_layout()` and
`dax_layout_busy_page_range()`.

## dax.block-freeing: Freeing and remapping blocks

- section: Page references and breaking layouts
- relevance: 5 - blocks freed under a page that DMA still targets corrupt data

Before which operations on the blocks of a DAX file does a filesystem have to call
`dax_break_layout()`, and which locks does it have to hold when it calls it? Name in-tree code
that shows it.

## dax.truncate-usage: Truncate and invalidate usage

- section: Page references and breaking layouts
- relevance: 4 - the generic truncate code only warns

What are the requirements for calling `truncate_inode_pages_range()` or
`invalidate_inode_pages2_range()` on a DAX mapping in order to assure safe usage? Which of
`dax_delete_mapping_entry()` and `dax_invalidate_mapping_entry_sync()` does each reach, and what
does that function do with a dirty entry? Start from `truncate_folio_batch_exceptionals()`.

# Reads, writes and writeback

## dax.read-write-path: Read and write path

- section: Reads, writes and writeback
- relevance: 4 - the asserts and the error translation are easy to miss

What does `dax_iomap_rw()` require of its caller, and which of those requirements does it assert?
Which iomap types does `dax_iomap_iter()` accept for a write, and what does it do when
`dax_direct_access()` reports a poisoned range or another error? Start from `dax_mem2blk_err()`
and `enum dax_access_mode`.

## dax.write-invalidation: Invalidation before a write

- section: Reads, writes and writeback
- relevance: 4 - a missing invalidation leaves a mapping with stale data after a write

When does `dax_iomap_iter()` invalidate the entries of the range it writes before it copies the
data, and which function does it call to do so?

## dax.writeback: Dirty tracking and writeback

- section: Reads, writes and writeback
- relevance: 4 - the order of the steps is the correctness argument

How is a DAX entry marked dirty, and what does `dax_writeback_one()` do, in order, to make the
data durable and clean the entry? For which requests does `dax_writeback_mapping_range()` return
without writing anything? Give the names of the xarray marks in full.

## dax.flush-conditions: Cache flush conditions

- section: Reads, writes and writeback
- relevance: 4 - writeback relies on the flush to make data durable

When does `dax_flush()` return without flushing anything? Give the names of the device flags in
full.

# The dax_device core

## dax.device-lifetime: Device lifetime

- section: The dax_device core
- relevance: 5 - a driver can go away under a mounted filesystem

What do `run_dax()` and `kill_dax()` change in a `struct dax_device`? What are the requirements
for calling `dax_alive()`, and for using an address returned by `dax_direct_access()`, in order to
assure safe usage? Start from `dax_read_lock()` in `drivers/dax/super.c`.

## dax.device-references: Allocation and references

- section: The dax_device core
- relevance: 5 - a driver can go away under a mounted filesystem

How is a `struct dax_device` referenced and freed, and in what state does `alloc_dax()` return it?

## dax.holder: Holders and failure notification

- section: The dax_device core
- relevance: 4 - the ordering in release is deliberate

What do `fs_dax_get_by_bdev()` and `fs_dax_get()` require of the holder and the holder operations
passed to them, and what must a caller of `fs_put_dax()` pass? By what path does a memory failure
on a DAX page reach the `notify_failure` operation of `struct dax_holder_operations`? Start from
`struct dax_holder_operations`.

## dax.holder-release: Holder release order

- section: The dax_device core
- relevance: 4 - the ordering in release is deliberate

In what order does `fs_put_dax()` clear the holder and the holder operations of a `struct
dax_device`, and what does `kill_dax()` tell the holder?

## dax.operations: Device operations

- section: The dax_device core
- relevance: 4 - the return conventions differ per call

What do `dax_direct_access()`, `dax_zero_page_range()`, `dax_copy_from_iter()` and
`dax_recovery_write()` return when the device is dead, has no operation for the call, or the
request cannot be met, and which operations of `struct dax_operations` may a driver leave out?
Which device flags change how the copy helpers copy, and which way does each change it?

# The DAX bus and its drivers

## dax.bus-model: Regions and devices

- section: The DAX bus and its drivers
- relevance: 4 - the objects and the two locks are tree specific

How do a static and a dynamic `struct dax_region` differ, and who owns the `dev_pagemap` of a
`struct dev_dax` in each case? Which locks protect region and device configuration, and in which
order are they taken? Start from `drivers/dax/bus.c`.

## dax.device-mmap: Character device mappings

- section: The DAX bus and its drivers
- relevance: 4 - the checks run again on every fault

What does the device DAX character device require of a mapping and where is that checked, and
what does each fault size return when the device's alignment is larger, equal or smaller than
the fault? What does the fault path write into the folios it maps? Start from `check_vma()` and
`dev_dax_huge_fault()`.

## dax.kmem: Memory hotplug driver

- section: The DAX bus and its drivers
- relevance: 4 - the unbind path cannot fail and may not block

How does `dev_dax_kmem_probe()` add the ranges of a `dev_dax` as system memory, and who decides
whether the blocks come online? What does `dev_dax_kmem_remove()` do with a range whose memory is
still online? Start from `dev_dax_kmem_probe()`.

## dax.fsdev: Filesystem-facing driver

- section: The DAX bus and its drivers
- relevance: 4 - new, and easy to confuse with the character device driver

Does this tree have a DAX bus driver that lets a filesystem use a `dev_dax` without a block
device? If so, how does it differ from the driver in `drivers/dax/device.c`, and how does it come
to be bound to a device? If there is none, say so and stop.

# Model gaps

## dax.model-gaps: Other mistakes models make

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
