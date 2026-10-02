# Questions: MM Page Table Operations (measurement set)

- guide: mm-pagetable.md
- title: MM Page Table Operations

A wide set of questions about page tables as generic MM code uses them: the
entries and their software bits, non-present entries, the lock and mapping
helpers, the walkers, batching, TLB flushing and the freeing of page table
pages. It is used to measure what a model already knows before deciding what
the built guide should spend its words on. The hand-written guide it will
replace is 4,005 words. Huge page specifics, VMAs and folios have their own
sets. Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## pagetable.core-files: Core files

- section: Finding your way
- relevance: 4 - helpers and whole mechanisms have moved between files
- words: 110

Which files hold the generic page table accessors, the typed helpers for
non-present entries, the swap entry encoding, the generic fallbacks for
architecture helpers, the user fault, zap and fork copy paths, protection
change, page table move, the callback walker, the reverse-map walker, the
mmu_gather code, reclaim of empty page tables, the page table checker and the
page table dumper? A table. Start from `include/linux/pgtable.h` and `mm/`.

## pagetable.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

For each job (map and lock a PTE table, walk a range with callbacks, walk to
the one folio at an address, visit every mapping of a folio, zap a range of one
VMA, change protection over a range, insert a PFN or a page from a driver, apply
a function to each PTE of a kernel range, free the page tables of an unmapped
range), which function do you start reading from? A table.

## pagetable.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - the locking rules are written down in one place
- words: 60

Which files under `Documentation/mm/` are the authority on page table locking
and the four kinds of page table operation, on split page table locks, on the
helpers an architecture supplies, and on the page table checker?

## pagetable.debug-and-tests: Debug and test builds

- section: Finding your way
- relevance: 3 - a helper change is checked by more than the compiler
- words: 70

Which debug options and tests exercise page table helpers (a boot-time test of
the architecture helpers, a checker of user mappings, a dumper, a unit test of
the lazy MMU mode, the selftests), and where does each live? Start from
`mm/Kconfig.debug`.

# Entries and how they are read

## pagetable.entry-read-write: Reading and writing entries

- section: Entries
- relevance: 4 - a plain dereference is sometimes a bug and sometimes fine
- words: 90

Which helpers does generic code use to read and to write an entry at each
level, what do the readers guarantee, and when is dereferencing the pointer
directly still done in-tree? Start from `ptep_get()`, `pmdp_get()` and
`set_ptes()`.

## pagetable.atomicity: Atomic updates

- section: Entries
- relevance: 4 - hardware writes accessed and dirty bits under you
- words: 80

Which bits can hardware change in a present entry while software holds the page
table lock, when is a plain read followed by a write therefore unsafe, and
which helpers do the read-and-clear or the permission change atomically?
Start from `ptep_get_and_clear()` and `ptep_modify_prot_start()`.

## pagetable.lockless-reads: Lockless reads

- section: Entries
- relevance: 3 - only matters on a few configurations, where it is a torn read
- words: 70

What do `ptep_get_lockless()` and `pmdp_get_lockless()` do that the ordinary
readers do not, on which configurations is that different code, and who must
use them? Start from `CONFIG_GUP_GET_PXX_LOW_HIGH`.

## pagetable.pte-mkwrite-vma: Making an entry writable

- section: Entries
- relevance: 3 - the helper's signature changed and there are two forms
- words: 60

Which helpers set the write bit on a PTE and on a PMD, why does one form take
the VMA, and which helper applies the VMA's permission for you? Start from
`pte_mkwrite()` and `maybe_mkwrite()`.

## pagetable.special-bit: Special entries

- section: Entries
- relevance: 4 - decides whether a walker sees a page at all
- words: 90

What does the special bit on an entry mean, at which levels can it be set and
under which configuration options, and what is mapped special? Start from
`pgtable_level_has_pxx_special()` in `mm/memory.c`.

## pagetable.normal-page-lookup: Normal page lookup

- section: Entries
- relevance: 4 - the family has grown and one hook overrides the bit
- words: 90

Which functions turn a present entry into its page or folio at PTE, PMD and
PUD level, how do they decide on an architecture without a special bit, and
which VMA hook can return a page for an entry that is marked special? Start
from `__vm_normal_page()`.

## pagetable.device-memory-entries: Device memory entries

- section: Entries
- relevance: 3 - a bit readers remember may no longer exist
- words: 60

How does a present entry that maps a ZONE_DEVICE page (fsdax, device coherent
memory) differ from one that maps ordinary memory, is there a dedicated PTE bit
or a PFN wrapper type for it in this tree, and how do walkers recognise such a
page?

## pagetable.uffd-bit: The userfaultfd entry bit

- section: Entries
- relevance: 5 - the accessors were renamed and the bit gained a second meaning
- words: 90

One software bit in a present entry and in a swap-format entry records
userfaultfd protection. What are its accessors called in this tree at PTE and
PMD level, which userfaultfd modes use it, and how does code tell which mode an
entry belongs to? Start from `include/linux/userfaultfd_k.h`.

## pagetable.soft-dirty-support: Soft-dirty support test

- section: Entries
- relevance: 3 - a compile-time test is wrong where support is found at run time
- words: 50

How should code ask whether soft-dirty tracking is available, why is testing the
configuration option alone not enough, and what do the soft-dirty accessors do
when it is not?

# Non-present entries

## pagetable.nonpresent-api: Typed non-present entries

- section: Non-present entries
- relevance: 5 - the whole family of helpers was renamed
- words: 110

Which type and helpers does this tree use to decode a non-present PTE or PMD
and test what kind it is, which older swap-entry helpers do they replace, and
which of the older constructors are still used? Start from
`include/linux/leafops.h`. If the tree has no such header, say so and describe
what it uses.

## pagetable.nonpresent-kinds: Kinds of non-present entry

- section: Non-present entries
- relevance: 5 - each kind has its own rules and they are easy to conflate
- words: 120

Give a table of the kinds of non-present entry: the enumerator or enumerators,
the predicate, the configuration option each depends on, and in one phrase what
the entry stands for. Start from `enum softleaf_type`.

## pagetable.markers: Marker entries

- section: Non-present entries
- relevance: 4 - markers carry no page and each kind faults differently
- words: 90

Which marker bits exist, what installs each, how does a fault on each resolve,
and which zap flag decides whether markers survive a zap? Start from
`PTE_MARKER_MASK` in `include/linux/swapops.h`.

## pagetable.pmd-nonpresent: Non-present PMD leaves

- section: Non-present entries
- relevance: 4 - code that tests only for a present huge PMD misses them
- words: 80

Which kinds of non-present entry can sit in a PMD, which configuration option
enables them, and which predicates test for them? Start from
`softleaf_is_valid_pmd_entry()`.

## pagetable.nonpresent-has-pfn: Entries that carry a PFN

- section: Non-present entries
- relevance: 4 - sharing the property does not make kinds interchangeable
- words: 80

Which kinds of non-present entry encode a PFN, how is the page or folio
recovered from one, and what must be true of the folio when the entry is a
migration entry? Start from `softleaf_has_pfn()` and `softleaf_to_folio()`.

## pagetable.nonpresent-refs: References held by non-present entries

- section: Non-present entries
- relevance: 4 - teardown must drop exactly what the entry holds
- words: 90

Which kinds of non-present entry keep a folio reference and a mapcount, which
keep neither, and what does zapping each kind therefore have to do? Start from
`zap_nonpresent_ptes()` and `try_to_migrate_one()`.

## pagetable.swap-pte-bits: Bits in a swap-format entry

- section: Non-present entries
- relevance: 4 - the present and swap forms use different bit positions
- words: 90

Which software bits can a swap-format PTE carry, which function builds them
when a page is unmapped for swap, which helper strips them so two entries can
be compared, and what goes wrong when the present-entry accessor is used on a
swap-format entry? Start from `pte_swp_clear_flags()`.

## pagetable.migration-ad-bits: Accessed and dirty in migration entries

- section: Non-present entries
- relevance: 3 - the bits are optional and restoring dirty has a condition
- words: 90

How does a migration entry record that the page was young or dirty, when is
that supported, and under what condition is dirty put back when the entry is
removed? Start from `migration_entry_supports_ad()` and
`remove_migration_pte()`.

## pagetable.nonpresent-dispatch-usage: Dispatch on non-present entries

- section: Non-present entries
- relevance: 5 - a kind accepted in the wrong branch misbehaves silently
- words: 100

In code that branches on the kind of a non-present entry, what usage is unsafe,
and what that looks similar is correct? Say which kinds are most often wrongly
grouped and why they differ, and name in-tree code that dispatches correctly.
Start from `check_pte()` in `mm/page_vma_mapped.c` and `copy_nonpresent_pte()`.

## pagetable.nonpresent-to-present: Restoring software bits

- section: Non-present entries
- relevance: 5 - a lost bit breaks userfaultfd or checkpoint restore silently
- words: 120

When a non-present entry is replaced by a present one, which software bits
have to be carried across, why can they not be copied as a mask, and which
functions do it? Say also what each site does beyond the common transfer. Start
from `do_swap_page()`, `restore_exclusive_pte()`, `remove_migration_pte()` and
`unuse_pte()`.

## pagetable.nonpresent-rewrite: Rewriting a non-present entry

- section: Non-present entries
- relevance: 3 - the swap-side writers differ and some drops are deliberate
- words: 80

When one non-present entry is rewritten as another (fork, a protection change),
which writers carry the software bits, and which rewrites deliberately drop one
of them? Start from `copy_nonpresent_pte()` and `change_softleaf_pte()`.

# State of a present entry

## pagetable.write-dirty-combinations: Writable and dirty combinations

- section: Present entry state
- relevance: 5 - one combination loses data and a similar one is normal
- words: 120

Which combinations of writable and dirty are forbidden in a present PTE and
which are only unusual? Cover shared mappings that want write notification and
exclusive anonymous pages, name what enforces each, and name paths that
legitimately produce a clean writable entry. Start from
`can_change_pte_writable()` in `mm/mprotect.c`.

## pagetable.young-dirty: Accessed with dirty

- section: Present entry state
- relevance: 3 - reviewers flag a legal state
- words: 70

Does marking an entry dirty also mark it accessed, is a dirty entry that is not
accessed legal, and why do fault paths set accessed themselves? Start from
`pte_sw_mkyoung()`.

## pagetable.fresh-anon-pte: Fresh anonymous entries

- section: Present entry state
- relevance: 3 - the function that builds the entry moved
- words: 70

Which function builds and installs the entries for a freshly allocated
anonymous folio on a fault, which bits does it set for a writable VMA, and who
else calls it? Start from `do_anonymous_page()`.

## pagetable.lazyfree-pte: Lazily freed entries

- section: Present entry state
- relevance: 3 - the state looks like a bug and is the design
- words: 70

What does MADV_FREE do to the bits of a present entry, which helper does it,
and what happens on the next write with and without hardware dirty tracking?
Start from `madvise_free_pte_range()`.

## pagetable.vm-write-gate: Writable entries and VM_WRITE

- section: Present entry state
- relevance: 4 - permissions can change between lookup and install
- words: 70

What usage of the write bit when building an entry is unsafe with respect to
the VMA's flags, and what is correct? Name the paths where it has to be checked
at install time and why.

## pagetable.uffd-rwp-protnone: Protnone entries and their two users

- section: Present entry state
- relevance: 4 - two mechanisms share one encoding
- words: 100

Which mechanisms use a present entry with no access permission in an accessible
VMA, how are their entries told apart, and which paths have to put the
no-access protection back after changing an entry's protection? Start from
`pte_protnone()` in `include/linux/pgtable.h` and `change_present_ptes()`.

## pagetable.numa-hint: NUMA hinting protection

- section: Present entry state
- relevance: 3 - the filter moved into a helper
- words: 70

When applying NUMA hinting protection, which entries does the protection loop
skip, and which helper decides whether a folio is worth a hinting fault? Start
from `change_pte_range()`.

## pagetable.change-prot-flags: Protection change flags

- section: Present entry state
- relevance: 3 - the flag set grew
- words: 60

Which flags can a caller pass to the protection change code and what does each
ask for? Start from `MM_CP_TRY_CHANGE_WRITABLE` in `include/linux/mm.h`.

## pagetable.soft-dirty-on-move: Soft dirty on move

- section: Present entry state
- relevance: 4 - two dirty bits with different audiences
- words: 90

When an entry is moved to a new address, what must happen to soft-dirty and to
hardware dirty, what usage is unsafe, and which function is the reference?
Start from `move_ptes()` in `mm/mremap.c`.

## pagetable.vma-flag-bits: VMA flags with per-entry state

- section: Present entry state
- relevance: 3 - the flag and the entries are cleared in different places
- words: 70

When a VMA flag that has state in the entries behind it is cleared, which forms
of entry have to be cleaned up, and where does the tree do it for userfaultfd
write protection? Start from `clear_uffd_wp_pmd()`.

## pagetable.present-only-accessors: Present-only conversions

- section: Present entry state
- relevance: 5 - the wrong accessor turns swap bits into a page pointer
- words: 100

Which helpers that turn an entry into a page or folio are only meaningful for a
present entry, what usage of them is unsafe, and what is the correct way to get
the folio behind a non-present PMD or PTE? Start from `pmd_folio()` and
`pmd_to_softleaf_folio()`.

## pagetable.special-usage: Marking entries special

- section: Present entry state
- relevance: 4 - a special entry hides a refcounted folio from every walker
- words: 100

What usage of the special bit when mapping a folio is unsafe, and what that
looks similar is correct? Say which constructors to use for a refcounted folio
and for a raw PFN at PMD and PUD level, and how the tree shares one insert
function between them. Start from `insert_pmd()` in `mm/huge_memory.c`.

# Locks and the life of a page table

## pagetable.ptdesc: Page table descriptor

- section: Tables and locks
- relevance: 4 - page table pages have their own type and helpers now
- words: 100

What describes a page table page, which fields does it have, how is its layout
tied to `struct page`, and which helpers allocate, construct, destruct and free
one? Start from `struct ptdesc` in `include/linux/mm_types.h`.

## pagetable.split-locks: Page table locks

- section: Tables and locks
- relevance: 4 - which lock covers which level depends on configuration
- words: 90

Which lock protects entries at each level, when are the PTE and PMD locks
per-table rather than per-mm, where does a per-table lock live, and which
helpers return each lock? Start from `pte_lockptr()` and `pmd_lock()`.

## pagetable.pte-map-variants: Mapping a PTE table

- section: Tables and locks
- relevance: 5 - four helpers with different guarantees
- words: 120

Give a table of the helpers that map a PTE table: for each, whether it takes
the lock, what it hands back, what it guarantees about the table staying
attached, and what it is meant for. Start from the comment above
`pte_offset_map_lock()` in `mm/pgtable-generic.c`.

## pagetable.pte-map-null: Failure to map a PTE table

- section: Tables and locks
- relevance: 5 - callers that assume success crash or skip data
- words: 80

Under which conditions do the PTE mapping helpers return NULL, what does the
locking variant recheck before it returns success, and what do correct callers
do on NULL? Start from `__pte_offset_map()`.

## pagetable.pte-map-rcu: Between map and unmap

- section: Tables and locks
- relevance: 4 - the mapping holds more than a pointer
- words: 70

What does a successful PTE table mapping hold until the matching unmap, what
may code therefore not do in between, and what does a table that was detached
meanwhile look like to the holder?

## pagetable.pte-unmap-pointer: Pointer given to unmap

- section: Tables and locks
- relevance: 3 - invisible on 64-bit, wrong page unmapped on one configuration
- words: 80

Which pointer must the PTE unmap be given, what usage is unsafe after a loop
that advanced the pointer or with a local copy of an entry, in what order must
two mappings be released, and on which configuration does a mistake show?

## pagetable.install-table: Installing a new table

- section: Tables and locks
- relevance: 4 - ordering and accounting are easy to drop
- words: 80

How is a newly allocated PTE table published into an empty PMD entry: which
lock, which barrier and why, which counter, and what happens to the allocation
when another thread got there first? Start from `pmd_install()` and
`__pte_alloc()`.

## pagetable.populate-lock-rule: Locks for each operation

- section: Tables and locks
- relevance: 5 - the rmap locks allow less than people assume
- words: 100

For traversing, installing, zapping and freeing, which of the mmap lock, a
per-VMA lock and the reverse-map locks is enough to hold, and why is installing
an entry under a reverse-map lock alone unsafe? Start from
`Documentation/mm/process_addrs.rst`.

## pagetable.free-pgtables: Freeing tables at unmap

- section: Tables and locks
- relevance: 4 - it takes no page table lock and may not use RCU
- words: 90

What does the function that frees page tables after an unmap assume has already
been done, which locks does it not take, what describes the range to it, and
what must code that is not the owner of the mm avoid once a VMA is detached?
Start from `free_pgtables()`.

## pagetable.empty-table-reclaim: Reclaiming empty PTE tables

- section: Tables and locks
- relevance: 5 - a PMD entry can vanish under a reader of a live mm
- words: 120

Outside unmap and exit, which paths detach and free a PTE table from a live mm,
under which locks, which configuration option governs the zap-time one and
where does that code live, and how is the table page finally freed? Start from
`zap_pte_range()` and `retract_page_tables()`.

## pagetable.recheck-after-relock: Decisions across a lock drop

- section: Tables and locks
- relevance: 4 - entries can be repopulated while the lock is dropped
- words: 80

In the zap path, how does the code decide that a PTE table is empty and can be
freed when the page table lock was dropped part way, and what does it recheck?
Start from `zap_pte_table_if_empty()`.

## pagetable.vma-lock-and-tables: mmap write lock and tables

- section: Tables and locks
- relevance: 5 - the race has shipped, and nothing in a diff shows it
- words: 110

What usage of page table state by code that holds the mmap write lock is
unsafe, which operations running under only a per-VMA lock can clear a PMD
entry and free the PTE table, through which call chain, and what makes the
write-lock holder safe? Start from `collapse_huge_page()` and
`zap_vma_range_batched()`.

## pagetable.move-tables: Moving page tables

- section: Tables and locks
- relevance: 3 - moving whole tables needs every lock
- words: 80

When mremap moves entries or whole tables, which locks does it take at each
level, when can it skip the reverse-map locks, and where does it flush the TLB
relative to dropping the page table locks? Start from `move_page_tables()`.

## pagetable.pmd-lock-accepts: Huge PMD lock helper

- section: Tables and locks
- relevance: 5 - success does not mean the PMD is present
- words: 80

For which PMD values does `pmd_trans_huge_lock()` succeed, what must a caller
therefore check before it uses the PMD as a mapping of a page, and which
predicate does the helper use? Start from `__pmd_trans_huge_lock()`.

## pagetable.fault-lock-order: Fault handler lock order

- section: Tables and locks
- relevance: 3 - an ABBA deadlock that lockdep only sees with freezing
- words: 100

Under which locks do a file's fault and page_mkwrite handlers run, which
filesystem freeze protection may they take and which not, and how does the
write path avoid faulting while it holds a folio lock? Start from
`vmf_can_call_fault()` and `filemap_page_mkwrite()`.

# Walkers

## pagetable.walk-ops: Walker callbacks

- section: The callback walker
- relevance: 4 - which callback fires for what decides correctness
- words: 110

Which callbacks can a user of the generic page walker supply, and when is each
called? Say which are called for empty entries, which for holes, and which one
makes the walker allocate missing tables. Start from `struct mm_walk_ops` in
`include/linux/pagewalk.h`.

## pagetable.walk-entry-points: Walker entry points

- section: The callback walker
- relevance: 4 - several variants with different checks
- words: 100

Which entry points does the page walker have (a range of an mm, a range of one
VMA, a whole VMA, a file mapping, kernel ranges, debug), what does each require
of its caller, and which refuse a callback set that installs entries?

## pagetable.walk-lock: Walker locking

- section: The callback walker
- relevance: 4 - the field makes the walker assert or take locks
- words: 80

Which values can the walker's lock field take, and for each, what does the
walker assert about the mmap lock and do or assert about each VMA? Start from
`enum page_walk_lock`.

## pagetable.walk-actions: Walker actions

- section: The callback walker
- relevance: 3 - how a callback steers the descent
- words: 60

Which actions can a PUD or PMD callback set, what does each make the walker do
next, and what is the default? Start from `enum page_walk_action`.

## pagetable.walker-returns: Callback return values

- section: The callback walker
- relevance: 3 - one callback's positive return means something else
- words: 60

What do zero, positive and negative returns from an entry callback do to the
walk and to the caller's return value, and how does the VMA test callback
differ?

## pagetable.walker-pmd-entry: PMD callbacks and huge entries

- section: The callback walker
- relevance: 5 - a callback that ignores huge PMDs skips data or crashes
- words: 110

Which PMD values does a PMD callback receive, when does the walker go on to the
PTE level after it, what does the walker do to a huge PMD before descending,
and what must a PMD callback that walks PTEs itself do about huge and
non-present PMDs and about a failed PTE mapping?

## pagetable.walker-default-vmas: VMAs the walker skips

- section: The callback walker
- relevance: 3 - success can mean skipped
- words: 70

Without a VMA test callback, which VMAs does a range walk skip, what is called
for them instead, and what does a hugetlb VMA get when no hugetlb callback is
supplied? Start from `walk_page_test()`.

## pagetable.walker-again-usage: Retrying from a callback

- section: The callback walker
- relevance: 4 - an unbounded retry spins while a migration is in flight
- words: 100

What usage of the retry action in a PMD callback is unsafe, and what that looks
similar is correct? Say why the PTE mapping can keep failing, name callbacks
that handle it correctly, and say what the walker does itself for users of the
PTE callback. Start from `walk_pte_range()`.

## pagetable.folio-walk: Walking to one folio

- section: Other walkers
- relevance: 3 - a newer helper with strict rules on what the caller may do
- words: 80

What does `folio_walk_start()` return and leave locked, which entries does it
refuse, what does its flag add, and what may the caller do with the folio
before and after `folio_walk_end()`?

## pagetable.pvmw-state: Reverse-map walk state

- section: Other walkers
- relevance: 4 - the flags select which entries are returned
- words: 90

Which fields and flags does the reverse-map page table walk take and set, what
does each input flag select, and which helpers end or restart a walk early?
Start from `struct page_vma_mapped_walk` in `include/linux/rmap.h`.

## pagetable.pvmw-nonpresent: Entries the reverse-map walk returns

- section: Other walkers
- relevance: 5 - a returned PTE is not always present
- words: 100

With and without the migration flag, which kinds of PTE can the reverse-map
walk return true for, and which kinds of PMD when it returns with no PTE set?
Start from `check_pte()` and `page_vma_mapped_walk()`.

## pagetable.pvmw-accessor-usage: Accessors in reverse-map callbacks

- section: Other walkers
- relevance: 5 - present-entry accessors read garbage from a swap-format entry
- words: 110

In a callback that loops over the reverse-map walk, what usage of PTE accessors
is unsafe, and what is correct? Say how to get the PFN, writability and the
software bits from a non-present result, name code that does it fully, and name
in-tree callbacks that do not check. Start from `try_to_migrate_one()` and
`folio_referenced_one()`.

## pagetable.gup-fast-walk: Lockless walk by GUP-fast

- section: Other walkers
- relevance: 4 - the rules every table-freeing path has to respect
- words: 90

How does GUP-fast walk page tables with no lock: what excludes table freeing,
how does it read each level, what does it recheck after taking a reference, and
on which entries does it give up? Start from `gup_fast_pte_range()`.

## pagetable.hugetlb-differences: hugetlb entries

- section: Other walkers
- relevance: 3 - generic accessors are wrong there
- words: 70

How do hugetlb page table entries differ for generic code: which accessors
read and write them, which lock protects a walk, and what is PMD sharing? Start
from `huge_ptep_get()` and `hugetlb_walk()`.

# Batching

## pagetable.batch-flags: Batch flags

- section: PTE batching
- relevance: 5 - each flag changes which entries join a batch
- words: 100

Give a table of the flags the PTE batching helper takes and what each makes it
compare or merge. Start from `fpb_t` in `mm/internal.h`.

## pagetable.batch-default-ignores: Default batch comparison

- section: PTE batching
- relevance: 5 - the simple wrapper ignores more than people expect
- words: 70

With no flags, which bits of consecutive PTEs does the batching helper ignore
when it decides they belong to one batch, and which must match? Where is the
wrapper that passes no flags? Start from `__pte_batch_clear_ignored()`.

## pagetable.batch-writeback-usage: Writing a batch back

- section: PTE batching
- relevance: 5 - the first entry's permissions get stamped on the rest
- words: 120

What usage of a PTE batch count is unsafe when the caller then writes entries
back, and what that looks similar is correct? Say why, name callers that may
use no flags, callers that must respect or merge the write bit and how they do
it, and the reverse-map unmap helper's flags. Start from `copy_present_ptes()`,
`move_ptes()` and `folio_unmap_pte_batch()`.

## pagetable.batch-bounds: Batch bounds

- section: PTE batching
- relevance: 5 - an uncapped count reads past the end of a page table
- words: 100

What must a caller guarantee about the maximum count it passes to the batching
helper, what does the helper cap by itself, which callers get a bounded range
for free, and which have to compute the bound? Give the usual expression.

## pagetable.batch-helpers: Ranged PTE helpers

- section: PTE batching
- relevance: 4 - what each does to the bits that differ within a batch
- words: 110

Which helpers operate on a run of consecutive PTEs (set, clear, clear and
return, write-protect, clear young and dirty, protection change start and
commit), and for each, how are bits that differ across the run treated? What
is `pte_batch_hint()` for? Start from `set_ptes()` in
`include/linux/pgtable.h`.

## pagetable.batch-handrolled: Hand-written batch loops

- section: PTE batching
- relevance: 2 - one paravirtual configuration
- words: 60

Why is it unsafe for a hand-written loop to find the end of a batch only by
comparing each PTE with the previous one advanced by a PFN, and what should
bound the loop? Start from `pte_advance_pfn()`.

## pagetable.large-folio-install: Partly populated range

- section: PTE batching
- relevance: 4 - the wrong fallback livelocks with no warning
- words: 100

When a fault wants to map a large folio with several PTEs and finds some of
them already populated, what does each path do (file folio, fresh anonymous
folio, PMD mapping), and what usage is unsafe? Start from `pte_range_none()`,
`finish_fault()` and `do_anonymous_page()`.

# TLB and freeing

## pagetable.tlb-flush-rules: Transitions that need a flush

- section: TLB flushing
- relevance: 5 - a missed flush leaves stale write access
- words: 100

Which changes to a present entry need a TLB flush before anything relies on
them, which do not, and what do paths that make an entry more permissive call
instead? Start from `ptep_set_access_flags()` and `update_mmu_cache_range()`.

## pagetable.tlb-flush-before-unlock: Flushing before the lock is dropped

- section: TLB flushing
- relevance: 4 - some flushes cannot wait for the end of the gather
- words: 100

In which cases must the TLB be flushed before the page table lock is released
rather than when the gather finishes, and how do the zap and mremap paths do
it? Start from `zap_pte_range()`, `tlb_flush_rmaps()` and `move_ptes()`.

## pagetable.mmu-gather-api: The mmu_gather API

- section: TLB flushing
- relevance: 4 - new start variants and new fields
- words: 110

Which functions start and finish an mmu_gather, which fields record what was
cleared and freed, what ordering does it guarantee, and what does finishing do
when another thread is gathering on the same mm? Start from `struct mmu_gather`
in `include/asm-generic/tlb.h`.

## pagetable.batched-flush-pending: Reclaim's deferred flushes

- section: TLB flushing
- relevance: 4 - entries look clear while a stale TLB entry still exists
- words: 100

Reclaim can clear entries and defer the TLB flush. Which function completes
those flushes for an mm, when and under what lock must loops that infer TLB
state from entry contents call it, which loops call it, and name a
drop-and-retake loop that correctly does not. Start from
`flush_tlb_batched_pending()`.

## pagetable.zap-api: Zap functions

- section: Zapping
- relevance: 5 - every name in this family changed
- words: 100

What are the functions for zapping a range within one VMA, the same with a
caller-supplied gather, the driver-facing one for PFN mappings, the OOM
reaper's one, and the internal per-VMA worker that all of them reach? Give
current names and what each requires. Start from `unmap_vmas()`.

## pagetable.zap-details: Zap details

- section: Zapping
- relevance: 3 - the fields select what a zap leaves behind
- words: 70

Which fields and flags does the structure that parameterises a zap have, and
what does each do? Start from `struct zap_details`.

## pagetable.table-free-configs: Table freeing configurations

- section: Freeing page table pages
- relevance: 4 - what the free waits for depends on three options
- words: 100

What do the options for freeing page table pages through the gather select
(tables freed as plain pages, a table batch, a table batch freed after an RCU
grace period, reclaim of empty PTE tables), and what happens when the batch page
cannot be allocated? Start from `tlb_remove_table()`.

## pagetable.table-free-vs-gup-fast: Freeing a table against lockless walkers

- section: Freeing page table pages
- relevance: 5 - use after free with no lock to point at
- words: 110

After an upper-level entry is cleared, which mechanisms make it safe to free
the table page while lockless walkers may still be in it, and which similarly
named helpers are not such a mechanism or must not be used for freeing? Start
from `mm/mmu_gather.c`, `pte_free_defer()` and `pmdp_get_lockless_sync()`.

## pagetable.kernel-table-free: Freeing kernel page tables

- section: Freeing page table pages
- relevance: 3 - kernel tables have their own deferred path
- words: 70

How is a page table page that maps kernel addresses marked, how does its free
path differ, and under which option is it deferred and to what? Start from
`pagetable_free_kernel()`.

# Kernel page tables and lazy mode

## pagetable.kernel-populate-sync: Populating kernel tables

- section: Kernel page tables
- relevance: 4 - a new top-level entry may not reach other page tables
- words: 110

Which helpers populate top-level entries of kernel page tables so that other
processes' tables see them, what decides whether a sync is needed, which
allocation helpers record what was modified, and what usage on an error path is
unsafe? Start from `include/linux/pgalloc.h`, `mm/pgalloc-track.h` and
`__apply_to_page_range()`.

## pagetable.kernel-walk-hotplug: Walking kernel tables

- section: Kernel page tables
- relevance: 3 - the asserted lock is not always enough
- words: 100

What do the kernel page table range walkers assert about locks, against what
does that not protect, when does a walker need memory hotplug excluded as well
and in which order, and when is adding that exclusion wrong? Start from
`walk_kernel_page_table_range()`.

## pagetable.lazy-mmu-api: Lazy MMU mode API

- section: Lazy MMU mode
- relevance: 4 - generic wrappers replaced direct calls to the arch hooks
- words: 100

Which functions enter, leave, pause and resume the lazy MMU mode, where is the
nesting state kept, what does a nested leave do, what happens in interrupt
context, and which architectures implement the mode? Start from
`lazy_mmu_mode_enable()` in `include/linux/pgtable.h`.

## pagetable.lazy-mmu-usage: Lazy MMU hazards

- section: Lazy MMU mode
- relevance: 4 - invisible on the common configurations
- words: 100

What usage inside a lazy MMU section is unsafe (reads after writes, sleeping,
allocation, leaving on an error path, calling the architecture hooks
directly), what is the correct form of each, and where do the bugs show?

# Changing the implementation

## pagetable.page-table-check-hooks: Page table check hooks

- section: What a change must preserve
- relevance: 3 - a new set or clear helper has to call them
- words: 80

What does the page table checker verify, which hooks must an architecture's or
a new generic set and clear helper call, and what did it catch in PTE batching?
Start from `mm/page_table_check.c`.

## pagetable.arch-helper-change: Adding an architecture helper

- section: What a change must preserve
- relevance: 3 - generic fallback, override convention, document and test
- words: 80

What does adding or changing a page table helper involve besides the helper:
the generic fallback and how an architecture overrides it, the document that
lists the helpers, and the boot-time test? Start from
`Documentation/mm/arch_pgtable_helpers.rst` and `mm/debug_vm_pgtable.c`.

## pagetable.zeropage-compare: Comparing page contents

- section: What a change must preserve
- relevance: 2 - one architecture's metadata
- words: 60

When deciding that a page can be replaced by a shared page with the same
contents, which helper must compare them, what is unsafe, and why? Start from
`pages_identical()`.
