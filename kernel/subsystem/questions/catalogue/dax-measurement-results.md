# What the dax measurement found

Three models were asked the 30 questions in `dax-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C said it assumed kernels 6.16
to 7.0 and is current on `fs/dax.c`: most of its answers there needed one
correction or none. Reader A said 6.10 to 6.15, has the right mechanisms in
`fs/dax.c` and misses the newest steps in them. Reader B said 6.9 to 6.12 and
was wrong about fundamentals: which way round the idle reference counts are,
what is stored in an entry, how a pfn reaches a page table, what the fault
entry point takes, and the order of the steps in writeback. The hand-written
guide is 108 words of headings with no names in it, and was never checked
against current sources; how it compares with the tree is noted near the end.

What filesystem DAX is, and how an entry is locked, is known to two readers
out of three. What all three missed is under `drivers/dax/`: a third driver
type on the DAX bus, a second way for a filesystem to claim a `dax_device`,
and a kmem driver that now chooses the online type itself and has a sysfs
attribute to change it. After that come the facts in `fs/dax.c` that moved
with the rework of DAX page references, where each reader was caught by a
different part.

## What all three readers got wrong

- **A third driver on the DAX bus.** `drivers/dax/fsdev.c` registers
  `fsdev_dax_driver` with `DAXDRV_FSDEV_TYPE`. It maps a `dev_dax` with
  `MEMORY_DEVICE_FS_DAX` and no `vmemmap_shift`, offers no mmap, installs
  `dax_operations` on the bus-allocated device with `dax_set_ops()`, and resets
  stale compound folios with `dax_folio_reset_order()`. Readers A and B said
  there was no such driver. Reader C described it correctly where it was asked
  about it, but said in two other answers that it could not confirm it was
  merged, listed only two driver types in a third, and had the direct-access
  path use a field that does not exist.
- **How it binds.** `dax_match_type()` only ever computes the device or the
  kmem type, so the fsdev driver binds only after the device name is written
  to its `new_id`; a plain `bind` goes through `dax_bus_match()` and fails.
  Reader B offered a driver_override file; the DAX bus has none.
- **Claiming a device without a block device.** `fs_dax_get()` in
  `drivers/dax/super.c` requires the `dev_dax` to be bound to a
  `DAXDRV_FSDEV_TYPE` driver and returns `-EBUSY` if it is held. All three
  gave `fs_dax_get_by_bdev()` as the only claim, and none said that ext4,
  erofs and device mapper pass a NULL holder, which takes a reference without
  claiming. `fs_put_dax()` clears `holder_ops` before it releases
  `holder_data`, and warns on a holder that does not match.
- **kmem.** Probe calls `__add_memory_driver_managed()` with the online type
  from `mhp_get_default_online_type()`; all three named
  add_memory_driver_managed() and said the driver leaves onlining to the
  hotplug core or to userspace. All three said the state cannot be changed
  after probe: there is a `state` attribute (`state_store()`) that accepts
  "unplugged" and the online types, refuses "offline", onlines only from
  "unplugged", and unplugs with `offline_and_remove_memory_ranges()`. Unbind
  uses `remove_memory()`, which never offlines; what stays online is leaked
  together with the driver data, the memory group and `kmem_name`.
- **ext2.** Readers A and C listed it as a DAX filesystem and reader B did not
  notice that the documentation still does. `fs/ext2/super.c` ignores the
  option with "DAX support has been removed". The callers of
  `dax_iomap_rw()` and `dax_iomap_fault()` are ext4, xfs, fuse (virtiofs) and
  erofs.
- **Mapping flags.** ext4, xfs and erofs set only `VMA_HUGEPAGE_BIT`, from
  `->mmap_prepare` with `vma_desc_set_flags()`; fuse alone still sets
  `VM_MIXEDMAP | VM_HUGEPAGE`. Reader A had vm_flags_set(), reader B said every
  filesystem sets `VM_MIXEDMAP` and that `vma_is_dax()` depends on it, reader
  C said nothing sets it. `fs/dax.c` inserts with `vmf_insert_page_mkwrite()`
  and `vmf_insert_folio_pmd()`, the zero page included; reader A kept
  vmf_insert_mixed() for holes and reader B for everything, and reader B said
  no page reference is taken around the insertion.

## What only some readers got wrong

- **Idle reference counts** (reader B). An idle filesystem DAX page has count
  0 and an idle device DAX page has count 1, reset by
  `free_zone_device_folio()`. Reader B had them the other way round and had
  `dax_page_is_idle()` test for 1. The kerneldoc above
  `dax_layout_busy_page_range()` still says a page is idle at count 1, so the
  tree itself invites the error. `dax_busy_page()` tests the folio's
  reference count minus its mapcount; reader A had it look for a page that is
  not idle and reader B had it walk the xarray.
- **Breaking layouts** (readers A and B). `dax_break_layout()` itself removes
  the entries with `dax_delete_mapping_range()` once no page is busy, so
  `truncate_folio_batch_exceptionals()` warns on every DAX entry it still
  finds. Reader A left both out and was unsure what a NULL callback means (it
  returns `-ERESTARTSYS` at the first busy page, used for the second inode of
  a reflink in xfs); reader B had the callback filter which entries count as
  busy and had eviction call dax_delete_mapping_entry() where the
  filesystems call `dax_break_layout_final()`. The comment in `mm/truncate.c`
  names a dax_break_layout_entry() that does not exist.
- **Shared folios** (readers A and B). `dax_folio_make_shared()` sets
  `folio->mapping` to NULL and `share` to 1; reader A had a
  PAGE_MAPPING_DAX_SHARED marker, reader B said the mapping is kept and that
  the order is not stored on the folio. `dax_folio_init()` builds the compound
  folio at the entry's order and `dax_folio_reset_order()` splits it again.
- **What an entry holds** (reader B). An `unsigned long` pfn, not a pfn_t, and
  four flag bits. Reader B invented DAX_DIRTY and DAX_SHARED bits (dirty and
  to-write are xarray marks) and lock_slot()/unlock_slot().
- **Fault entry point** (reader B). `dax_iomap_fault()` takes an order, 0 or
  `PMD_ORDER`; reader B gave PE_SIZE values, wrong fallback conditions and an
  untouched page table on fallback (`split_huge_pmd()` runs).
- **Synchronous faults** (readers A and B). The mmap-time gate is
  `FOP_MMAP_SYNC` in `fop_flags`, not an mmap_supported_flags field, and
  `dax_finish_sync_fault()` calls `vfs_fsync_range()` and then
  `dax_insert_pfn_mkwrite()`; reader B had it repeat the iomap lookup.
- **Writeback** (reader B). The order is: clear the to-write mark under the
  entry lock, `pfn_mkclean_range()` over the VMAs that map the range,
  `dax_flush()`, clear the dirty mark, wake one waiter. Reader B had another
  order, and gated `dax_flush()` on the synchronous flag where the code tests
  `DAXDEV_WRITE_CACHE`.
- **Device flags** (readers A and B). `DAXDEV_NOMC` selects
  `_copy_mc_to_iter()`; both had it turn machine-check-safe copies off.
  Reader A named a dax_recovery_capable() that is not in the tree.
- **Device lifetime** (readers A and B). `alloc_dax()` returns a live device,
  because `dax_dev_get()` sets `DAXDEV_ALIVE`; the bus kills it at once and
  the bound driver's probe calls `run_dax()`. Reader B offered a get_dax().
  `dax_alive()` asserts that `dax_srcu` is held.
- **Character device faults** (readers A and B). `dev_dax_huge_fault()` returns
  `VM_FAULT_SIGBUS` for an order it does not handle, for an alignment larger
  than the fault and for a huge fault outside the VMA, and
  `VM_FAULT_FALLBACK` only when the alignment is smaller; both had some of
  these swapped. The check is on `VMA_MAYSHARE_BIT`.
- **Bus locks** (all three, in detail). `delete_store()` takes
  `dax_dev_rwsem` only; each reader gave it the region lock.

## What the readers already knew

Readers A and C: the four flag bits of an entry and the helpers that read
them, the wait table and the two wake modes, the PMD fallback conditions, the
read and write path with its poison recovery, the writeback order, the static
and dynamic regions and the two bus rwsems. Reader C also had the fault
sequence, the break-layout loop with its NULL callback, the idle counts and
the synchronous fault path right to within one detail each. All three knew
that `dax_read_lock()` has to be held across `dax_direct_access()` and the use
of the address it returns.

## Where the hand-written guide is stale

`dax.md` names no function, file or lock, so it has little to be wrong about
and nothing a reviewer can look up. Against this tree:

- "DAX entries in radix tree": the page cache is an xarray and the entries are
  xarray value entries.
- "No struct page for some DAX mappings": `FS_DAX` depends on `ZONE_DEVICE`,
  `fs/dax.c` converts every pfn with `pfn_to_page()`, and there is no pfn_t
  and no limited mode without pages. Both kinds of DAX have folios.
- "Special handling for 2MB/1GB huge pages": filesystem DAX handles order 0
  and `PMD_ORDER` and nothing else; PUD faults exist only in the character
  device driver.
- "Huge page splitting/collapsing": the fallback path calls
  `split_huge_pmd()`; nothing collapses a DAX mapping.
- "Memory barriers for ordering" and "power-fail atomicity" are not things
  `fs/dax.c` or `drivers/dax/` do; persistence there is `dax_flush()` from
  writeback and the synchronous fault path.
- It has nothing on page references and breaking layouts, on the `dax_device`
  lifetime, or on anything under `drivers/dax/`.

## What was left out of the build set and why

The build set has 10 of the 30 questions, 505 words of budget, sized to 600
words, the floor for a built guide, with no question under 40. Kept: the file
map (every reader missed a file), the mapping flags and insertion functions
(all three wrong, each differently), the idle counts, the folio state and
breaking layouts (the reworked reference rules, where the oldest reader is
inverted and the middle one a step behind), writeback (the order of the steps
is the correctness argument, the oldest reader had another order, and
persistence is a third of the hand-written guide), kmem and the
filesystem-facing driver (all three wrong), the entry lock rule (the centre of
`fs/dax.c`), and what a change to entry handling has to preserve (three
corrections or more for every reader, and the only question about changing the
implementation). Left out:

- What two readers answer and the space cannot carry for the third: entry
  encoding, entry locking, PMD and PTE conflicts, the fault sequence, PMD
  fallback, holes and COW, the read and write path.
- `dax.truncate-usage`, because the answer to `dax.break-layout` carries the
  fact it turns on; `dax.holder` and `dax.driver-binding`, because the answer
  to `dax.fsdev` names the claim function and what it returns under another
  driver. A guide with room for one more question should take `dax.holder`: no
  reader said that a NULL holder takes a reference without claiming.
- `dax.device-lifetime`, `dax.operations`, `dax.memory-failure`,
  `dax.sync-faults`: real corrections for readers A and B, narrower than what
  was kept.
- `dax.bus-model`, `dax.device-mmap`, `dax.flavours`, `dax.filesystems`,
  `dax.nrpages-accounting`, `dax.test-build`: they stay in the measurement
  set.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A           68        34%      3      9   6.10 to 6.15
reader B          104        81%      0     29   6.9 to 6.12
reader C           60        21%     15      7   6.16 to 7.0

question                    reader A      reader B      reader C   verdict
dax.core-files               6% ( 3)      25% ( 6)       4% ( 2)   middling
dax.flavours                23% ( 1)      82% ( 2)      49% ( 4)   weak: reader B, reader C
dax.filesystems             37% ( 1)      88% ( 3)      53% ( 4)   weak: reader B, reader C
dax.entry-encoding           1% ( 1)      69% ( 5)       0% ( 0)   weak: reader B
dax.entry-locking           16% ( 2)      84% ( 1)       7% ( 2)   weak: reader B
dax.entry-lock-usage        29% ( 1)      87% ( 1)      24% ( 1)   weak: reader B
dax.order-conflicts         44% ( 1)      74% ( 1)      11% ( 1)   weak: reader A, reader B
dax.nrpages-accounting      56% ( 2)      95% ( 1)      22% ( 1)   weak: reader A, reader B
dax.fault-entry-points      47% ( 1)      82% ( 4)       6% ( 2)   weak: reader A, reader B
dax.vma-flags               26% ( 2)      83% ( 5)      42% ( 3)   weak: reader B, reader C
dax.pmd-fallback            14% ( 1)      92% ( 3)      11% ( 1)   weak: reader B
dax.sync-faults             55% ( 1)      80% ( 3)       2% ( 1)   weak: reader A, reader B
dax.holes-and-cow           24% ( 1)      86% ( 2)      15% ( 1)   weak: reader B
dax.read-write-path         31% ( 5)      87% ( 5)       0% ( 0)   weak: reader B
dax.writeback               20% ( 3)      85% ( 6)      12% ( 1)   weak: reader B
dax.page-refcount           28% ( 2)      78% ( 4)       3% ( 1)   weak: reader B
dax.folio-association       29% ( 1)      89% ( 3)       8% ( 2)   weak: reader B
dax.break-layout            26% ( 1)      81% ( 3)       0% ( 0)   weak: reader B
dax.truncate-usage          32% ( 2)      86% ( 3)      10% ( 1)   weak: reader B
dax.device-lifetime         54% ( 3)      64% ( 3)      21% ( 2)   weak: reader A, reader B
dax.operations              24% ( 3)      71% ( 5)      21% ( 2)   weak: reader B
dax.holder                  24% ( 3)      85% ( 4)      58% ( 4)   weak: reader B, reader C
dax.memory-failure          37% ( 1)      90% ( 3)      28% ( 1)   weak: reader B
dax.bus-model               23% ( 2)      82% ( 6)      12% ( 3)   weak: reader B
dax.driver-binding          58% ( 5)      85% ( 5)      45% ( 3)   all weak
dax.device-mmap             35% ( 4)      88% ( 3)      24% ( 2)   weak: reader B
dax.kmem                    69% ( 5)      82% ( 3)      52% ( 5)   all weak
dax.fsdev                   78% ( 3)      93% ( 3)      52% ( 6)   all weak
dax.change-checklist        57% ( 4)      93% ( 5)      32% ( 3)   weak: reader A, reader B
dax.test-build              36% ( 3)      93% ( 3)      20% ( 1)   weak: reader B
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `dax.sync-faults`, `dax.device-lifetime`, `dax.holder`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `dax.flavours`, `dax.entry-encoding`, `dax.entry-locking`, `dax.order-conflicts`, `dax.fault-entry-points`, `dax.pmd-fallback`, `dax.holes-and-cow`, `dax.read-write-path`, `dax.truncate-usage`, `dax.operations`, `dax.device-mmap`.
Put back because a guide has to say what each main structure is before anything else: `dax.bus-model`.

## Questions reorganised

By subject now, still 27 questions: finding your way (the file map and `dax.flavours`); page cache
entries (with `dax.entry-lock-usage` and `dax.change-checklist`, which are about the same entries);
faults (with `dax.vma-flags`); page references and breaking layouts (with `dax.break-layout` and
`dax.truncate-usage` side by side); reads, writes and writeback; the dax_device core; the DAX bus and
its drivers. Nothing merged or dropped and no ids changed. `dax.bus-model`, `dax.device-lifetime` and
`dax.operations` no longer ask what a structure is or which callbacks it has, which the overview and
the header give; `dax.entry-encoding`, `dax.entry-locking` and `dax.pmd-fallback` ask for the contract,
not a list; `dax.holder` and `dax.fsdev` also ask about a claim with no holder and how the driver binds.
