# Questions: MM Page Table Operations

- guide: mm-pagetable.md
- title: MM Page Table Operations

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/mm-pagetable-measurement.md` is
the wider set the readers were measured on and `catalogue/mm-pagetable-measurement-results.md`
says what they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## pagetable.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## pagetable.core-files: Core files

- section: Finding your way
- relevance: 4 - helpers and whole mechanisms have moved between files

A table and nothing else, job to file: generic accessors; typed helpers for non-present entries;
swap entry encoding; generic fallbacks for architecture helpers; user fault, zap and fork copy;
protection change; page table move; the callback walker; the reverse-map walker; mmu_gather;
reclaim of empty PTE tables; the page table checker. Where a reader is likely to look for a file
that does not exist in this tree, say so in the row.

## pagetable.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to the function to start reading from: map and lock a PTE table;
walk a range with callbacks; walk to the one folio at an address; visit every mapping of a
folio; zap a range of one VMA; change protection over a range; insert a PFN or a page from a
driver; apply a function to each PTE of a kernel range; free the page tables of an unmapped
range. Give the current name where it has changed. Do not describe what the functions do inside.

# Userfaultfd, soft-dirty and special bits

## pagetable.uffd-bit: The userfaultfd entry bit

- section: Userfaultfd, soft-dirty and special bits
- relevance: 5 - the accessors were renamed and the bit gained a second meaning

What does this tree call the software bit that records userfaultfd protection in a present entry
and in a swap-format entry, and its accessors? Give the pattern of the accessor names, not every
accessor. Which userfaultfd modes use the bit, and how must code decide which mode an entry with
the bit set is in? Start from `include/linux/userfaultfd_k.h`.

## pagetable.soft-dirty-support: Soft-dirty support test

- section: Userfaultfd, soft-dirty and special bits
- relevance: 3 - a compile-time test is wrong where support is found at run time

How must code ask whether soft-dirty tracking works on the running system, and what does that test
depend on? What do `pte_mksoft_dirty()` and `pte_soft_dirty()` do on hardware without the bit?

## pagetable.special-bit: Special entries and normal-page lookup

- section: Userfaultfd, soft-dirty and special bits
- relevance: 4 - decides whether a walker sees a page at all

What does a special entry tell core mm that it must not do? How do `vm_normal_page()`,
`vm_normal_page_pmd()` and `vm_normal_page_pud()` decide what is a normal page where the level or
the architecture has no special bit? Which hook can return a page for a special entry? Start from
`__vm_normal_page()`.

## pagetable.special-usage: Marking entries special

- section: Userfaultfd, soft-dirty and special bits
- relevance: 4 - a special entry hides a refcounted folio from every walker

What are the requirements for setting the special bit in a PTE, PMD or PUD entry that maps a folio
or a raw PFN, in order to assure safe usage? Which functions build the entry for a refcounted
folio, and which for a raw PFN? Start from `insert_pmd()` in `mm/huge_memory.c`.

## pagetable.vma-flag-bits: Clearing userfaultfd protection from entries

- section: Userfaultfd, soft-dirty and special bits
- relevance: 3 - the flag and the entries are cleared in different places

What must be cleared from the entries of a VMA that stops being userfaultfd write-protected or
read-write-protected, and in which kinds of entry? What ties that clearing to the clearing of the
VMA flag? Start from `userfaultfd_clear_vma()`.

## pagetable.uffd-mremap-merge: Userfaultfd state after a move

- section: Userfaultfd, soft-dirty and special bits
- relevance: 5 - a VMA flag that disagrees with its entries breaks userfaultfd silently

What are the requirements for resetting the userfaultfd context of the VMA that `copy_vma()`
returns, in order to assure safe usage? Which entries of that VMA has `move_page_tables()` visited?
Start from `mremap_userfaultfd_prep()` in `mm/userfaultfd.c`.

## pagetable.soft-dirty-on-move: Soft dirty on move

- section: Userfaultfd, soft-dirty and special bits
- relevance: 4 - two dirty bits with different audiences

When an entry is moved to a new address, what must the code do with the soft-dirty bit, and what
with the hardware dirty bit? Name in-tree code that shows it. Start from `move_ptes()` in
`mm/mremap.c`.

# Present entry state

## pagetable.write-dirty-combinations: Writable and dirty combinations

- section: Present entry state
- relevance: 5 - one combination loses data and a similar one is normal

What are the requirements for the dirty bit of a present entry that is writable or is made
writable, for each kind of mapping, in order to assure safe usage? Which check enforces each
requirement? Start from `can_change_pte_writable()` in `mm/mprotect.c`.

## pagetable.young-dirty: Accessed with dirty

- section: Present entry state
- relevance: 3 - reviewers flag a legal state

Does `pte_mkdirty()` set the accessed bit? Does any code require that a dirty entry is also
accessed? Which code sets the accessed bit of the entry that a fault installs?

## pagetable.lazyfree-pte: Lazily freed entries

- section: Present entry state
- relevance: 3 - the state looks like a bug and is the design

What state does MADV_FREE deliberately leave an entry in, what happens on the next write with
and without hardware dirty tracking, and how does reclaim find out the page was written again?
Start from `madvise_free_pte_range()`.

## pagetable.uffd-rwp-protnone: NUMA and userfaultfd protnone entries

- section: Present entry state
- relevance: 4 - two mechanisms share one encoding

Which mechanisms use a present entry with no access permission in an accessible VMA, and how does
code tell their entries apart? What must a path that rebuilds such an entry keep? Name two paths
that show it. Start from `pte_protnone()` and `change_present_ptes()`.

## pagetable.numa-scan-protnone: NUMA scan of no-access entries

- section: Present entry state
- relevance: 4 - a scan that rewrites an entry which already has no access may change what the entry stands for

What does a NUMA scan do with a present entry that already has no access permission? Start from
`change_present_ptes()`.

## pagetable.vm-write-gate: Writable entries and VM_WRITE

- section: Present entry state
- relevance: 4 - permissions can change between lookup and install

What are the requirements for setting the write bit in an entry that is being built, with respect
to the VMA's flags, in order to assure safe usage? At what point must the code read the VMA's
flags? What are the requirements when the write bit comes from saved state, such as a write
migration entry or a huge PMD that is being split?

## pagetable.entry-read-write: Reading and writing entries

- section: Present entry state
- relevance: 4 - a plain dereference is sometimes a bug and sometimes fine

What does `ptep_get()` guarantee about the value it returns, and when must code use
`ptep_get_lockless()` in its place? What must a caller of `ptep_get_lockless()` recheck?

## pagetable.pte-direct-read: Direct read of a PTE

- section: Present entry state
- relevance: 4 - a reviewer has to tell a direct read that is a bug from one that is correct

What are the requirements for code that reads a PTE by dereferencing the pointer and not through
`ptep_get()`, in order to assure safe usage? Name in-tree code that shows it.

## pagetable.atomicity: Atomic updates

- section: Present entry state
- relevance: 4 - hardware writes accessed and dirty bits under you

Which bits can hardware change in a present entry while software holds the page table lock? What
are the requirements for code that reads a present entry, changes the value and writes it back, in
order to assure safe usage? Start from `ptep_modify_prot_start()`.

## pagetable.zeropage-compare: Comparing page contents

- section: Present entry state
- relevance: 2 - one architecture's metadata

What are the requirements for comparing the contents of two pages, when code decides that one page
can replace the other, in order to assure safe usage? What does `pages_identical()` compare? Start
from `pages_identical()`.

# Non-present entries

## pagetable.nonpresent-api: Typed non-present entries

- section: Non-present entries
- relevance: 5 - the whole family of helpers was renamed

Which type and which family of helpers decode a non-present PTE or PMD and test its kind? What
does the decode return for a present entry and for an empty one? Start from
`include/linux/leafops.h`; if the tree has no such header, say so.

## pagetable.nonpresent-kinds: Kinds of non-present entry

- section: Non-present entries
- relevance: 5 - each kind has its own rules and they are easy to conflate

One table of the kinds of non-present entry in `enum softleaf_type`: what each stands for, whether
it carries a PFN, whether it holds a folio reference and a mapcount, and whether a PMD can hold
it. What must `zap_nonpresent_ptes()` do for each kind? Start from `enum softleaf_type` and
`zap_nonpresent_ptes()`.

## pagetable.nonpresent-dispatch: Dispatching on kind

- section: Non-present entries
- relevance: 5 - grouping kinds that carry a PFN is the mistake that leaks or double-puts a folio

What are the requirements for code that branches on the kind of a non-present entry in order to
assure safe usage? Which kinds of entry carry a PFN, and what must code do differently for each of
them? Name in-tree code that shows it. Start from `check_pte()` in `mm/page_vma_mapped.c` and
`copy_nonpresent_pte()`.

## pagetable.markers: Marker entries

- section: Non-present entries
- relevance: 4 - markers carry no page and each kind faults differently

What does a fault on each kind of marker entry do, which markers survive a zap that was not told
to drop them, and what decides whether a marker is copied at fork? Start from
`handle_pte_marker()` and `zap_nonpresent_ptes()`.

## pagetable.nonpresent-has-pfn: Folio behind a migration entry

- section: Non-present entries
- relevance: 4 - sharing the property does not make kinds interchangeable

What does `softleaf_to_folio()` require of the folio behind a migration entry, and what does it do
when that does not hold? What does a migration entry in a page table guarantee about the lifetime
of the folio? Start from `softleaf_to_folio()`.

## pagetable.softleaf-pfn-offset: PFN in the offset field

- section: Non-present entries
- relevance: 4 - code that takes the PFN from the wrong field looks up the wrong page

How does `softleaf_to_pfn()` get the PFN from a non-present entry, and what else can the offset
field of such an entry hold? Start from `softleaf_to_pfn()`.

## pagetable.swap-pte-bits: Bits in a swap-format entry

- section: Non-present entries
- relevance: 4 - the present and swap forms use different bit positions

Which software bits can a swap-format PTE carry? What are the requirements for the accessors that
code uses on a swap-format PTE in order to assure safe usage? Which helpers that compare
swap-format entries ignore those bits, and which do not? Start from `pte_swp_clear_flags()`.

## pagetable.migration-ad-bits: A/D bits in migration entries

- section: Non-present entries
- relevance: 3 - the bits are optional and restoring dirty has a condition

When does a migration entry remember that the page was young or dirty and when can it not, and
under what condition is dirty put back when the entry is removed? What keeps dirtiness from
being lost when the entry cannot carry it? Start from `migration_entry_supports_ad()`.

## pagetable.nonpresent-to-present: Restoring software bits

- section: Non-present entries
- relevance: 5 - a lost bit breaks userfaultfd or checkpoint restore silently

When a non-present entry is replaced by a present one, which software bits must the code carry
across, and with which accessors? What more must the code do in a VMA that is userfaultfd
read-write-protected? Name the sites that do it. Start from `do_swap_page()` and
`remove_migration_pte()`.

## pagetable.nonpresent-rewrite: Rewriting a non-present entry

- section: Non-present entries
- relevance: 3 - the swap-side writers differ and some drops are deliberate

When one non-present entry is rewritten as another, at fork or on a protection change, which
software bits does the code keep and which does it drop, for each kind of entry? Where do the PTE
and PMD paths differ? Start from `copy_nonpresent_pte()` and `change_softleaf_pte()`.

## pagetable.present-only-accessors: Present-only page accessors

- section: Non-present entries
- relevance: 5 - the wrong accessor turns swap bits into a page pointer

What are the requirements for the entry passed to `pmd_folio()`, to `pte_page()` and to the other
functions that convert an entry to a PFN, a page or a folio, in order to assure safe usage? Which
function returns the folio behind a non-present PMD, and which the folio behind a non-present PTE?
Start from `pmd_folio()` and `pmd_to_softleaf_folio()`.

# Mapping and locking a table

## pagetable.ptdesc: Page table descriptor

- section: Mapping and locking a table
- relevance: 4 - page table pages have their own type and helpers now

What is a `struct ptdesc` in relation to the table's `struct page`, why can constructing a PTE
or PMD table fail, and what must a path that frees a table not skip? Do not list its members.
Start from `pagetable_pte_ctor()`.

## pagetable.split-locks: Page table locks

- section: Mapping and locking a table
- relevance: 4 - which lock covers which level depends on configuration

Which lock protects the entries of a PTE table, a PMD table, a PUD table and the levels above? How
does code that needs the locks of two levels take them? What do `pmd_lock()` and `pud_lock()`
leave the caller to recheck?

## pagetable.pte-lockptr-argument: Argument to the lock lookup

- section: Mapping and locking a table
- relevance: 4 - the lookup reads the PMD entry it is given, and that entry can change

What are the requirements for the `pmd` argument of `pte_lockptr()` in order to assure safe usage?

## pagetable.pte-map: Mapping a PTE table

- section: Mapping and locking a table
- relevance: 5 - which helper to use, and what NULL means, decide whether a walk is safe

A table of the helpers that map a PTE table: whether each takes the lock, and what it guarantees
about the table staying attached. When do they return NULL, and what must a caller do then? What
must a caller of `pte_offset_map_rw_nolock()` recheck after it takes the lock? Start from the
comment above `pte_offset_map_lock()` in `mm/pgtable-generic.c`.

## pagetable.pte-map-rcu: Between map and unmap

- section: Mapping and locking a table
- relevance: 4 - the mapping holds more than a pointer

What does a successful `pte_offset_map()` hold until `pte_unmap()`, and what may code therefore
not do in between? What does the holder see, on reads and on writes, in a table that was detached
in the meantime?

## pagetable.pte-unmap-pointer: Pointer given to unmap

- section: Mapping and locking a table
- relevance: 3 - invisible on 64-bit, wrong page unmapped on one configuration

What are the requirements for the pointer passed to `pte_unmap()` and to `pte_unmap_unlock()` in
order to assure safe usage? In what order must two PTE table mappings be released? On which
configurations does `pte_unmap()` use the pointer?

## pagetable.pmd-lock-accepts: Huge PMD lock helper

- section: Mapping and locking a table
- relevance: 5 - success does not mean the PMD is present

For which PMD values does `pmd_trans_huge_lock()` succeed, what must a caller therefore check
before treating the PMD as mapping a folio, and what else can a present huge PMD be besides a
normal folio? Name code that gets it right.

## pagetable.populate-lock-rule: Locks for each operation

- section: Mapping and locking a table
- relevance: 5 - the rmap locks allow less than people assume

For traversing page tables, installing an entry, zapping entries and freeing a table, which of the
mmap lock, a per-VMA lock and the reverse-map locks must code hold? What may code that holds only
a reverse-map lock do to page tables? Start from `Documentation/mm/process_addrs.rst`.

## pagetable.fault-lock-order: Fault handler lock order

- section: Mapping and locking a table
- relevance: 3 - an ABBA deadlock that lockdep only sees with freezing

Which locks are held when a file's `fault` and `page_mkwrite` handlers are called? Which
filesystem freeze protection may those handlers take, and which may they not take? Start from
`vmf_can_call_fault()` and `filemap_page_mkwrite()`.

## pagetable.write-path-fault: User faults during buffered writes

- section: Mapping and locking a table
- relevance: 3 - a fault on the user buffer taken under a folio lock can deadlock with the fault handler

How does a buffered write avoid a page fault on the user's buffer while it holds a folio lock, and
what does it do when the copy from the user's buffer fails? Start from `generic_perform_write()`.

# The callback walker

## pagetable.walk-ops: Walker callbacks

- section: The callback walker
- relevance: 4 - which callback fires for what decides correctness

For which entries does the page walker call each callback of `struct mm_walk_ops`, and when does
it descend from a PMD to PTEs? What does the `depth` argument of `pte_hole` mean? Start from
`walk_pmd_range()`.

## pagetable.walk-install-pte: Walks that install entries

- section: The callback walker
- relevance: 4 - a walk that installs entries behaves differently on empty ranges and has its own entry points

What does supplying `install_pte` in a `struct mm_walk_ops` change in what the walker does, and
which entry points of the walker accept it? Start from `walk_pmd_range()`.

## pagetable.walk-entry-points: Walker entry points

- section: The callback walker
- relevance: 4 - several variants with different checks

A table of the page walker's entry points to choose between: the scope of the walk, what the
caller must hold, and whether the walk calls `test_walk`. What do the entry points for a kernel
range leave their caller to protect against?

## pagetable.walk-lock: Walker locking

- section: The callback walker
- relevance: 4 - the field makes the walker assert or take locks

For each value of `enum page_walk_lock`, what does the walker assert about the mmap lock, and what
does it do or assert about each VMA?

## pagetable.walker-pmd-entry: PMD callbacks and huge entries

- section: The callback walker
- relevance: 5 - a callback that ignores huge PMDs skips data or crashes

What must a `pmd_entry` callback that walks PTEs itself do about a huge PMD, a non-present PMD and
a failed mapping of the PTE table? What does the walker do to a huge PMD before it descends to
PTEs?

## pagetable.walker-returns: Return values and skipped VMAs

- section: The callback walker
- relevance: 3 - a positive return and a skipped VMA both look like success to the caller

What do zero, positive and negative returns from an entry callback do to the walk and to the
caller's result, and how do the returns of `test_walk` differ? Which VMAs does `walk_page_range()`
skip when no `test_walk` is supplied?

## pagetable.walker-again-usage: Retrying from a callback

- section: The callback walker
- relevance: 4 - an unbounded retry spins while a migration is in flight

What are the requirements for a `pmd_entry` callback that sets `ACTION_AGAIN` in order to assure
safe usage? What does the walker itself do, for users of `pte_entry`, when it cannot map the PTE
table? Start from `walk_pte_range()`.

# The reverse-map walker and GUP-fast

## pagetable.pvmw-state: Reverse-map walk state

- section: The reverse-map walker and GUP-fast
- relevance: 4 - a callback that leaves the loop wrongly unlocks twice or leaks a mapping

What does a caller hold between a true return from `page_vma_mapped_walk()` and the next call, and
what may it therefore not do? What are the requirements for calling `page_vma_mapped_walk_done()`
and `page_vma_mapped_walk_restart()` in order to assure safe usage? Start from
`page_vma_mapped_walk()`.

## pagetable.pvmw-nonpresent: Entries the reverse-map walk returns

- section: The reverse-map walker and GUP-fast
- relevance: 5 - a returned PTE is not always present

With and without the migration flag, which kinds of PTE can the reverse-map walk return true
for, and which kinds of PMD when it returns with no PTE set? Which kinds does it never return?
Start from `check_pte()`.

## pagetable.pvmw-accessor-usage: Accessors in reverse-map callbacks

- section: The reverse-map walker and GUP-fast
- relevance: 5 - present-entry accessors read garbage from a swap-format entry

What are the requirements for the accessors that a callback uses on the entry
`page_vma_mapped_walk()` returned, in order to assure safe usage? How does a callback get the PFN,
the writability and the software bits from a non-present entry? Name a callback that handles
present and non-present entries. Start from `try_to_migrate_one()` and `folio_referenced_one()`.

## pagetable.gup-fast-walk: Lockless walk by GUP-fast

- section: The reverse-map walker and GUP-fast
- relevance: 4 - the rules every table-freeing path has to respect

What keeps a page table from being freed while GUP-fast walks it, and what does that require of a
path that frees a table? What does `gup_fast_pte_range()` recheck after it takes a reference on a
folio? Start from `gup_fast_pte_range()`.

# PTE batching

## pagetable.batch-flags: Batch flags and default comparison

- section: PTE batching
- relevance: 5 - what a flag-less batch ignores is what makes writing it back unsafe

A table of the `fpb_t` flags that `folio_pte_batch_flags()` takes and what each makes it compare
or merge. With no flags, which bits may differ across a batch and which must match? What does
`folio_pte_batch_flags()` require of its `ptentp` argument? Start from `fpb_t` and
`__pte_batch_clear_ignored()` in `mm/internal.h`.

## pagetable.batch-helpers: Ranged PTE helpers

- section: PTE batching
- relevance: 4 - what each does to the bits that differ within a batch

For `set_ptes()` and the other helpers in `include/linux/pgtable.h` that act on a run of
consecutive PTEs, a table of what each does with bits that differ across the run. What does each
require of the run? Start from `set_ptes()` in `include/linux/pgtable.h`.

## pagetable.batch-writeback-usage: Writing a batch back

- section: PTE batching
- relevance: 5 - the first entry's permissions get stamped on the rest

What are the requirements for a caller that gets a count from `folio_pte_batch()` or
`folio_pte_batch_flags()` and then writes entries back, in order to assure safe usage? Name one
caller that passes `FPB_RESPECT_WRITE`, one that passes `FPB_MERGE_WRITE` and one that passes no
flags, and say how each meets the requirements. Start from `copy_present_ptes()`, `move_ptes()`
and `folio_unmap_pte_batch()`.

## pagetable.batch-bounds: Batch bounds

- section: PTE batching
- relevance: 5 - an uncapped count reads past the end of a page table

What must a caller of `folio_pte_batch()` guarantee about the `max_nr` it passes, and what does
the function cap by itself? Name in-tree code that computes `max_nr`.

## pagetable.large-folio-install: Large folio over populated PTEs

- section: PTE batching
- relevance: 4 - the wrong fallback livelocks with no warning

When a fault wants to map a large folio with several PTEs and finds some of them populated, what
must it do, for a file folio and for a fresh anonymous folio? What are the requirements for a
fault path that picks the folio order from a call to `pte_range_none()` made without the page
table lock, in order to assure safe usage? Start from `pte_range_none()` and `finish_fault()`.

# Zapping and freeing tables

## pagetable.zap-api: Zap functions

- section: Zapping and freeing tables
- relevance: 5 - every name in this family changed

A table of the zap functions to choose between: a range within one VMA, the same with a caller's
gather, the one for drivers with PFN mappings, the OOM reaper's, and the function they all reach;
for each, what the caller must already have done or hold. What does a zap leave in place when it
is passed no `struct zap_details`? Start from `unmap_vmas()`.

## pagetable.mmu-gather-api: The mmu_gather contract

- section: Zapping and freeing tables
- relevance: 4 - the ordering is the point, not the fields

What ordering does a `struct mmu_gather` guarantee between clearing entries, flushing the TLB, and
freeing pages and tables? What does `tlb_finish_mmu()` do when another thread is gathering on the
same mm? Do not list the structure's members. Start from `tlb_finish_mmu()`.

## pagetable.mmu-gather-start: Starting a gather

- section: Zapping and freeing tables
- relevance: 4 - the function that starts a gather decides which calls the caller still has to make

Of `tlb_gather_mmu()`, `tlb_gather_mmu_fullmm()` and `tlb_gather_mmu_vma()`, which is used when,
and what does each leave for its caller to do? Start from `tlb_gather_mmu_vma()`.

## pagetable.table-free: Table freeing and lockless walkers

- section: Zapping and freeing tables
- relevance: 5 - a table freed by the wrong mechanism is a use-after-free in GUP-fast

After an upper-level entry is cleared, what must a path that frees the table page call so that
lockless walkers are out of the table, and what does each such function wait for? What does
`tlb_remove_table()` do when it cannot allocate a batch? Start from `tlb_remove_table()` in
`mm/mmu_gather.c` and `pte_free_defer()`.

## pagetable.empty-table-reclaim: Reclaiming empty PTE tables

- section: Zapping and freeing tables
- relevance: 5 - a PMD entry can vanish under a reader of a live mm

Outside unmap and exit, which paths detach and free a PTE table from a live mm, which locks does
each hold and which does it conspicuously not hold, and what makes that safe for someone who has
the table mapped? Start from `zap_pte_range()` and `retract_page_tables()`.

## pagetable.recheck-after-relock: Decisions across a lock drop

- section: Zapping and freeing tables
- relevance: 4 - entries can be repopulated while the lock is dropped

In the zap path, when may a PTE table be freed without looking at it again, and when must it be
rescanned and under which locks? State the general rule for a decision taken before a page table
lock was dropped. Start from `zap_pte_table_if_empty()`.

## pagetable.free-pgtables: Freeing tables at unmap

- section: Zapping and freeing tables
- relevance: 4 - it takes no page table lock and may not use RCU

What does `free_pgtables()` require to have been done before it is called, and which locks does it
take? What may code that does not own the mm do with the page tables of a VMA once the VMA is
detached? Start from `free_pgtables()`.

## pagetable.vma-lock-and-tables: mmap write lock and tables

- section: Zapping and freeing tables
- relevance: 5 - the race has shipped, and nothing in a diff shows it

What are the requirements for code that holds the mmap write lock and reads or changes page
tables, in order to assure safe usage? Which operations change page tables while they hold only a
per-VMA lock? Start from `collapse_huge_page()` and `zap_vma_range_batched()`.

# TLB flushing

## pagetable.tlb-flush-rules: Transitions that need a flush

- section: TLB flushing
- relevance: 5 - a missed flush leaves stale write access

Which changes to a present entry require a TLB flush before other code relies on them, and which
do not? What must a path do that only makes an entry more permissive? Start from
`ptep_set_access_flags()`.

## pagetable.tlb-flush-before-unlock: Flush before dropping the lock

- section: TLB flushing
- relevance: 4 - some flushes cannot wait for the end of the gather

In which cases must the TLB be flushed before the page table lock is released, and not when the
gather finishes? What relies on the flush in each case? Which locks must `move_ptes()` hold until
the flush? Start from `zap_pte_range()` and `move_ptes()`.

## pagetable.batched-flush-pending: Reclaim's deferred flushes

- section: TLB flushing
- relevance: 4 - entries look clear while a stale TLB entry still exists

What are the requirements for a loop that infers TLB state from entry contents, for when and under
which lock it calls `flush_tlb_batched_pending()`, in order to assure safe usage? What must such a
loop do after it drops and retakes the page table lock? Start from `flush_tlb_batched_pending()`.

# Kernel tables and lazy MMU mode

## pagetable.lazy-mmu: Lazy MMU mode

- section: Kernel tables and lazy MMU mode
- relevance: 4 - the bugs show on four architectures only, so nobody's test catches them

What may code assume about page table reads and writes between `lazy_mmu_mode_enable()` and
`lazy_mmu_mode_disable()`? What are the requirements for code inside such a section in order to
assure safe usage? How do nested sections and interrupts behave? Start from
`lazy_mmu_mode_enable()` in `include/linux/pgtable.h`.

## pagetable.kernel-populate-sync: Populating kernel tables

- section: Kernel tables and lazy MMU mode
- relevance: 4 - a new top-level entry may not reach other page tables

What must code that installs a new top-level entry in the kernel's page tables do so that the
entry reaches the page tables of every process? Which helpers in `include/linux/pgalloc.h` do
that, and which do not? Start from `include/linux/pgalloc.h` and `__apply_to_page_range()`.

## pagetable.kernel-walk-hotplug: Walking kernel tables

- section: Kernel tables and lazy MMU mode
- relevance: 3 - the asserted lock is not always enough

What does `walk_kernel_page_table_range()` assert about locks? When must a caller also exclude
memory hotplug, and in which order must it take the two locks? Start from
`walk_kernel_page_table_range()`.

# The page table checker

## pagetable.page-table-check-hooks: Page table check hooks

- section: The page table checker
- relevance: 3 - a new set or clear helper has to call them

What does the page table checker in `mm/page_table_check.c` detect? What must a new set or clear
helper, generic or of one architecture, call so that the checker keeps working? Start from
`mm/page_table_check.c`.

# Model gaps

## pagetable.model-gaps: Other mistakes models make

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
