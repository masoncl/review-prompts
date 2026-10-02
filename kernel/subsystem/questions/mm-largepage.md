# Questions: MM Large Folios, THP, and Hugetlb

- guide: mm-largepage.md
- title: MM Large Folios, THP, and Hugetlb

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/mm-largepage-measurement.md` is
the wider set the readers were measured on and `catalogue/mm-largepage-measurement-results.md`
says what they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## largepage.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## largepage.core-files: Core files

- section: Finding your way
- relevance: 4 - hugetlb and THP are each spread over several files

A table and nothing else, job to file: the transparent huge page fault, PMD and split code; the
collapse daemon; the hugetlb pool and fault code; hugetlb's sysfs, sysctl, CMA, cgroup and struct
page optimisation parts; hugetlbfs; the rmap calls for each mapping level; large folio swap-in;
memory failure handling. Where a reader is likely to look for a file that does not exist in this
tree, say so in the row. Start from `mm/huge_memory.c` and `mm/hugetlb.c`.

## largepage.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to the function to start reading from: fault in an anonymous
PMD-sized folio; fault in a smaller anonymous large folio; split a huge PMD; split a large folio;
collapse small pages into a large folio; handle a hugetlb fault; allocate a hugetlb folio; reserve
hugetlb pages at mmap; handle a hardware memory error. Give the current name where it has
changed.

# Large folio state

## largepage.kinds: Kinds of large folio

- section: Large folio state
- relevance: 4 - each kind is tested for differently and handled differently

Of `folio_test_large()`, `folio_test_pmd_mappable()`, `folio_test_large_rmappable()` and
`folio_test_hugetlb()`, which is used when, and for which kinds of large folio does each return
true? Start from `folio_test_large()` and `folio_test_pmd_mappable()`.

## largepage.state-tracking: Per-folio and per-page state

- section: Large folio state
- relevance: 5 - checking the wrong struct page reads stale state

For anonymous exclusivity, hardware poison, dirty, accessed or young, the reference count and the
mapcount of a large folio, a table of whether the state is kept per folio, per page or only in
the page table entry, and where.

## largepage.anon-exclusive: Anonymous exclusive flag

- section: Large folio state
- relevance: 4 - which page carries it depends on how the folio is mapped

On which struct page is `PG_anon_exclusive` kept for a PTE-mapped large folio, for a PMD-mapped
one and for hugetlb? What are the requirements for code that tests, sets or clears
`PG_anon_exclusive` on a large folio in order to assure safe usage? What must fork, a PMD split
and an unmap for migration do with it? Start from `PG_anon_exclusive` and
`__folio_add_anon_rmap()`.

## largepage.mapcount-consistency: Large mapcount lock

- section: Large folio state
- relevance: 3 - the lock covers fewer fields than its name suggests

Which of a large folio's mapcount fields does `folio_lock_large_mapcount()` keep stable while it
is held, and which not? What are the requirements for code that reads those fields to decide
whether it is the only mapper of the folio, in order to assure safe usage? Start from
`__wp_can_reuse_large_anon_folio()`.

## largepage.rmap-api: Rmap calls by mapping level

- section: Large folio state
- relevance: 4 - the wrong level corrupts the counts

Of the PTE, PMD and PUD forms of the rmap add, duplicate and remove functions, which is used when?
What are the requirements for the level a caller passes, with respect to how the folio is mapped,
in order to assure safe usage? Which functions does hugetlb use in their place? Start from
`folio_add_anon_rmap_ptes()` and `hugetlb_add_anon_rmap()`.

## largepage.second-page-flag-updates: First tail page flags

- section: Large folio state
- relevance: 4 - a lost update on a flag nobody was touching

What else can write the flags word of the page that holds the folio flags declared with
`FOLIO_SECOND_PAGE`? What are the requirements for using the setters and clearers that
`__FOLIO_SET_FLAG` and `__FOLIO_CLEAR_FLAG` declare for such a flag, in order to assure safe
usage? Start from `FOLIO_SECOND_PAGE` and `__FOLIO_SET_FLAG` in `include/linux/page-flags.h`.

# Huge PMD entries

## largepage.pmd-leaf-tests: Huge PMD tests

- section: Huge PMD entries
- relevance: 4 - the tests differ in what they match besides a transparent huge page

Of `pmd_trans_huge()`, `pmd_leaf()` and `pmd_is_huge()`, which is used when, and for which kinds
of PMD entry does each return true? What are the requirements for code that uses one of them to
decide that a PMD maps a transparent huge page, in order to assure safe usage?

## largepage.pmd-softleaf: Non-present huge PMD entries

- section: Huge PMD entries
- relevance: 4 - walkers that assume a present entry dereference garbage

Which kinds of non-present entry can a huge PMD hold, and which helpers recognise and decode them?
What are the requirements for a page table walker that reads a PMD which may be a non-present huge
entry, in order to assure safe usage? Start from `pmd_is_migration_entry()` and
`set_pmd_migration_entry()`.

## largepage.pmd-locking: Locking a huge PMD

- section: Huge PMD entries
- relevance: 4 - the PMD can change between the test and the lock

For which PMD entries does `pmd_trans_huge_lock()` take the lock and return with it held, and what
does it leave its caller to check? What must code recheck after it read a PMD without the lock?
Start from `pmd_trans_huge_lock()` and `pmd_lock()`.

## largepage.pgtable-deposit: Deposited page table

- section: Huge PMD entries
- relevance: 4 - a missing withdraw leaks a page table and a wrong one corrupts the count

Which huge PMD mappings keep a preallocated PTE table deposited, and how does code ask whether a
given huge PMD has one? What are the requirements for a zap, a split and a move of a huge PMD,
with respect to the deposited table and the mm's count of page tables, in order to assure safe
usage? Start from `pgtable_trans_huge_deposit()` and `zap_huge_pmd()`.

## largepage.pmd-split: Splitting a huge PMD

- section: Huge PMD entries
- relevance: 5 - what is left behind differs for every kind of mapping

What does `__split_huge_pmd_locked()` leave in the page table for each kind of huge PMD entry that
it can be given? What must the caller hold, and when does the split do nothing? Start from
`__split_huge_pmd_locked()`.

## largepage.pmd-split-accounting: PMD split accounting

- section: Huge PMD entries
- relevance: 5 - references, rmap and exclusivity all change representation here

In the anonymous case of `__split_huge_pmd_locked()`, how do the folio's reference count, mapcount
and `PG_anon_exclusive` change when a huge PMD becomes PTEs, and what does the `freeze` argument
change about that? In what order must the huge PMD be invalidated and the page table be installed,
and what relies on that order? Start from `__split_huge_pmd_locked()`.

## largepage.unmap-pmd-mapped: Unmapping a PMD-mapped folio

- section: Huge PMD entries
- relevance: 4 - the assertion fires only for the rare PMD-mapped case

What are the requirements for calling `try_to_unmap()` on a folio that may be mapped by a PMD, in
order to assure safe usage, and what does `try_to_unmap_one()` do when they are not met? What does
`TTU_SPLIT_HUGE_PMD` change? Start from `TTU_SPLIT_HUGE_PMD` and `try_to_unmap_one()`.

## largepage.pmd-cow: Huge PMD write fault

- section: Huge PMD entries
- relevance: 4 - the reuse test is a security boundary

On a write or unshare fault on an anonymous huge PMD, when is the folio reused in place, which
locks and counts does that test depend on, and what is done when it cannot be reused? Start from
`do_huge_pmd_wp_page()`.

# Allocating large anonymous folios

## largepage.allowable-orders: Allowed orders for a VMA

- section: Allocating large anonymous folios
- relevance: 4 - every fault, collapse and smaps path asks this one function

Which kinds of caller does `thp_vma_allowable_orders()` distinguish, and how do its answers to
them differ? Which orders can it return for an anonymous mapping, a file mapping and a DAX or PFN
mapping? What does it leave for its caller to check? Start from `thp_vma_allowable_orders()`.

## largepage.anon-mthp-fault: Smaller anonymous large folios

- section: Allocating large anonymous folios
- relevance: 4 - decides when a fault falls back to a single page

How does an anonymous fault below PMD size choose a folio order, what makes it skip an order or
fall back to a single page, and what does userfaultfd change? Start from `alloc_anon_folio()` in
`mm/memory.c`.

## largepage.anon-alloc-site: Adding an allocation site

- section: Allocating large anonymous folios
- relevance: 4 - several steps are easy to leave out and the counters are not where a reader looks

What must a code path that allocates and maps a large anonymous folio do between charging the
folio and making it visible in a page table, and what must an error path after the charge undo?
What do `map_anon_folio_pmd_nopf()` and `map_anon_folio_pte_nopf()` leave to their callers? Start
from `map_anon_folio_pmd_nopf()`, `map_anon_folio_pte_nopf()` and `do_huge_pmd_anonymous_page()`.

# Splitting a folio

## largepage.split-api: Split entry points

- section: Splitting a folio
- relevance: 5 - the variants differ in target order, uniformity and what stays locked

A table of the functions that split a large folio, to choose between: the target order, whether
the pieces are all one size, where the pieces are put, and which piece stays locked and referenced
for the caller. What does each require of the folio's mappings before the call, and what does each
leave for its caller to do afterwards? Start from `split_huge_page()`, `folio_split()` and
`folio_split_unmapped()`.

## largepage.split-preconditions: Split preconditions

- section: Splitting a folio
- relevance: 5 - violated preconditions fail only under load

What must the caller of `folio_split()` or `split_huge_page()` hold and guarantee before the call?
Which of those requirements does the split check for itself, and which does it trust? Start from
`folio_check_splittable()`.

## largepage.split-refcount: Reference counts at split

- section: Splitting a folio
- relevance: 5 - one stray reference makes every split fail

Which reference count must a folio have for a split to go ahead, and where is that checked? Which
extra references that make the split fail go away without action by the caller? Start from
`folio_expected_ref_count()` and `folio_ref_freeze()`.

## largepage.split-errors: Split return values

- section: Splitting a folio
- relevance: 4 - callers must tell transient from permanent failure

Which error values can a folio split return, and what does each tell the caller about the state of
the folio and about trying again? Which error does `folio_check_splittable()` return for a folio
that was just truncated, and which for the huge zero folio?

## largepage.split-min-order: Minimum order of a mapping

- section: Splitting a folio
- relevance: 4 - a split to order zero fails on some filesystems

What does a folio split do when the target order is below the minimum folio order of the file's
mapping? What does `min_order_for_split()` return for a folio that was just truncated? What are
the requirements for a caller's use of the folio after a successful split, in order to assure safe
usage? Start from `min_order_for_split()`.

## largepage.split-state-propagation: State carried to the pieces

- section: Splitting a folio
- relevance: 4 - a flag left behind is a silent corruption

When `__split_folio_to_order()` makes new folios out of one, which state of the old folio needs
more than a copy of the first page's flags to reach each new folio? Which state does it not carry?
What must a change that adds per-folio state do there? Start from `__split_folio_to_order()`.

## largepage.split-invariants: Split lock order and freeze

- section: Splitting a folio
- relevance: 4 - the split is relied on from reclaim, truncate, migration and hwpoison

In what order does `__folio_split()` take its locks for an anonymous folio and for a file folio?
What does it keep frozen, and until when? Which folio keeps the caller's lock and reference? Start
from `__folio_split()`.

## largepage.split-retry-usage: Retrying a failed split

- section: Splitting a folio
- relevance: 4 - the livelock only shows with several tasks on one folio

What are the requirements for a loop that takes a reference on a large folio, locks it, calls a
folio split and tries again on failure, in order to assure safe usage? Name in-tree callers that
lock the folio with a reference held and meet the requirements. Start from
`madvise_free_huge_pmd()` and `try_to_split_thp_page()`.

# Deferred split

## largepage.deferred-split-queue: Deferred split queue

- section: Deferred split
- relevance: 5 - the data structure and its lock have been replaced

Which structure holds the folios queued for deferred splitting, and which lock protects a folio's
entry on it? Which folios can be queued, and which never are? Start from `deferred_split_folio()`
and the `_deferred_list` field.

## largepage.deferred-split-alloc: Allocation sites and the queue

- section: Deferred split
- relevance: 4 - a new allocation site that skips the step cannot queue

What does `folio_memcg_alloc_deferred()` set up, and for which folio orders must an allocation
site call it? What does `deferred_split_folio()` do with a folio from a site that did not call it?
Start from `folio_memcg_alloc_deferred()`.

## largepage.deferred-split-queuers: Queueing for deferred split

- section: Deferred split
- relevance: 4 - callers of the rmap helpers must not queue again

Which code queues a folio for deferred splitting, and on what condition? What are the requirements
for a caller of `folio_remove_rmap_ptes()` or `folio_remove_rmap_pmd()`, with respect to the
deferred split queue, in order to assure safe usage? What must code that unmaps or moves a folio
without those functions do about the queue? Start from `__folio_remove_rmap()`.

## largepage.deferred-split-unqueue: Leaving the deferred split queue

- section: Deferred split
- relevance: 4 - unqueueing at the wrong time corrupts the list

When is a folio taken off the deferred split queue? What does `folio_unqueue_deferred_split()`
require of the folio's reference count? What must happen to the folio's queue entry before its
memory cgroup changes? Start from `folio_unqueue_deferred_split()` in `mm/internal.h`.

# Collapse

## largepage.khugepaged-overview: Collapse daemon structure

- section: Collapse
- relevance: 4 - the function names have changed

How does an mm get registered with the collapse daemon and dropped again? Which functions scan one
mm, one PMD range of anonymous memory and one range of a file? Start from `khugepaged_enter_vma()`
and `struct khugepaged_scan`.

## largepage.file-collapse-eligibility: File mappings eligible for collapse

- section: Collapse
- relevance: 4 - the condition has been reworked and old configuration names may be gone

Which file mappings may the collapse daemon turn into PMD-sized folios, and what does
`file_thp_enabled()` test to decide it? Start from `file_thp_enabled()` in `mm/huge_memory.c`.

## largepage.collapse-mthp: Collapse to smaller orders

- section: Collapse
- relevance: 4 - whether the daemon can build folios smaller than a PMD is tree-specific

Into which folio orders can the collapse daemon collapse anonymous memory? How does it choose the
order, and how do the limits on empty, swapped and shared PTEs apply to an order below PMD order?
Start from `collapse_scan_pmd()` and `collapse_max_ptes_none()`.

## largepage.collapse-mthp-install: Installing a smaller collapsed folio

- section: Collapse
- relevance: 4 - the steps that install a PMD mapping do not all apply to a folio mapped by PTEs

How does the collapse daemon install a collapsed anonymous folio of an order below PMD order, and
how does that differ from the way it installs a PMD-sized one? Start from `collapse_huge_page()`.

## largepage.collapse-anon-steps: Anonymous collapse locking

- section: Collapse
- relevance: 5 - the lock order and the revalidation are where the bugs are

In `collapse_huge_page()`, which locks are held, and in which mode, at each stage from allocation
to installing the new mapping? What must the code revalidate each time a lock was dropped and
retaken? Start from `collapse_huge_page()`.

## largepage.collapse-gup-fast: Collapse and lockless walkers

- section: Collapse
- relevance: 4 - a missing step lets GUP-fast use a freed page table

How does an anonymous collapse make sure that lockless page table walkers such as GUP-fast no
longer use the PTE table it is about to empty? What are the requirements for code that empties or
frees a PTE table in a collapse, with respect to lockless walkers, in order to assure safe usage?
Start from `pmdp_collapse_flush()` and `tlb_remove_table_sync_one()`.

## largepage.collapse-file: File collapse and rollback

- section: Collapse
- relevance: 4 - the rollback path is long

In a collapse of a file or shmem range, what state are the old folios and the page cache slots
in between the start and the point after which nothing can fail, what is rolled back on a
failure before it, and when are the page tables that map the range dealt with? Start from
`collapse_file()`.

# Page cache and swap

## largepage.pagecache-refs: Page cache references

- section: Page cache and swap
- relevance: 4 - a single put after removal leaks

How many references does the page cache hold on a large folio, and which function takes them? What
are the requirements for dropping those references when a large folio is removed from the page
cache, in order to assure safe usage? Start from `__filemap_add_folio()` and
`filemap_free_folio()`.

## largepage.isize-mapping: Mapping past end of file

- section: Page cache and swap
- relevance: 5 - over-mapping breaks SIGBUS semantics silently

What rule stops a large file folio from being mapped beyond the end of the file, by PTEs and by
a PMD, which mappings are exempt, and what does truncation do when it cannot split the folio?
Name the places that enforce the rule. Start from `filemap_map_pages()`, `finish_fault()` and
`folio_split_or_unmap()`.

## largepage.swapin: Large folio swap-in

- section: Page cache and swap
- relevance: 4 - a new path that checks and allocates separately reopens a race

What does `swap_cache_alloc_folio()` guarantee about the range the folio covers and about falling
back to a smaller order? What are the requirements for a path that allocates a folio for swap-in,
with respect to the swap cache, in order to assure safe usage? Start from `swapin_sync()` and
`swap_cache_alloc_folio()`.

# Hugetlb folios and the pool

## largepage.hugetlb-in-generic-code: Hugetlb in generic code

- section: Hugetlb folios and the pool
- relevance: 4 - generic folio code is wrong for hugetlb in several ways

What are the requirements for generic folio code that can be handed a folio for which
`folio_test_hugetlb()` is true, in order to assure safe usage? What must an rmap walk callback do
with such a folio? Start from `try_to_unmap_one()` and `try_to_migrate_one()`.

## largepage.hugetlb-type-usage: Testing for hugetlb

- section: Hugetlb folios and the pool
- relevance: 4 - the type can be cleared between the test and the use

What are the requirements for code that calls `folio_test_hugetlb()` and then `folio_hstate()`, or
reads other hugetlb-only fields, in order to assure safe usage? What must code that finds a folio
by scanning PFNs hold or call to meet them? Start from `__update_and_free_hugetlb_folio()` and
`page_is_unmovable()`.

## largepage.hugetlb-free: Freeing a hugetlb folio

- section: Hugetlb folios and the pool
- relevance: 4 - the free path restores reservations and may defer

When the last reference on a hugetlb folio is dropped, what decides whether the folio goes back to
the pool or to the page allocator? What does `free_huge_folio()` give back to the subpool and to
the reservation? In which context does the final free run? Start from `free_huge_folio()` and
`enum hugetlb_page_flags` in `include/linux/hugetlb.h`.

## largepage.hugetlb-surplus-adjust: Surplus adjustment

- section: Hugetlb folios and the pool
- relevance: 4 - an error path that passes a different value skews the pool

What does the `adjust_surplus` argument of `remove_hugetlb_folio()` and `add_hugetlb_folio()`
decide? What must an error path that adds a folio back with `add_hugetlb_folio()` pass for it?
Name in-tree code that shows it.

## largepage.change-hugetlb-pool: Pool counter invariants

- section: Hugetlb folios and the pool
- relevance: 4 - the counters are read in combinations

Which relations among the counters of a `struct hstate` must code keep true when it adds a hugetlb
folio to a pool or removes one, and which lock must it hold while it changes them? What other
state of the folio must change together with the counters?

## largepage.hugetlb-demote: Hugetlb demotion

- section: Hugetlb folios and the pool
- relevance: 3 - one folio becomes many and per-folio state must follow

When demotion turns a free hugetlb folio into folios of a smaller pool, which per-folio state is
carried over by the generic initialisation and which must be copied explicitly, and what goes
wrong when the new folios are later freed if it is not? Start from
`demote_free_hugetlb_folios()` and `init_new_hugetlb_folio()`.

## largepage.hugetlb-vmemmap: Hugetlb vmemmap optimisation

- section: Hugetlb folios and the pool
- relevance: 4 - tail struct pages may be read-only and shared

What are the requirements for code that reads or writes the tail struct pages of a hugetlb folio
after `hugetlb_vmemmap_optimize_folio()`, in order to assure safe usage? When must code call
`hugetlb_vmemmap_restore_folio()`, and what happens when that call fails? Start from
`hugetlb_vmemmap_optimize_folio()` and `hugetlb_vmemmap_restore_folio()`.

# Hugetlb reservations

## largepage.hugetlb-alloc-paths: Hugetlb allocation functions

- section: Hugetlb reservations
- relevance: 4 - the variants differ in what they charge and reserve

A table of the functions that allocate a hugetlb folio, to choose between: for a fault, for
migration, for a reservation made outside a VMA, and as a surplus or fresh pool page; for each,
what it does about reservations, cgroup charges and the pool counters. Start from
`alloc_hugetlb_folio()` and `hugetlb_alloc_folio()`.

## largepage.hugetlb-reservation: Reservation bookkeeping

- section: Hugetlb reservations
- relevance: 5 - the whole allocation path is phrased in these terms

How are hugetlb reservations recorded for shared and for private mappings? What do
`vma_needs_reservation()`, `vma_commit_reservation()` and `vma_end_reservation()` do? What do
`map_chg` and `gbl_chg` in `alloc_hugetlb_folio()` mean? Start from `vma_needs_reservation()` and
`alloc_hugetlb_folio()`.

## largepage.hugetlb-subpool: Subpool accounting

- section: Hugetlb reservations
- relevance: 4 - the return values are partial amounts

What do `hugepage_subpool_get_pages()` and `hugepage_subpool_put_pages()` return when the subpool
has a minimum size? What are the requirements for an error path that undoes a reservation, in what
it passes to each of them and to `hugetlb_acct_memory()`, in order to assure safe usage? Name a
caller that shows it.

## largepage.hugetlb-restore-reserve: Restoring a reservation

- section: Hugetlb reservations
- relevance: 4 - a fault that fails after allocation must give the reservation back

What does the restore-reserve flag on a hugetlb folio record, when is it set and cleared, and
what must a path that allocated a hugetlb folio and then fails do before freeing it? Start from
`restore_reserve_on_error()`.

# Hugetlb faults and page tables

## largepage.hugetlb-fault-locks: Fault path lock order

- section: Hugetlb faults and page tables
- relevance: 5 - the fault path drops and retakes locks half way

In which order does a hugetlb fault take the fault mutex, the hugetlb VMA lock, the file rmap
lock, the folio lock and the page table lock, which of them is taken only on some paths and by
which function, and where are some dropped and retaken in the middle? Start from
`hugetlb_fault()` and `hugetlb_wp()`.

## largepage.hugetlb-vma-lock: Hugetlb VMA lock

- section: Hugetlb faults and page tables
- relevance: 4 - it is not the per-VMA lock

What does the hugetlb VMA lock protect, and which mappings have one? What do
`hugetlb_vma_lock_read()` and `hugetlb_vma_lock_write()` do for a mapping that has none? Start
from `hugetlb_vma_lock_read()` and `struct hugetlb_vma_lock`.

## largepage.hugetlb-walk: Walking hugetlb page tables

- section: Hugetlb faults and page tables
- relevance: 4 - the entry pointer can be freed under a walker

What must a caller of `hugetlb_walk()` and a caller of `huge_pte_offset()` hold for the returned
pointer to stay valid? Which lock protects the entry itself? Start from `hugetlb_walk()`,
`huge_pte_offset()` and `huge_pte_lock()`.

## largepage.hugetlb-pmd-share: PMD table sharing

- section: Hugetlb faults and page tables
- relevance: 4 - sharing makes one process's page table another's

When may a hugetlb mapping share a PMD table with another, how is the number of sharers
recorded, and which lock does `huge_pmd_share()` take itself and which must its caller hold?
Start from `want_pmd_share()` and `page_table_shareable()`.

## largepage.hugetlb-pmd-unshare: Unsharing a PMD table

- section: Hugetlb faults and page tables
- relevance: 5 - the step after unsharing is the one that gets left out

What does `huge_pmd_unshare()` leave for its caller to do? Which locks must the caller hold, and
which of them must it still hold when it does the rest? Start from `huge_pmd_unshare()`,
`huge_pmd_unshare_flush()` and `tlb_unshare_pmd_ptdesc()`.

## largepage.hugetlb-unshare-lockless: Unsharing and lockless walkers

- section: Hugetlb faults and page tables
- relevance: 5 - a lockless walker may still read a PMD table that was just unshared

What does the unsharing of a hugetlb PMD table do about lockless page table walkers that may still
read the table, and at which step? Start from `huge_pmd_unshare_flush()` and
`tlb_unshare_pmd_ptdesc()`.

## largepage.hugetlb-fault-folio-lock: Folio lock under fault mutex

- section: Hugetlb faults and page tables
- relevance: 5 - a blocking lock here is a deadlock between two faulters

What are the requirements for taking a folio lock while the hugetlb fault mutex is held, in order
to assure safe usage, and to which folios do they apply? Start from the comment near the end of
`hugetlb_fault()` and from `hugetlb_no_page()`.

## largepage.hugetlb-cow: Hugetlb copy-on-write

- section: Hugetlb faults and page tables
- relevance: 4 - the owner of a private mapping may unmap others

On a hugetlb write fault, what decides between reusing the folio and copying it? What does
`hugetlb_wp()` do when no folio is available for the copy? What does it recheck after it dropped
and retook locks? Start from `hugetlb_wp()` and `unmap_ref_private()`.

## largepage.hugetlb-pagecache: Hugetlb page cache insertion

- section: Hugetlb faults and page tables
- relevance: 3 - the function does not enforce what it needs

What must be true of a hugetlb folio and what must the caller hold before it is added to the
page cache, and in what unit is the index the function is given and the one it stores? Start
from `hugetlb_add_to_page_cache()` and `hugetlbfs_fallocate()`.

# Memory failure

## largepage.mf-returns: Memory failure return values

- section: Memory failure
- relevance: 4 - architecture handlers branch on them

Which values does `memory_failure()` return, and what does each tell the caller about the page?
Which architecture code acts on the difference? What must a function return on success when
`memory_failure()` passes its return value on to the caller? Start from `kill_me_maybe()` in
`arch/x86/kernel/cpu/mce/core.c`.

## largepage.mf-large-folio: Memory failure on large folios

- section: Memory failure
- relevance: 4 - the handler only deals with single pages

When the bad page is in a large folio that is not hugetlb, to which order does the memory
failure handler try to split it, what has it marked on the folio before trying, and what does it
do and return when the split fails or cannot reach order zero? Start from
`try_to_split_thp_page()`.

## largepage.hwpoison-flags: Poison flags on large folios

- section: Memory failure
- relevance: 4 - testing the head page misses a poisoned tail

Which hardware poison flag is kept per page and which per folio, for a large folio and for a
hugetlb folio? What are the requirements for code that tests a large folio for hardware poison in
order to assure safe usage? What must a folio split keep consistent between the flags? Start from
`folio_contain_hwpoisoned_page()`.

## largepage.hwpoison-content-usage: Reading poisoned contents

- section: Memory failure
- relevance: 4 - the read itself can be fatal

What are the requirements for kernel code that reads the contents of a page which may be hardware
poisoned, in order to assure safe usage? Name in-tree examples. Start from `thp_underused()` and
`folio_mc_copy()`.

# Model gaps

## largepage.model-gaps: Other mistakes models make

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
