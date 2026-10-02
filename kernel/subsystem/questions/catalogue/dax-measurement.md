# Questions: DAX (measurement set)

- guide: dax.md
- title: DAX Subsystem Details

A wide set of questions about DAX: filesystem DAX in `fs/dax.c` (the entries
it keeps in the page cache xarray, how they are locked, the fault, read/write,
writeback and truncate paths, and the page reference rules), the `dax_device`
core in `drivers/dax/super.c`, and device DAX under `drivers/dax/` (the bus,
the character device, kmem and the other drivers). It is used to measure what
a model already knows before deciding what the built guide should spend its
words on. The hand-written guide it will replace is 108 words of headings
with no names in it. Page tables and folios in general have their own guides;
these questions stay on what is specific to DAX. Format:
`../../../docs/subsystem-questions.md`.

# Finding your way

## dax.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

Which files hold each of these: the filesystem DAX fault, read/write,
writeback and truncate helpers; the `struct dax_device` core; the DAX bus with
its regions and sysfs attributes; the character device driver; the driver that
hands a range to the page allocator; any other driver that binds to a device
on the DAX bus; the glue that creates DAX regions for persistent memory, CXL
and firmware-reserved memory; the public and the private headers; the
tracepoints; the documentation; and the test build that shares these sources?
A table. Start from `fs/dax.c`, `drivers/dax/` and `tools/testing/nvdimm/`.

## dax.flavours: Kinds of DAX

- section: Finding your way
- relevance: 4 - rules for one kind are wrong for another
- words: 90

Which kinds of DAX does this tree have (file mappings from a filesystem, a
character device, memory handed to the page allocator, anything else), which
`dev_pagemap` memory type does each use, and how does code tell them apart
given a VMA, an inode or a folio? Start from `vma_is_fsdax()`,
`enum dax_driver_type` and `enum memory_type`.

## dax.filesystems: Filesystems and providers

- section: Finding your way
- relevance: 3 - the documentation's list is one input, the code is another
- words: 80

Which filesystems in this tree call `dax_iomap_rw()` or `dax_iomap_fault()`,
and which drivers call `alloc_dax()` with a `struct dax_operations`? Say
where `Documentation/filesystems/dax.rst` disagrees with the code, if it does.

# Entries in the page cache

## dax.entry-encoding: Entry encoding

- section: Page cache entries
- relevance: 5 - every function in the file reads these bits
- words: 90

What does filesystem DAX store in a file's `i_pages` xarray: how is an entry
encoded, which flag bits are there, which kinds of entry do the bits
distinguish, and which helpers read them? Start from `dax_make_entry()` in
`fs/dax.c`.

## dax.entry-locking: Entry locking

- section: Page cache entries
- relevance: 5 - the entry lock is what serialises faults, writeback and truncate
- words: 110

How is one DAX entry locked, waited for and unlocked? Name the functions, say
which lock must be held when each is called and whether it is dropped inside,
how a waiter finds its wait queue when the entry is PMD sized, and what
`enum dax_wake_mode` chooses between.

## dax.entry-lock-usage: Entry lock usage

- section: Page cache entries
- relevance: 5 - a missed wakeup or a stale xa_state hangs or corrupts, and no diff shows it
- words: 100

In `fs/dax.c`, what usage of an entry returned by `get_next_unlocked_entry()`
or `grab_mapping_entry()` is unsafe, and what that looks similar is correct?
Cover what must follow each of them on every path, what has to happen to the
`xa_state` after the `i_pages` lock was dropped, and which wake mode goes with
removing an entry. Name in-tree code that shows each.

## dax.order-conflicts: PMD and PTE entries

- section: Page cache entries
- relevance: 4 - decides when a huge fault falls back
- words: 90

What happens when a fault of one size finds an entry of the other size at
that index: a PTE fault that finds a PMD entry of each kind, and a PMD fault
that finds PTE entries in its range? How does `grab_mapping_entry()` report an
error or a fallback to its caller? Start from `dax_is_conflict()`.

## dax.nrpages-accounting: Entry accounting

- section: Page cache entries
- relevance: 3 - generic page cache code depends on it
- words: 70

Who keeps `mapping->nrpages` right for a DAX mapping, and which code outside
`fs/dax.c` has to recognise a DAX entry when it meets one in `i_pages`? Start
from `dax_mapping()` and `mm/truncate.c`.

# Faults and I/O

## dax.fault-entry-points: Fault entry points

- section: Faults
- relevance: 5 - the locking is the filesystem's job and nothing asserts it
- words: 100

Which function does a filesystem call to handle a fault on a DAX file, from
which `vm_operations_struct` handlers, and what must the filesystem already
hold or have checked when it calls? What does `dax_iomap_pte_fault()` do, in
order, between taking the entry and releasing it? Use one in-tree filesystem
as the example.

## dax.vma-flags: Mapping flags and page table insertion

- section: Faults
- relevance: 4 - the documentation describes a different scheme
- words: 90

Which VMA flags does a filesystem set on a DAX file mapping in this tree, and
with which functions does `fs/dax.c` put a pfn into a PTE or a PMD? Does
`dax_fault_iter()` take a reference around the insertion, and which? Give the
flag names in full. Say if `Documentation/filesystems/dax.rst` describes
something else.

## dax.pmd-fallback: Huge fault fallback

- section: Faults
- relevance: 4 - each condition has been a bug
- words: 90

List the conditions under which a PMD-sized fault on a DAX file falls back,
where each is tested, what the fallback path does to the page table, and which
fault orders `dax_iomap_fault()` accepts at all. Start from
`dax_fault_check_fallback()`.

## dax.sync-faults: Synchronous faults

- section: Faults
- relevance: 4 - the durability promise of MAP_SYNC rests on this
- words: 90

How does a write fault on a `MAP_SYNC` mapping differ from an ordinary one:
what decides that a fault is synchronous, what does `dax_iomap_fault()` return
and leave undone, and what must the filesystem then call? Which check refuses
a `MAP_SYNC` mapping at mmap time? Start from `dax_fault_is_synchronous()`
and `daxdev_mapping_supported()`.

## dax.holes-and-cow: Holes, private COW and shared extents

- section: Faults
- relevance: 4 - three cases that look alike and are handled differently
- words: 100

How does the fault path handle a read of a hole, a write fault on a private
mapping that has a `cow_page`, and a write to an extent the filesystem reports
with `IOMAP_F_SHARED`? Say which entry kind and which xarray marks each
leaves behind. Start from `dax_load_hole()`, `dax_fault_cow_page()` and
`dax_iomap_copy_around()`.

## dax.read-write-path: Read and write path

- section: I/O and writeback
- relevance: 4 - the asserts and the error translation are easy to miss
- words: 100

What does `dax_iomap_rw()` require of its caller and assert, which iomap
types does `dax_iomap_iter()` accept for a write, when does it invalidate
entries before copying, how does it deal with a poisoned range, and how are
errors from the device translated for the caller? Start from
`dax_mem2blk_err()` and `enum dax_access_mode`.

## dax.writeback: Dirty tracking and writeback

- section: I/O and writeback
- relevance: 4 - the order of the steps is the correctness argument
- words: 100

How is a DAX entry marked dirty, and what does `dax_writeback_one()` do, in
order, to make the data durable and clean the entry? Which calls does
`dax_writeback_mapping_range()` ignore? When does `dax_flush()` do nothing?
Give the names of the xarray marks and the device flags in full.

# Page references and truncate

## dax.page-refcount: Idle and busy pages

- section: Page references
- relevance: 5 - the idle count changed, and every truncate decision rests on it
- words: 90

What reference count does an idle page of filesystem DAX memory have in this
tree, and an idle page of a device DAX device? How does `fs/dax.c` decide that
a page is still in use by someone other than page tables, what happens when
the last reference is dropped, and who is woken? Start from
`dax_page_is_idle()`, `dax_busy_page()` and `free_zone_device_folio()`.

## dax.folio-association: Folio state

- section: Page references
- relevance: 4 - fs/dax.c builds and tears down compound folios by hand
- words: 100

What does `fs/dax.c` write into the folio behind an entry when the entry is
inserted and when it is removed: `mapping`, `index`, `share`, the order? When
is a folio shared between files, what does that do to `folio->mapping`, and
who then finds the owners? Start from `dax_associate_entry()` and
`dax_folio_put()`.

## dax.break-layout: Breaking layouts

- section: Page references
- relevance: 5 - freeing blocks under a page that DMA still targets corrupts data
- words: 110

What must a filesystem call before it frees or remaps the blocks of a DAX file
in truncate, hole punch or reflink, what does that call do in order, what is
the callback for, and what does passing no callback mean? What is called at
inode eviction instead? Start from `dax_break_layout()` and
`dax_layout_busy_page_range()`.

## dax.truncate-usage: Truncate and invalidate usage

- section: Page references
- relevance: 4 - the generic truncate code only warns
- words: 90

What usage of `truncate_inode_pages_range()` or
`invalidate_inode_pages2_range()` on a DAX mapping is unsafe, and what that
looks similar is correct? Say which of `dax_delete_mapping_entry()` and
`dax_invalidate_mapping_entry_sync()` each reaches, and what each does with a
dirty entry. Start from `truncate_folio_batch_exceptionals()`.

# The dax_device

## dax.device-lifetime: Device lifetime

- section: The dax_device core
- relevance: 5 - a driver can go away under a mounted filesystem
- words: 100

What is a `struct dax_device`, how is it allocated, referenced and freed, and
what do `run_dax()` and `kill_dax()` change? What usage of `dax_alive()` or of
an address returned by `dax_direct_access()` is unsafe, and what is correct?
Start from `dax_read_lock()` in `drivers/dax/super.c`.

## dax.operations: Device operations

- section: The dax_device core
- relevance: 4 - the return conventions differ per call
- words: 90

Which callbacks does `struct dax_operations` have, which are mandatory, and
what do `dax_direct_access()`, `dax_zero_page_range()`,
`dax_copy_from_iter()` and `dax_recovery_write()` return when the device is
dead, has no operations, or the request cannot be met? Which device flags
change how the copy helpers copy?

## dax.holder: Holders and failure notification

- section: The dax_device core
- relevance: 4 - the ordering in release is deliberate
- words: 100

How does a filesystem or device mapper claim a `dax_device`, with which
functions, and what makes the claim exclusive? By what path does a memory
failure on a DAX page reach the holder, and what does `kill_dax()` tell it?
What must a caller of `fs_put_dax()` pass? Start from
`struct dax_holder_operations`.

## dax.memory-failure: Memory failure locking

- section: The dax_device core
- relevance: 3 - the cookie has two special values
- words: 80

How does `mm/memory-failure.c` pin down a DAX page's owner without the folio
lock? What do `dax_lock_folio()` and `dax_lock_mapping_entry()` return in each
case (locked, nothing to lock, failure), and what is different for a device
DAX folio?

# Device DAX

## dax.bus-model: Regions and devices

- section: The DAX bus
- relevance: 4 - the objects and the two locks are tree specific
- words: 110

What are `struct dax_region`, `struct dev_dax`, `struct dev_dax_range` and
`struct dax_mapping`, how do a static and a dynamic region differ, and who
owns the `dev_pagemap` in each case? Which locks protect region and device
configuration, in which order are they taken, and which sysfs attributes take
them? Start from `drivers/dax/bus.c`.

## dax.driver-binding: Driver binding

- section: The DAX bus
- relevance: 3 - explains why a device ends up with one driver and not another
- words: 80

How does the DAX bus choose a driver for a `dev_dax`: the driver types, the
resource flag that steers a region to one of them, and the sysfs files that
override the choice? In what state is the `dax_device` while no driver is
bound? Start from `dax_bus_match()`.

## dax.device-mmap: Character device mappings

- section: Device DAX drivers
- relevance: 4 - the checks run again on every fault
- words: 100

What does the device DAX character device require of a mapping, where is that
checked, and what does each fault size return when the device's alignment is
larger, equal or smaller than the fault? What does the fault path write into
the folios it maps? Start from `check_vma()` and `dev_dax_huge_fault()`.

## dax.kmem: Memory hotplug driver

- section: Device DAX drivers
- relevance: 4 - the unbind path cannot fail and may not block
- words: 110

How does the kmem driver add a `dev_dax`'s ranges as system memory: which
hotplug call, which flags, who decides whether the blocks come online? Does
the driver offer a way to change that state after probe, and what are its
rules? What happens at unbind when memory is still online, and what is leaked
on purpose? Give flag and constant names in full. Start from
`dev_dax_kmem_probe()`.

## dax.fsdev: Filesystem-facing driver

- section: Device DAX drivers
- relevance: 3 - new, and easy to confuse with the character device driver
- words: 90

Does this tree have a DAX bus driver that lets a filesystem use a `dev_dax`
without a block device? If so, how does it differ from `drivers/dax/device.c`
in memory type, folio setup and user mappings, how does it supply
`dax_operations`, and which function does a filesystem call to claim the
device? If there is none, say so and stop.

# Changing the implementation

## dax.change-checklist: Changing entry handling

- section: What a change must preserve
- relevance: 4 - the invariants live in comments, not asserts
- words: 100

Someone changes how `fs/dax.c` inserts, replaces or removes an entry. What
must still hold afterwards: between the entry and the folio behind it, between
the entry and the page tables that map it, for the dirty and towrite marks,
and for tasks waiting on the entry? Which `WARN_ON_ONCE` checks in the file
guard each? Give the names of the marks and wake modes in full.

## dax.test-build: Shared test build

- section: What a change must preserve
- relevance: 2 - a rename in drivers/dax breaks an out-of-the-way build
- words: 60

Which sources under `drivers/dax/` are also compiled by
`tools/testing/nvdimm/`, and which function there is declared weak so that the
test build can replace it?
