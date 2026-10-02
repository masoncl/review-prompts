# Questions: MM Large Folios, THP, and Hugetlb (measurement set)

- guide: mm-largepage.md
- title: MM Large Folios, THP, and Hugetlb

A wide set of questions about transparent huge pages, folio splitting and
collapse, hugetlb and memory failure on large folios, used to measure what a
model already knows before deciding what the built guide should spend its words
on. The hand-written guide it will replace is 3,067 words. What a folio is, its
reference counts and the page cache are in the `mm-folio` sets. Run it with
`build-guides.py --no-sources --check-memory --questions` pointed at this
directory. The trimmed set a guide is built from is `../mm-largepage.md`.
Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## largepage.core-files: Core files

- section: Finding your way
- relevance: 4 - hugetlb and THP are each spread over several files
- words: 120

Which files hold the transparent huge page fault, PMD and split code, the
collapse daemon, the hugetlb pool and fault code and its sysfs, sysctl, CMA,
cgroup and struct page optimisation parts, hugetlbfs, and memory failure
handling? A table. Start from `mm/huge_memory.c` and `mm/hugetlb.c`.

## largepage.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 120

For each job (fault in an anonymous PMD-sized folio, fault in a smaller
anonymous large folio, split a huge PMD, split a large folio, collapse small
pages into a large folio, handle a hugetlb fault, allocate a hugetlb folio,
reserve hugetlb pages at mmap, handle a hardware memory error), which function
do you start reading from? A table.

## largepage.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - the reservation rules are written down in one place only
- words: 60

Which files under `Documentation/mm/` and `Documentation/admin-guide/mm/` are
the authority on transparent huge page design and tuning, on hugetlb
reservations, on freeing a hugetlb folio's struct pages, and on hardware poison
handling?

# Transparent huge pages

## largepage.kinds: Kinds of large folio

- section: Kinds and policy
- relevance: 4 - each kind is tested for differently and handled differently
- words: 100

Which kinds of large folio does the kernel have (PMD-sized anonymous, smaller
anonymous, file, shmem, hugetlb, device private, DAX), and which test tells each
apart: large, mappable by a PMD, on the rmap and deferred split machinery,
hugetlb? Start from `folio_test_large()` and `folio_test_pmd_mappable()`.

## largepage.allowable-orders: Allowed orders for a VMA

- section: Kinds and policy
- relevance: 4 - every fault, collapse and smaps path asks this one function
- words: 100

Which function decides which folio orders may be used in a given VMA, what kinds
of caller does it distinguish and how do they differ, and which sets of orders
are possible for anonymous, file and DAX or PFN mappings? Start from
`thp_vma_allowable_orders()`.

## largepage.sysfs-controls: Per-size controls

- section: Kinds and policy
- relevance: 3 - the global knob no longer says everything
- words: 80

How do the global enabled setting and the per-size settings in the
transparent_hugepage sysfs directory combine for anonymous memory, which kernel
variables hold them, and what does "inherit" mean? Start from
`huge_anon_orders_always`.

## largepage.thp-disable: Disabling per process and per VMA

- section: Kinds and policy
- relevance: 3 - the prctl has more than one mode
- words: 60

Which per-VMA flag and which per-process flags turn transparent huge pages off,
what is the difference between the per-process modes, and what overrides them?
Start from `vma_thp_disabled()`.

## largepage.shmem-huge: Shmem huge policy

- section: Kinds and policy
- relevance: 3 - shmem has its own knobs and they are checked first
- words: 80

How is the use of large folios in shmem and tmpfs controlled: the mount option,
the global shmem setting, the per-size settings, and the values that force or
deny? Which function combines them? Start from `shmem_allowable_huge_orders()`.

## largepage.file-collapse-eligibility: File mappings eligible for collapse

- section: Kinds and policy
- relevance: 4 - the condition has been reworked and old configuration names may be gone
- words: 80

Which file mappings may the collapse daemon turn into PMD-sized folios, what
test decides it, and does that depend on a configuration option, on the file
being read-only, or on what the filesystem declared for its mapping? Start from
`file_thp_enabled()` in `mm/huge_memory.c`.

## largepage.anon-pmd-fault: Anonymous PMD fault

- section: Faults
- relevance: 4 - the order of steps is what error paths must undo
- words: 100

List in order what the first fault on an empty anonymous PMD does when it
installs a PMD-sized folio: allocation, charging, anything set up for later
splitting, zeroing, the page table kept in reserve, the rmap, LRU and counter
updates. Start from `do_huge_pmd_anonymous_page()`.

## largepage.anon-mthp-fault: Smaller anonymous large folios

- section: Faults
- relevance: 4 - decides when a fault falls back to a single page
- words: 90

How does an anonymous fault below PMD size choose a folio order, what makes it
skip an order or fall back to a single page, and what does userfaultfd change?
Start from `alloc_anon_folio()` in `mm/memory.c`.

## largepage.huge-zero: Huge zero folio

- section: Faults
- relevance: 3 - its lifetime rules differ by configuration
- words: 80

How is the huge zero folio allocated, reference counted and freed, which
configuration makes it permanent, how is a PMD that maps it marked, and what
does a write fault on it do? Start from `mm_get_huge_zero_folio()`.

## largepage.pgtable-deposit: Deposited page table

- section: Faults
- relevance: 4 - a missing withdraw leaks a page table and a wrong one corrupts the count
- words: 80

Which huge PMD mappings keep a preallocated PTE page table in reserve, who
deposits and withdraws it, and which helper says whether a given huge PMD has
one? Start from `pgtable_trans_huge_deposit()` and `zap_huge_pmd()`.

## largepage.file-pmd-mapping: File PMD mappings

- section: Faults
- relevance: 3 - differs from anonymous in references, deposit and split
- words: 80

Which functions map a file or shmem folio with a PMD, what conditions must hold
for the folio and the VMA, and what happens to such a mapping when the PMD is
split? Start from `do_set_pmd()` and `filemap_map_pmd()`.

## largepage.pmd-cow: Write fault on a huge PMD

- section: Faults
- relevance: 4 - the reuse test is a security boundary
- words: 90

On a write or unshare fault on an anonymous huge PMD, when is the folio reused
in place, which locks and counts does that test depend on, and what is done when
it cannot be reused? Start from `do_huge_pmd_wp_page()`.

## largepage.pmd-leaf-tests: Huge PMD tests

- section: Huge PMD entries
- relevance: 4 - the tests differ in whether they cover non-present entries
- words: 90

Which helpers test whether a PMD is a huge mapping, which of them also accept
non-present huge entries, and which does `split_huge_pmd()` use? Start from
`pmd_trans_huge()`, `pmd_leaf()` and `pmd_is_huge()`.

## largepage.pmd-softleaf: Non-present huge PMD entries

- section: Huge PMD entries
- relevance: 4 - walkers that assume a present entry dereference garbage
- words: 90

Which kinds of non-present entry can a huge PMD hold, which helpers recognise
and decode them, which configuration enables them, and what must a walker that
finds one not do? Start from `pmd_is_migration_entry()` and
`set_pmd_migration_entry()`.

## largepage.pmd-locking: Locking a huge PMD

- section: Huge PMD entries
- relevance: 4 - the PMD can change between the test and the lock
- words: 70

Which lock protects a huge PMD entry, which helper takes it only if the entry is
huge, and what must be rechecked after a PMD was read without the lock? Start
from `pmd_trans_huge_lock()` and `pmd_lock()`.

## largepage.pmd-split: Splitting a huge PMD

- section: Huge PMD entries
- relevance: 5 - references, rmap and exclusivity all change representation here
- words: 120

What does splitting a huge PMD do to an anonymous mapping, to a file mapping and
to a huge zero mapping: how are the folio's references and rmap converted, what
does the freeze argument change, and why is the entry invalidated before the
page table is installed? Start from `__split_huge_pmd_locked()`.

## largepage.huge-pmd-ambiguity: THP and hugetlb PMDs

- section: Huge PMD entries
- relevance: 3 - a test for one kind can match the other
- words: 60

Can a PMD-level test for a transparent huge page also match a hugetlb mapping,
what usage of such a test before THP-only operations is unsafe, and what that
looks similar is correct? Start from `is_vm_hugetlb_page()` and
`walk_hugetlb_range()`.

# Splitting and collapsing folios

## largepage.split-api: Split entry points

- section: Splitting a folio
- relevance: 5 - the variants differ in target order, uniformity and what stays locked
- words: 120

Give a table of the functions that split a large folio, saying for each the
target order, whether the pieces are all one size, where the pieces are put, and
which piece stays locked and referenced for the caller. Start from
`split_huge_page()`, `folio_split()` and `folio_split_unmapped()`.

## largepage.split-preconditions: Split preconditions

- section: Splitting a folio
- relevance: 5 - violated preconditions fail only under load
- words: 70

What must the caller of a folio split hold and guarantee beforehand (lock,
reference, mapping state, writeback), and which function checks the conditions
that depend only on the folio? Start from `folio_check_splittable()`.

## largepage.split-errors: Split return values

- section: Splitting a folio
- relevance: 4 - callers must tell transient from permanent failure
- words: 90

Which error values can a folio split return and what does each mean, which are
worth retrying, and after which can the folio have been partly split? Read the
tests in `folio_check_splittable()` in the order they run, and say which one a
just-truncated folio and the huge zero folio each hit first: a later branch that
names a case is not what a caller sees if an earlier test already returned.
Compare the result with the comment above `__split_huge_page_to_list_to_order()`
and say whether the two agree.

## largepage.split-steps: Split sequence

- section: Splitting a folio
- relevance: 4 - anyone changing the split must keep the order
- words: 120

List in order what a split of a mapped large folio does from entry to return:
the locks taken for anonymous and for file folios, unmapping, the reference
count check and freeze, the page cache or swap cache update, remapping, and
unlocking. Start from `__folio_split()`.

## largepage.split-refcount: Reference counts at split

- section: Splitting a folio
- relevance: 5 - one stray reference makes every split fail
- words: 80

Which reference count must a folio have for a split to go ahead, where is it
checked and where is it frozen, and what kinds of extra reference make it fail?
Start from `folio_expected_ref_count()` and `folio_ref_freeze()`.

## largepage.split-retry-usage: Retrying a failed split

- section: Splitting a folio
- relevance: 4 - the livelock only shows with several tasks on one folio
- words: 90

What usage of take a reference, lock the folio, split, and retry on failure is
unsafe, and what that looks similar is correct? Name in-tree callers that block
on the lock with a reference held and are fine, and say why. Start from
`madvise_free_huge_pmd()` and `try_to_split_thp_page()`.

## largepage.split-min-order: Minimum order of a mapping

- section: Splitting a folio
- relevance: 4 - a split to order zero fails on some filesystems
- words: 90

What happens when a file folio is split below the minimum folio order of its
mapping, which helper tells a caller the lowest order it may ask for, and what
usage after a successful split is unsafe? Start from `min_order_for_split()`.

## largepage.split-uniform: Uniform and non-uniform splits

- section: Splitting a folio
- relevance: 3 - the non-uniform kind can stop half way
- words: 90

How do a uniform and a non-uniform split differ in the pieces they produce, in
how the page cache entry is split and in how they can fail, and which folios may
only be split uniformly to order zero? Start from `enum split_type` and
`__split_unmapped_folio()`.

## largepage.split-beyond-eof: Pieces beyond end of file

- section: Splitting a folio
- relevance: 3 - the split itself drops page cache pages
- words: 70

What does a split of a file or shmem folio do with the pieces that lie beyond
the end of the file, how is the end determined, and what accounting follows for
shmem? Start from `__folio_freeze_and_split_unmapped()`.

## largepage.split-state-propagation: State carried to the pieces

- section: Splitting a folio
- relevance: 4 - a flag left behind is a silent corruption
- words: 100

Which flags and fields does a split copy from the original folio to each new
folio, how are hardware poison, the swap entry, memcg data and page owner
handled, and which flag is dropped? Start from `__split_folio_to_order()`.

## largepage.split-zeropage: Zero-filled pages after a split

- section: Splitting a folio
- relevance: 3 - remapping may replace a page with the shared zero page
- words: 70

When a split remaps the pieces of an anonymous folio, under what conditions is a
zero-filled piece replaced by the shared zero page, and which folios are
excluded? Start from `TTU_USE_SHARED_ZEROPAGE` and
`try_to_map_unused_to_zeropage()`.

## largepage.deferred-split-queue: Deferred split queue

- section: Deferred split
- relevance: 5 - the data structure and its lock have been replaced
- words: 100

What data structure holds the folios queued for deferred splitting, how is it
divided by node and by memory cgroup, which lock protects a folio's entry, and
which folios can be on it? Start from `deferred_split_folio()` and the
`_deferred_list` field.

## largepage.deferred-split-queuers: Queueing for deferred split

- section: Deferred split
- relevance: 4 - callers of the rmap helpers must not queue again
- words: 90

Who queues a folio for deferred splitting and on what condition, what usage by a
caller of the rmap removal helpers is wrong, and what must code that unmaps or
moves a folio without those helpers preserve? Start from `__folio_remove_rmap()`.

## largepage.deferred-split-unqueue: Leaving the deferred split queue

- section: Deferred split
- relevance: 4 - unqueueing at the wrong time corrupts the list
- words: 90

When is a folio taken off the deferred split queue, why is it unsafe to do so
while the folio still has references, and what must happen before a folio's
memory cgroup changes? Start from `folio_unqueue_deferred_split()` in
`mm/internal.h`.

## largepage.deferred-split-alloc: Allocation sites and the queue

- section: Deferred split
- relevance: 4 - a new allocation site that skips the step cannot queue
- words: 70

After allocating and charging a large anonymous folio, what must an allocation
site call before the folio can ever be queued for deferred split, for which
orders, and which sites do? Start from `folio_memcg_alloc_deferred()`.

## largepage.underused: Underused huge pages

- section: Deferred split
- relevance: 3 - fully mapped folios are queued too
- words: 80

Why is a fully mapped PMD-sized anonymous folio put on the deferred split queue,
how does the shrinker decide it is underused, which setting turns that off, and
which folios does it leave alone? Start from `thp_underused()` and
`deferred_split_scan()`.

## largepage.khugepaged-overview: Collapse daemon structure

- section: Collapse
- relevance: 4 - the function names have changed
- words: 100

How does the collapse daemon find work: how an mm gets registered, the scan
cursor, and the functions that scan one mm, one PMD range of anonymous memory and
one range of a file? Start from `khugepaged_enter_vma()` and
`struct khugepaged_scan`.

## largepage.collapse-anon-steps: Anonymous collapse sequence

- section: Collapse
- relevance: 5 - the lock order and the revalidation are where the bugs are
- words: 120

List in order what collapsing a range of anonymous PTEs does: allocation, which
locks are taken and dropped in which mode, what is revalidated after each, how
the PMD is cleared, isolation, copy, and installing the new mapping. Start from
`collapse_huge_page()`.

## largepage.collapse-mthp: Collapse to smaller orders

- section: Collapse
- relevance: 4 - whether the daemon can build folios smaller than a PMD is tree-specific
- words: 100

Can the collapse daemon collapse anonymous memory into folios smaller than a
PMD? If so, how does it pick the order and the offset, which orders are
eligible, and how does installing the result differ from the PMD case? If this
tree cannot, say so. Start from `collapse_scan_pmd()`.

## largepage.collapse-limits: Collapse thresholds

- section: Collapse
- relevance: 3 - the three limits apply differently by caller and order
- words: 90

What do the limits on empty, swapped-out and shared PTEs mean for a collapse,
how do they differ between the daemon and a collapse requested through madvise,
and how are they applied to orders below PMD size? Start from
`khugepaged_max_ptes_none`.

## largepage.collapse-gup-fast: Collapse and lockless walkers

- section: Collapse
- relevance: 4 - a missing step lets GUP-fast use a freed page table
- words: 70

How does an anonymous collapse make sure that lockless page table walkers such
as GUP-fast are no longer using the PTE table it is about to empty? Start from
`pmdp_collapse_flush()` and `tlb_remove_table_sync_one()`.

## largepage.collapse-file: File collapse sequence

- section: Collapse
- relevance: 4 - the rollback path is long
- words: 110

List in order what collapsing a range of a file or shmem mapping does to the
page cache: the new folio, locking and freezing the old folios, the copy, what
is rolled back on failure, and when page tables that map the range are dealt
with. Start from `collapse_file()`.

## largepage.collapse-pte-mapped: PTE-mapped file huge pages

- section: Collapse
- relevance: 3 - runs under different locks from the anonymous path
- words: 90

After a file collapse, how do PTE mappings of the old pages become a PMD mapping:
which function removes or replaces the page tables, which locks does it hold,
and which VMAs does it skip? Start from `retract_page_tables()` and
`collapse_pte_mapped_thp()`.

## largepage.madv-collapse: Collapse on request

- section: Collapse
- relevance: 3 - it ignores most tunables and reports errors differently
- words: 80

How does a collapse requested through madvise differ from the daemon in which
settings it honours, in the allocation mask, and in how scan results become
error numbers? Start from `madvise_collapse()`.

# Large folios elsewhere in mm

## largepage.state-tracking: State tracking level

- section: Per-page and per-folio state
- relevance: 5 - checking the wrong struct page reads stale state
- words: 120

For anonymous exclusivity, hardware poison, dirty, accessed or young, the
reference count and the mapcount of a large folio, say in a table whether the
state is kept per folio, per page or only in the page table entry, and where.

## largepage.anon-exclusive: Anonymous exclusive flag

- section: Per-page and per-folio state
- relevance: 4 - which page carries it depends on how the folio is mapped
- words: 80

On which struct page is the anonymous exclusive flag kept for a PTE-mapped large
folio, for a PMD-mapped one and for hugetlb, and what happens to it on fork, on
PMD split and when a folio is unmapped for migration? Start from
`PG_anon_exclusive` and `__folio_add_anon_rmap()`.

## largepage.second-page-flags: Flags on the first tail page

- section: Per-page and per-folio state
- relevance: 4 - they share a word with a per-page flag
- words: 70

Which folio flags are stored in the first tail page, how are they declared, and
which per-page flag can be set in the same flags word by a different subsystem?
Start from `FOLIO_SECOND_PAGE` in `include/linux/page-flags.h`.

## largepage.nonatomic-flag-usage: Non-atomic flag updates

- section: Per-page and per-folio state
- relevance: 4 - a lost update on a flag nobody was touching
- words: 80

What usage of the non-atomic page and folio flag setters and clearers is unsafe
even when the flag itself is protected by a lock, and when is it correct? Start
from `__FOLIO_SET_FLAG` in `include/linux/page-flags.h`.

## largepage.mapcount-consistency: Mapcount field consistency

- section: Per-page and per-folio state
- relevance: 3 - the lock covers fewer fields than its name suggests
- words: 80

Which of a large folio's mapcount fields does `folio_lock_large_mapcount()` keep
consistent with each other and which not, and how does code that must decide
exactly whether it is the only mapper proceed? Start from
`__wp_can_reuse_large_anon_folio()`.

## largepage.rmap-api: Rmap calls by mapping level

- section: Per-page and per-folio state
- relevance: 4 - the wrong level corrupts the counts
- words: 100

Which rmap functions add, duplicate and remove mappings of a folio by PTEs, by a
PMD and by a PUD, how is the level named in the common implementation, and which
separate functions does hugetlb use? Start from `folio_add_anon_rmap_ptes()` and
`hugetlb_add_anon_rmap()`.

## largepage.pfn-alignment: Natural alignment

- section: Ranges and iteration
- relevance: 2 - elementary, but relied on
- words: 40

What alignment does the first PFN of a large folio have, and how is the head PFN
found from the PFN of any page in it?

## largepage.range-dedup: Folios spanning range pieces

- section: Ranges and iteration
- relevance: 3 - the same folio is acted on twice
- words: 70

When a physical or virtual range is processed in pieces, what goes wrong for a
large folio that crosses a piece boundary, and how does in-tree code avoid it?
Start from `last_applied` in `struct damos`.

## largepage.pagecache-refs: Page cache references

- section: Page cache and swap
- relevance: 4 - a single put after removal leaks
- words: 80

How many references does the page cache hold on a large folio, which function
takes them, and what usage when removing a large folio from the page cache is
unsafe? Start from `__filemap_add_folio()` and `filemap_free_folio()`.

## largepage.isize-mapping: Mapping past end of file

- section: Page cache and swap
- relevance: 5 - over-mapping breaks SIGBUS semantics silently
- words: 110

Which rules stop a large file folio from being mapped beyond the end of the
file, by PTEs and by a PMD, which three places enforce them, which mappings are
exempt, and what does truncation do when it cannot split the folio? Start from
`filemap_map_pages()`, `finish_fault()` and `folio_split_or_unmap()`.

## largepage.swapin: Large folio swap-in

- section: Page cache and swap
- relevance: 4 - a new path that checks and allocates separately reopens a race
- words: 100

How does swap-in of a large folio choose its order and avoid covering a range
where a smaller folio is already in the swap cache, which function does the
check, allocation and fallback, and what do the anonymous and shmem callers pass
it? Start from `swapin_sync()` and `swap_cache_alloc_folio()`.

## largepage.migration: Migrating large folios

- section: Page cache and swap
- relevance: 3 - splitting is the fallback and it is bounded
- words: 90

How does migration handle a large folio: PMD migration entries, when it splits
instead, how often it retries, and what happens to a partially mapped folio's
place on the deferred split queue? Start from `migrate_pages_batch()` and
`try_split_folio()`.

## largepage.unmap-pmd-mapped: Unmapping a PMD-mapped folio

- section: Page cache and swap
- relevance: 4 - the assertion fires only for the rare PMD-mapped case
- words: 80

What must a caller of `try_to_unmap()` pass when the folio may be mapped by a
PMD, what happens otherwise, which case is handled without it, and which wrapper
leaves the guarantee to its callers? Start from `TTU_SPLIT_HUGE_PMD` and
`try_to_unmap_one()`.

# Hugetlb

## largepage.hugetlb-vs-thp: Hugetlb compared with THP

- section: The pool
- relevance: 4 - generic folio code is wrong for hugetlb in several ways
- words: 100

In what ways does a hugetlb folio differ from a transparent huge page: how it is
recognised, whether it can be split, swapped or put on the LRU, how it is mapped
and counted in the rmap, which statistics it uses, and how it is freed?

## largepage.hstate-counters: Pool counters

- section: The pool
- relevance: 5 - every accounting bug is a wrong relation between these
- words: 100

Which counters does `struct hstate` keep for its pool, what does each count,
which have per-node copies, which lock protects them, and which derived values
are computed from two of them? Start from `available_huge_pages()` and
`persistent_huge_pages()`.

## largepage.hugetlb-folio-state: Hugetlb folio state

- section: The pool
- relevance: 4 - the flags decide which path frees the folio
- words: 100

Which hugetlb-specific flags are kept on a hugetlb folio and where, what does
each mean, and which other hugetlb fields live in the folio's tail pages? Start
from `enum hugetlb_page_flags` in `include/linux/hugetlb.h`.

## largepage.hugetlb-alloc-paths: Hugetlb allocation functions

- section: The pool
- relevance: 4 - the variants differ in what they charge and reserve
- words: 110

Give a table of the functions that allocate a hugetlb folio for a fault, for
migration, for a reservation made outside a VMA, and as a surplus or fresh pool
page, saying what each does about reservations, cgroup charges and the pool
counters. Start from `alloc_hugetlb_folio()` and `hugetlb_alloc_folio()`.

## largepage.hugetlb-free: Freeing a hugetlb folio

- section: The pool
- relevance: 4 - the free path restores reservations and may defer
- words: 100

What happens when the last reference on a hugetlb folio is dropped: which
function runs, what it does to the subpool, the reservation and the counters,
when the folio goes back to the pool and when to the page allocator, and why the
final free can be deferred to a workqueue? Start from `free_huge_folio()`.

## largepage.hugetlb-surplus-adjust: Surplus adjustment

- section: The pool
- relevance: 4 - an error path that passes a different value skews the pool
- words: 100

What does the surplus argument of `remove_hugetlb_folio()` and
`add_hugetlb_folio()` decide, when is a constant correct, how do callers that
cannot know decide, and what must an error path that adds a folio back pass?

## largepage.hugetlb-demote: Demotion

- section: The pool
- relevance: 3 - one folio becomes many and per-folio state must follow
- words: 80

How does demotion turn a free hugetlb folio into folios of a smaller pool, which
per-folio flags are carried over by the generic initialisation and which must be
copied explicitly, and why does that matter when the folios are freed? Start
from `demote_free_hugetlb_folios()` and `init_new_hugetlb_folio()`.

## largepage.hugetlb-reservation: Reservations

- section: Reservations
- relevance: 5 - the whole allocation path is phrased in these terms
- words: 120

How are hugetlb reservations recorded for shared and for private mappings, what
do the needs, commit and end calls on a VMA's reservation do, and what do the
map change and global change values computed at allocation mean? Start from
`vma_needs_reservation()` and `alloc_hugetlb_folio()`.

## largepage.hugetlb-subpool: Subpool accounting

- section: Reservations
- relevance: 4 - the return values are partial amounts
- words: 100

What do `hugepage_subpool_get_pages()` and `hugepage_subpool_put_pages()` return
when the subpool has a minimum size, what usage on an error path that undoes a
reservation is unsafe, and what does a correct rollback pass to each and to
`hugetlb_acct_memory()`? Name a caller that shows it.

## largepage.hugetlb-restore-reserve: Restoring a reservation

- section: Reservations
- relevance: 4 - a fault that fails after allocation must give the reservation back
- words: 90

What does the restore-reserve flag on a hugetlb folio record, when is it set and
cleared, and what must a path that allocated a hugetlb folio and then fails do
before freeing it? Start from `restore_reserve_on_error()`.

## largepage.hugetlb-cgroup: Hugetlb cgroup charges

- section: Reservations
- relevance: 3 - two charges with different lifetimes
- words: 80

Which two hugetlb cgroup charges can a hugetlb folio carry, when is each made
and undone, and is the folio also charged to the memory cgroup? Start from
`hugetlb_cgroup_charge_cgroup_rsvd()` and `mem_cgroup_charge_hugetlb()`.

## largepage.hugetlb-fault-locks: Fault path lock order

- section: Faults and page tables
- relevance: 5 - the fault path drops and retakes locks half way
- words: 110

In which order does a hugetlb fault take the fault mutex, the hugetlb VMA lock,
the file rmap lock, the folio lock and the page table lock, which of them can a
hugetlb fault hold besides the per-VMA lock, and where are some dropped and
retaken in the middle? Start from `hugetlb_fault()` and `hugetlb_wp()`.

## largepage.hugetlb-fault-folio-lock: Folio lock under the fault mutex

- section: Faults and page tables
- relevance: 5 - a blocking lock here is a deadlock between two faulters
- words: 110

What usage of the folio lock while the hugetlb fault mutex is held is unsafe,
for which folios, and why? What that looks similar is correct for page cache
folios? Start from the comment near the end of `hugetlb_fault()` and from
`hugetlb_no_page()`.

## largepage.hugetlb-vma-lock: Hugetlb VMA lock

- section: Faults and page tables
- relevance: 4 - it is not the per-VMA lock
- words: 90

What is the hugetlb VMA lock, where is it stored for shared and for private
mappings, when is it allocated and freed, what does it protect, and how does it
differ from the per-VMA lock taken by `vma_start_read()`? Start from
`hugetlb_vma_lock_read()` and `struct hugetlb_vma_lock`.

## largepage.hugetlb-cow: Hugetlb copy-on-write

- section: Faults and page tables
- relevance: 4 - the owner of a private mapping may unmap others
- words: 100

How does a hugetlb write fault decide between reusing and copying, what does the
owner of a private mapping do when no folio is available, which locks does that
drop, and what does the argument that marks a copy made by the owner change in
the allocation? Start from `hugetlb_wp()` and `unmap_ref_private()`.

## largepage.hugetlb-pagecache: Hugetlb page cache insertion

- section: Faults and page tables
- relevance: 3 - the function does not enforce what it needs
- words: 80

What must be true of a hugetlb folio and what must the caller hold before it is
added to the page cache, in what unit is the index, and which callers do it?
Start from `hugetlb_add_to_page_cache()` and `hugetlbfs_fallocate()`.

## largepage.hugetlb-walk: Walking hugetlb page tables

- section: Faults and page tables
- relevance: 4 - the entry pointer can be freed under a walker
- words: 90

Which function finds the page table entry for a hugetlb address, which locks
make the returned pointer safe to use and why, and which lock protects the entry
itself? Start from `hugetlb_walk()`, `huge_pte_offset()` and `huge_pte_lock()`.

## largepage.hugetlb-pmd-share: PMD table sharing

- section: Faults and page tables
- relevance: 4 - sharing makes one process's page table another's
- words: 100

When can two mappings of a hugetlb file share a PMD table, how is a candidate
found and how is the number of sharers recorded, and which lock does
`huge_pmd_share()` take itself and which must its caller hold? Start from
`want_pmd_share()` and `page_table_shareable()`.

## largepage.hugetlb-pmd-unshare: Unsharing a PMD table

- section: Faults and page tables
- relevance: 5 - the step after unsharing is the one that gets left out
- words: 120

What does unsharing a hugetlb PMD table do and not do, which locks must be held,
what must the caller do afterwards and before which lock is dropped, and how are
lockless walkers waited for? Start from `huge_pmd_unshare()`,
`huge_pmd_unshare_flush()` and `tlb_unshare_pmd_ptdesc()`.

## largepage.hugetlb-type-usage: Testing for hugetlb

- section: Hugetlb seen from outside
- relevance: 4 - the type can be cleared between the test and the use
- words: 100

What usage of `folio_test_hugetlb()` followed by `folio_hstate()` or other
hugetlb-only fields is unsafe, under what conditions is the same sequence
correct, and what should code that finds a folio by scanning PFNs use instead?
Start from `__update_and_free_hugetlb_folio()` and `page_is_unmovable()`.

## largepage.hugetlb-generic-paths: Hugetlb in generic paths

- section: Hugetlb seen from outside
- relevance: 3 - a new rmap or migration callback has to decide
- words: 80

What must a generic rmap walk, migration or page table callback do when it can
be handed a hugetlb folio, and which in-tree callbacks show a full hugetlb branch
and which reject hugetlb early? Start from `try_to_unmap_one()` and
`try_to_migrate_one()`.

## largepage.hugetlb-vmemmap: Struct page optimisation

- section: Hugetlb seen from outside
- relevance: 4 - tail struct pages may be read-only and shared
- words: 100

What does the hugetlb struct page optimisation do to a hugetlb folio's tail
struct pages, which flag marks an optimised folio, what may code not do to the
tail pages meanwhile, and when are they restored and what if that fails? Start
from `hugetlb_vmemmap_optimize_folio()` and `hugetlb_vmemmap_restore_folio()`.

## largepage.hugetlb-migration: Migrating hugetlb folios

- section: Hugetlb seen from outside
- relevance: 3 - pool state has to move with the data
- words: 90

How is a hugetlb folio isolated for migration and put back, where does the
target folio come from, and what pool and per-folio state is transferred to it
afterwards? Start from `folio_isolate_hugetlb()`, `alloc_migrate_hugetlb_folio()`
and `move_hugetlb_state()`.

# Memory failure

## largepage.mf-returns: Memory failure return values

- section: Memory failure
- relevance: 4 - architecture handlers branch on them
- words: 90

What does `memory_failure()` return for a recovered page, an already poisoned
page, a filtered event and a failure, which architecture code acts on the
difference, and what must a helper whose return value is passed through return
on success? Start from `kill_me_maybe()` in `arch/x86/kernel/cpu/mce/core.c`.

## largepage.mf-large-folio: Memory failure on a large folio

- section: Memory failure
- relevance: 4 - the handler only deals with single pages
- words: 100

What does the memory failure handler do when the bad page is in a large folio
that is not hugetlb: which flag it sets and when, to which order it splits, what
it does when the split fails or cannot reach order zero, and what it returns
then? Start from `try_to_split_thp_page()`.

## largepage.hwpoison-flags: Poison flags on large folios

- section: Memory failure
- relevance: 4 - testing the head page misses a poisoned tail
- words: 100

How is hardware poison recorded on a large folio and on a hugetlb folio, which
flag is per page and which per folio, which helper answers "does this folio
contain a poisoned page" for both, and what must a split keep consistent? Start
from `folio_contain_hwpoisoned_page()`.

## largepage.mf-hugetlb: Hugetlb poison records

- section: Memory failure
- relevance: 3 - the poisoned subpage is not marked in its own struct page
- words: 90

Where does hugetlb record which of a folio's pages are poisoned, what does the
flag that calls that record unreliable cause when the folio is freed, and what
happens to the record when a poisoned hugetlb folio is released to the page
allocator? Start from `hugetlb_update_hwpoison()` and
`folio_clear_hugetlb_hwpoison()`.

## largepage.hwpoison-content-usage: Reading poisoned contents

- section: Memory failure
- relevance: 4 - the read itself can be fatal
- words: 90

What usage of a page's contents in split, collapse, migration, KSM or compaction
code is unsafe with respect to hardware poison, and what does correct code do
first or use instead? Name in-tree examples. Start from `thp_underused()` and
`folio_mc_copy()`.

## largepage.unmap-poisoned: Unmapping a poisoned folio

- section: Memory failure
- relevance: 3 - the precondition is on the callers
- words: 80

Which folios can `unmap_poisoned_folio()` not handle, what must its callers
check or do first, and what do the memory failure, memory hot-remove and reclaim
callers each do?

## largepage.mf-accounting: Poison accounting

- section: Memory failure
- relevance: 2 - two counters that user space compares
- words: 70

Which global and per-node counters record poisoned pages, which function updates
them together, and which path updates only one by design? Start from
`action_result()` and `num_poisoned_pages_inc()`.

# Changing the implementation

## largepage.change-new-alloc-site: Adding an allocation site

- section: What a change must preserve
- relevance: 4 - several steps are easy to leave out
- words: 100

What must a new code path that allocates and maps a large anonymous folio do
besides allocating it: charging, preparing for deferred split, zeroing, marking
up to date, the rmap and LRU calls, the counters and the per-order statistics?
Start from `map_anon_folio_pmd_nopf()` and `map_anon_folio_pte_nopf()`.

## largepage.change-split: Changing the split code

- section: What a change must preserve
- relevance: 4 - the split is relied on from reclaim, truncate, migration and hwpoison
- words: 100

What must a change to the folio split code keep true for its callers and for
concurrent lockless lookups: what stays frozen until when, which folio keeps the
caller's lock and reference, the statistics, and which tests pin the behaviour?

## largepage.change-hugetlb-pool: Changing pool accounting

- section: What a change must preserve
- relevance: 4 - the counters are read in combinations
- words: 90

What must a change that adds or removes hugetlb folios from a pool keep true of
the counters, under which lock must related counters change together, and what
else is tied to the same transitions (cgroup charges, struct page optimisation,
the hugetlb folio type)?

