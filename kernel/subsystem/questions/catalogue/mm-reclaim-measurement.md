# Questions: MM Reclaim, Swap, and Migration (measurement set)

- guide: mm-reclaim.md
- title: MM Reclaim, Swap, and Migration

A wide set of questions about page reclaim, the swap subsystem, folio
migration, the writeback tags and dirty throttling, and the memory cgroup
charge that follows a folio through all of them. It is used to measure what a
model already knows before deciding what the built guide should spend its
words on. The hand-written guide it will replace is 2,305 words. What the
measurement found is in `mm-reclaim-measurement-results.md`. Format:
`../../../docs/subsystem-questions.md`.

# The subsystem

## reclaim.core-files: Core files

- section: Finding your way
- relevance: 4 - the swap code has been split across new files
- words: 120

Which files hold page reclaim, the multi-generation LRU, workingset detection,
shrinkers, the swap slot allocator, the swap cache and its storage, swap I/O,
zswap, folio migration, device migration, dirty throttling and the memory
cgroup charge code? A table. Start from `mm/vmscan.c` and `mm/swap.h`.

## reclaim.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 120

For each job (direct reclaim, the per-node background reclaimer, reclaim for a
memory cgroup over its limit, giving a folio swap space, swapping a folio in at
a fault, migrating a list of folios, starting and ending writeback on a folio,
charging a folio to a memory cgroup), which function do you start reading
from? A table.

## reclaim.docs-and-tests: Documentation and tests

- section: Finding your way
- relevance: 3 - several rules are written down only there
- words: 80

Which files under `Documentation/` describe the multi-generation LRU, the swap
cache storage, page migration, the unevictable LRU and zswap, and which
selftests exercise migration, memory cgroup reclaim and zswap? Start from
`Documentation/mm/` and `tools/testing/selftests/`.

# Reclaim

## reclaim.reclaim-callers: Callers of reclaim

- section: The reclaim core
- relevance: 4 - each caller sets up the scan differently
- words: 110

Which functions start a reclaim pass (for an allocation, for the background
reclaimer, for a memory cgroup, for a request from userspace, for node reclaim,
for hibernation), and which fields of `struct scan_control` does each set
differently? A table. Start from `try_to_free_pages()` and `balance_pgdat()`.

## reclaim.folio-list-steps: Shrinking a folio list

- section: The reclaim core
- relevance: 5 - almost every reclaim change lands in this function
- words: 120

List in order the checks and steps `shrink_folio_list()` applies to one folio,
from taking the folio lock to freeing it, and say at each where the folio goes
if the step fails: kept, kept and activated, or retried.

## reclaim.dirty-file-folios: Dirty folios in reclaim

- section: The reclaim core
- relevance: 5 - what reclaim writes out has changed over time
- words: 80

What does reclaim do with a dirty file-backed folio, a dirty shmem folio and a
dirty anonymous folio it finds at the tail of the LRU: which of them does it
write itself, through which function, and what flag does it leave on the ones
it does not write? Start from `pageout()`.

## reclaim.writeback-in-reclaim: Folios under writeback

- section: The reclaim core
- relevance: 4 - the three cases decide whether reclaim waits
- words: 90

When `shrink_folio_list()` finds a folio under writeback, what are the cases it
distinguishes, in which of them does it wait, and what decides between them?
Start from `writeback_throttling_sane()` and `may_enter_fs()`.

## reclaim.references-check: Reference check

- section: The reclaim core
- relevance: 4 - decides activate, keep or reclaim
- words: 90

What does `folio_check_references()` return for a folio that was referenced
through page tables once, more than once, or not at all, and how does the
answer differ when the multi-generation LRU is enabled? What does a return of
minus one from the rmap walk mean?

## reclaim.remove-mapping: Detaching from the mapping

- section: The reclaim core
- relevance: 5 - the order of the tests is what prevents data loss
- words: 90

How does `__remove_mapping()` decide that a folio can be freed: which locks it
takes for a page-cache folio and for a swap-cache folio, what reference count it
expects, in which order it tests the count and the dirty flag and why, and
what it leaves behind in the slot?

## reclaim.anon-swap-step: Anonymous folios to swap

- section: The reclaim core
- relevance: 4 - several early exits and a split fallback
- words: 100

In `shrink_folio_list()`, what is checked before an anonymous folio is given
swap space, what happens to a large folio that cannot get contiguous slots, and
why is the folio marked dirty afterwards? Start from the call to
`folio_alloc_swap()`.

## reclaim.demotion: Demotion

- section: The reclaim core
- relevance: 3 - only with memory tiers, but it reorders the loop
- words: 80

When does reclaim migrate a folio to a lower memory tier instead of freeing it,
how is the target node chosen and restricted, and what happens to folios that
could not be demoted? Start from `can_demote()` and `demote_folio_list()`.

## reclaim.isolation: LRU isolation

- section: The reclaim core
- relevance: 4 - the flag and the reference are the protocol
- words: 90

How is a folio taken off an LRU list for reclaim or migration: which flag is
cleared and by whom, which reference is taken, what makes isolation fail, and
what limits how many folios may be isolated at once? Start from
`folio_isolate_lru()`, `isolate_lru_folios()` and `too_many_isolated()`.

## reclaim.bounded-lru-scan: Scans under the LRU lock

- section: The reclaim core
- relevance: 3 - an unbounded skip loop holds a spinlock with interrupts off
- words: 70

In a loop that filters an LRU list while holding the LRU lock, what way of
skipping entries is unsafe, and what skip path that looks similar is correct?
Name in-tree code that shows the correct form. Start from
`isolate_lru_folios()`.

## reclaim.scan-balance: Anon and file balance

- section: Pressure and balance
- relevance: 4 - the inputs have been reworked more than once
- words: 100

How does `get_scan_count()` split scanning between anonymous and file folios:
what inputs does it use (swappiness, the cost counters, the cache-trim and
tiny-file conditions, the priority), and which conditions force one type to be
skipped entirely?

## reclaim.memcg-protection: Memory cgroup protection

- section: Pressure and balance
- relevance: 4 - protection scales the scan, it does not just skip
- words: 90

How do a memory cgroup's min and low settings affect a reclaim pass: where is
the effective protection computed, where is it tested, how does it scale the
scan target, and when is low protection overridden? Start from
`mem_cgroup_calculate_protection()` and `shrink_node_memcgs()`.

## reclaim.throttling: Reclaim throttling

- section: Pressure and balance
- relevance: 4 - replaces the congestion waits people remember
- words: 90

For what reasons can a reclaimer be put to sleep by `reclaim_throttle()`, how
long for, what wakes it early, and which tasks are never throttled? Start from
`enum vmscan_throttle_state`.

## reclaim.kswapd-loop: Background reclaim loop

- section: Pressure and balance
- relevance: 4 - the termination conditions are subtle
- words: 100

In `balance_pgdat()`, what is done on each pass, what raises the scanning
priority, and what ends the loop? What does kswapd do before sleeping, and what
wakes it?

## reclaim.kswapd-order-drop: Order drop in background reclaim

- section: Pressure and balance
- relevance: 3 - ignoring it causes massive overreclaim
- words: 70

When does the background reclaimer stop reclaiming for the allocation order it
was woken for, and what usage of the order in a later balance check is unsafe,
and what is correct? Start from `kswapd_shrink_node()` and `pgdat_balanced()`.

## reclaim.kswapd-failures: Hopeless nodes

- section: Pressure and balance
- relevance: 4 - the reset condition has been tightened
- words: 80

How does a node come to be treated as one the background reclaimer cannot
balance, what do direct reclaimers and wakeups do differently for such a node,
and what resets the state? Start from `kswapd_failures` in
`struct pglist_data`.

## reclaim.direct-throttle: Throttling direct reclaimers

- section: Pressure and balance
- relevance: 3 - a hang if the wake condition and the sleep condition disagree
- words: 80

When is a task entering direct reclaim made to wait for the background
reclaimer, which zones and which watermark decide it, which tasks are exempt,
and what wakes the waiters? Start from `throttle_direct_reclaim()` and
`allow_direct_reclaim()`.

## reclaim.zone-skip-consistency: Zones that count

- section: Pressure and balance
- relevance: 3 - a mismatch means an escape hatch never fires
- words: 80

Several functions in `mm/vmscan.c` loop over a node's zones and leave some out.
Which functions must agree on which zones count, what goes wrong if they do
not, and what rule do they currently share? Start from
`for_each_managed_zone_pgdat()` and `allow_direct_reclaim()`.

## reclaim.proactive: Proactive reclaim

- section: Pressure and balance
- relevance: 3 - a newer entry with its own arguments
- words: 80

Through which files can userspace ask for memory to be reclaimed from a cgroup
or from a node, what arguments do they take, and how does such a pass differ
from reclaim driven by an allocation? Start from `user_proactive_reclaim()`.

## reclaim.vmstat-counters: Reclaim counters

- section: Accounting
- relevance: 4 - where the counters live decides which helper updates them
- words: 80

Where are the scan, steal, refill, rotate and demote counters of reclaim kept:
as global VM events, as node statistics or as per-lruvec statistics, and which
helper updates them? How is the counter for the kind of reclaimer selected?
Start from `reclaimer_offset()`.

## reclaim.classic-mglru-pairing: Accounting in both implementations

- section: Accounting
- relevance: 4 - a bug shows only when the other implementation is active
- words: 110

The active/inactive LRU and the multi-generation LRU both feed
`shrink_folio_list()`, and each updates statistics, memcg events and
tracepoints around it. For each counter or tracepoint, which function on one
side corresponds to which on the other, and what do they share? A table.

## reclaim.unevictable: Unevictable folios

- section: Accounting
- relevance: 3 - the test is racy by design and is repeated
- words: 70

What makes a folio unevictable, where is that tested as a folio is put on an
LRU list and again in reclaim, and how do folios get back to an evictable list
when the reason goes away? Start from `folio_evictable()` and
`check_move_unevictable_folios()`.

## reclaim.workingset-shadows: Shadow entries

- section: Accounting
- relevance: 4 - what is packed into them constrains memcg ids and node ids
- words: 100

What does reclaim leave in place of an evicted folio, what is packed into that
value, where is it stored for a page-cache folio and for a swapped-out folio,
and what happens when the folio is faulted back? Start from
`workingset_eviction()` and `workingset_refault()`.

## reclaim.shrinker-api: Shrinkers

- section: Shrinkers
- relevance: 4 - the registration API and the return values are easy to misuse
- words: 110

How is a shrinker allocated, registered and freed, what do its count and scan
callbacks return to say "nothing", "stop" and a number, what do the flags for
NUMA and memory cgroup awareness change, and how is a shrinker kept alive while
reclaim is calling it? Start from `shrinker_alloc()` and `do_shrink_slab()`.

## reclaim.list-lru: Object lists for shrinkers

- section: Shrinkers
- relevance: 3 - used by most filesystem caches
- words: 80

What does `struct list_lru` provide to a cache with a shrinker, which lock
protects each list, what may a walk callback return and what does each return
value require of the callback, and what happens to the lists of a memory
cgroup that goes offline?

# The multi-generation LRU

## reclaim.mglru-structure: Generations and tiers

- section: Structure
- relevance: 4 - the vocabulary everything else uses
- words: 110

What are generations and tiers in the multi-generation LRU: how many of each,
which sequence numbers bound the generations, where in a folio is its
generation and its access count stored, and which generations count as
"active" for the statistics? Start from `struct lru_gen_folio` and
`lru_gen_is_active()`.

## reclaim.mglru-enable: Runtime switch

- section: Structure
- relevance: 4 - code must behave while folios are on either kind of list
- words: 80

How is the multi-generation LRU switched on and off at run time, what state are
the lists in while the switch is in progress, and how do the paths that choose
between the two implementations test for that? Start from
`lru_gen_change_state()`.

## reclaim.mglru-aging: Aging

- section: Structure
- relevance: 4 - two ways of finding accessed folios, with different locking
- words: 110

How does aging produce a new youngest generation: what walks page tables and
what walks the rmap, how are address spaces chosen and revisited, what are the
Bloom filters for, and when is the walk skipped? Start from
`try_to_inc_max_seq()`, `walk_mm()` and `lru_gen_look_around()`.

## reclaim.mglru-eviction: Eviction

- section: Structure
- relevance: 4 - the sorting step moves folios without reclaiming them
- words: 110

How does eviction work under the multi-generation LRU: how is the type and
tier to scan chosen, what does the sorting step do with a folio instead of
isolating it, what bounds a scan, and what happens to folios that reclaim
rejects? Start from `evict_folios()`, `scan_folios()` and `sort_folio()`.

## reclaim.mglru-refs-flags: Access tracking flags

- section: Structure
- relevance: 4 - three flags and a bit field are overloaded
- words: 100

How do the referenced flag, the workingset flag and the reference-count bits
record accesses through file descriptors and through page tables under the
multi-generation LRU, and which functions set and clear them? Start from the
comment on `LRU_REFS_FLAGS` in `include/linux/mmzone.h`.

## reclaim.mglru-tier-bits: Tier bits on generation change

- section: Structure
- relevance: 4 - stale bits inflate access counts
- words: 90

What must code that moves a folio to another generation do with the folio's
access-tracking bits, what usage is unsafe, and which functions that rewrite the
generation field deliberately keep those bits and are correct? Start from
`folio_update_gen()`, `folio_inc_gen()` and `lru_gen_add_folio()`.

## reclaim.mglru-memcg-lru: Memory cgroup ordering

- section: Structure
- relevance: 3 - global reclaim under the multi-generation LRU does not walk the cgroup tree
- words: 90

How does global reclaim choose which memory cgroup to reclaim from under the
multi-generation LRU, what are the generations, bins and segments of that
structure, and which events move a memory cgroup within it? Start from
`lru_gen_rotate_memcg()` and `shrink_many()`.

# Swap

## reclaim.swap-entry-encoding: Swap entries in page tables

- section: Swap structures
- relevance: 4 - the helpers for non-present entries have been renamed
- words: 90

How is a swap entry encoded, and which type and helpers does this tree use to
read a non-present page table entry and tell a swap entry from a migration
entry, a device-private entry or a marker? Start from
`include/linux/swapops.h`.

## reclaim.swap-device-and-clusters: Swap device and clusters

- section: Swap structures
- relevance: 4 - what is per device and what is per cluster has moved
- words: 120

What does `struct swap_info_struct` hold and what does
`struct swap_cluster_info` hold, how big is a cluster, which lists does a
cluster move between and what do the cluster flags mean, and which lock
protects what? A table for the locks.

## reclaim.swap-slot-state: Per-slot state

- section: Swap structures
- relevance: 5 - the count, the cache and the shadow have been unified
- words: 120

Where is the state of one swap slot kept: whether it is free, swapped out or
cached, its reference count, whether its contents are all zero, and which memory
cgroup it is charged to? Give the formats a slot's value can take and how they
are told apart. Start from `swap_table_get()`.

## reclaim.swap-count: Swap counts

- section: Swap structures
- relevance: 5 - who may raise a count from zero is a locking rule
- words: 110

Which functions raise and lower a swap slot's reference count, what must the
caller of each hold, what count do freshly allocated slots start with, what
keeps such slots from being freed, and what happens when a count overflows its
field? Start from `folio_dup_swap()` and `swap_put_entries_direct()`.

## reclaim.swap-cache-api: Swap cache operations

- section: Swap cache
- relevance: 5 - the locking and reference rules are new
- words: 120

Which functions look a folio up in the swap cache, add one, delete one and
replace one, what must the caller hold for each (folio lock, cluster lock,
device stabilised), how many references does the swap cache hold on a folio,
and in which order are the folio lock and the cluster lock taken? A table.

## reclaim.swap-cache-lookup-usage: Using a looked-up folio

- section: Swap cache
- relevance: 5 - a swap entry value can come back naming different data
- words: 90

After looking a folio up in the swap cache by a swap entry read from a page
table, what usage of the folio is unsafe, and what sequence of checks makes it
correct? What must be rechecked under the page table lock when the lookup
found nothing? Name in-tree code that does each.

## reclaim.swap-residency: Staying in the swap cache

- section: Swap cache
- relevance: 4 - the release test can err in one direction only
- words: 90

What keeps a folio in the swap cache once it is there, which conditions must
hold before `folio_free_swap()` removes it, in which direction can its test for
"still swapped" be wrong, and who calls it?

## reclaim.swap-address-space: The swap address space

- section: Swap cache
- relevance: 4 - callers still get a mapping for a swap-cache folio
- words: 70

What does `folio_mapping()` return for a folio in the swap cache, what does
that object contain, and what is it used for? Start from `swap_space` in
`mm/swap_state.c`.

## reclaim.swapbacked-vs-swapcache: Swap-backed versus cached

- section: Swap cache
- relevance: 5 - confusing the two flags corrupts the wrong structure
- words: 120

What do `folio_test_swapbacked()` and `folio_test_swapcache()` each mean, and
for a shmem folio in the page cache, a shmem folio in the swap cache and an
anonymous folio in the swap cache, what are the two flags, what is
`folio->mapping`, and where are the folio's entries stored? A table. Which test
must code use to choose between page-cache and swap-cache operations?

## reclaim.swap-alloc: Slot allocation

- section: Swapping out
- relevance: 4 - the allocator has been rewritten around clusters
- words: 110

How does `folio_alloc_swap()` find slots for a folio: what is tried first and
what is the slow path, how are devices and clusters chosen, what is different
for a large folio, and what state is the folio in on success and on failure?

## reclaim.swap-alloc-local-lock: Allocator local lock

- section: Swapping out
- relevance: 3 - a sleeping call there is silent unless it really blocks
- words: 80

Which lock does the swap slot allocator run under, what may code reachable from
there not do, how does code that needs to do it anyway proceed, and what after
the allocator returns is free of the restriction? Start from
`percpu_swap_cluster` and `swap_cluster_populate()`.

## reclaim.swap-out-sequence: Swap-out sequence

- section: Swapping out
- relevance: 4 - four subsystems each do one step
- words: 110

List in order what happens to an anonymous folio from the moment reclaim gives
it swap space to the moment its memory is freed: which function does each step,
when the page table entries are replaced, when the swap count is raised, when
the data is written, and when the folio leaves the swap cache.

## reclaim.swap-io: Swap I/O

- section: Swapping out
- relevance: 4 - the write and read paths have new plumbing
- words: 110

How are swap writes and reads issued: what do `swap_writeout()` and
`swap_read_folio()` try before touching the device, how are requests batched
and submitted, what does a swap device's operations table provide, and what
changes for a swap file on a filesystem? Start from `struct swap_io_ctx` and
`struct swap_ops`.

## reclaim.zswap: zswap

- section: Swapping out
- relevance: 3 - the store and load contracts have preconditions
- words: 100

What do `zswap_store()`, `zswap_load()` and `zswap_invalidate()` each promise
and require, what happens to a large folio, how is zswap memory charged to a
memory cgroup, and how does written-back data reach the swap device? Start from
`mm/zswap.c`.

## reclaim.swapin-fault: Swap-in at a fault

- section: Swapping in
- relevance: 5 - each recheck is there for a race
- words: 120

List the steps `do_swap_page()` takes for a real swap entry, from pinning the
device to installing the page table entry: which function reads the folio in
for a fast device and for a slow one, what is rechecked after the folio is
locked and after the page table lock is taken, and when is the swap slot
released?

## reclaim.swapin-large: Large folio swap-in

- section: Swapping in
- relevance: 4 - the error codes each mean something different
- words: 110

What does `swap_cache_alloc_folio()` return when the target slot is no longer
swapped out, when it already has a folio, and when another slot of a large range
is unsuitable, which of these does it handle itself and how, and what makes a
range unsuitable? Start from `__swap_cache_add_check()`.

## reclaim.swapin-conflict-usage: Retrying a swap-in

- section: Swapping in
- relevance: 4 - retrying the same order can loop forever
- words: 80

When a caller asks `swap_cache_alloc_folio()` for a large folio and it fails
because of a conflict in the range, what retry is unsafe and what is correct?
Which callers can never see that failure? Name in-tree code that shows the
correct form. Start from `shmem_swap_alloc_folio()`.

## reclaim.swap-readahead: Swap readahead

- section: Swapping in
- relevance: 3 - the two kinds walk different things
- words: 90

What are the two kinds of swap readahead, what does each walk to find entries
to read, how is the window sized, and what must readahead that walks page
table entries do about entries that belong to a different swap device? Start
from `swapin_readahead()` and `swap_vma_readahead()`.

## reclaim.swap-device-lifetime: Swap device lifetime

- section: Swap devices
- relevance: 5 - use after free against swapoff
- words: 110

What does swapoff free and in what order, what does `get_swap_device()` check
and take, and which other things a caller may hold stabilise a swap device
without it? Start from the comments above `get_swap_device()` in
`mm/swapfile.c` and above `swap_cache_has_folio()` in `mm/swap.h`.

## reclaim.swap-device-usage: Unpinned device access

- section: Swap devices
- relevance: 5 - the helper that skips the reference is the common one
- words: 90

What usage of `__swap_entry_to_info()` or `__swap_entry_to_cluster()` is unsafe,
and which in-tree uses without a device reference are correct and why? Which
path needs none of the usual protections?

## reclaim.swapoff: Swapoff

- section: Swap devices
- relevance: 3 - the one path that reads every slot back
- words: 90

List in order what the swapoff system call does, from taking the device off the
allocation lists to freeing its structures: how entries in page tables, in
shmem and in the swap cache are each brought back, and what makes it give up.
Start from `try_to_unuse()`.

## reclaim.swap-memcg: Swap accounting

- section: Swap and memory cgroups
- relevance: 5 - the record lives in a new place
- words: 110

When a folio is given swap space, which memory cgroup is charged for the swap,
how is that cgroup resolved if the folio's own one is offline, where is the
owner of each slot recorded, when is the swap charge released, and what is
different in the legacy hierarchy's combined memory and swap counter? Start
from `__mem_cgroup_try_charge_swap()`.

## reclaim.swap-memcg-usage: Charging and recording one cgroup

- section: Swap and memory cgroups
- relevance: 4 - a mismatch leaks a counter permanently
- words: 80

In code that charges swap to a memory cgroup, records an id and later
uncharges by that id, what usage is unsafe, and what is correct? What kind of
refactoring introduces the unsafe form?

## reclaim.shmem-swap: Shmem and swap

- section: Shmem
- relevance: 4 - a shmem folio changes caches under its lock
- words: 100

How does a shmem folio move from the page cache to the swap cache and back:
which functions do it, what is held across the move, what is stored in the
page cache in the folio's place, and how does shmem keep track of the inodes
that have swapped-out pages? Start from `shmem_writeout()` and
`shmem_swapin_folio()`.

## reclaim.counter-gated-list: Counter-gated list membership

- section: Shmem
- relevance: 2 - one pattern, but it hangs swapoff
- words: 70

When an object's membership of a tracking list is governed by a counter, what
removal from the list on an error path is unsafe, and what is correct? Start
from `shmem_swaplist` and the `swapped` field of `struct shmem_inode_info`.

## reclaim.list-walk-lock-drop: List walks that drop the lock

- section: Shmem
- relevance: 2 - a generic hazard with an example here
- words: 70

What is unsafe about dropping the list lock inside a
`list_for_each_entry_safe()` walk, and what does a correct walk that must drop
the lock do? Start from `shmem_unuse()`.

# Migration

## reclaim.migrate-api: Migration API

- section: Migrating folios
- relevance: 4 - the return value and the list contents are easy to misread
- words: 110

What are the arguments of `migrate_pages()`, what do the modes and the reasons
mean, what does it return, what is left on the list it was given, and who must
put those folios back and how? Start from `include/linux/migrate_mode.h`.

## reclaim.migrate-phases: Phases of one migration

- section: Migrating folios
- relevance: 4 - failure handling differs by phase
- words: 110

Migrating one folio is split into an unmap phase and a move phase. What does
each do, what state is recorded between them and where, and what is undone if
either fails? Start from `migrate_folio_unmap()` and `migrate_folio_move()`.

## reclaim.migrate-batch: Batched migration

- section: Migrating folios
- relevance: 3 - batching constrains what a callback may assume
- words: 90

How does `migrate_pages_batch()` batch work: what is batched, how many retries
there are and for which errors, what happens to a large folio that cannot be
migrated whole, and when does migration fall back to one folio at a time?

## reclaim.migrate-refcount: Expected references

- section: Migrating folios
- relevance: 4 - extra references make migration fail, not wait
- words: 80

How does migration decide that nobody else is using a folio: which function
computes the expected reference count, where is the count frozen, and what is
returned when it does not match? Start from `folio_migrate_mapping()`.

## reclaim.migrate-callback: The migrate callback

- section: Migrating folios
- relevance: 4 - a filesystem contract
- words: 110

What must an address space's `migrate_folio` operation do and return, which
ready-made implementations exist and when is each appropriate, what locks and
state are the two folios in when it is called, and what happens for a mapping
that does not provide one?

## reclaim.migrate-callback-sleeps: Sleeping in migrate callbacks

- section: Migrating folios
- relevance: 4 - safe for small folios, a bug for large ones
- words: 80

Which of the generic migration helpers can sleep and for which folios, what
usage of them in a `migrate_folio` callback is therefore unsafe, and what does
correct in-tree code do instead? Start from `folio_mc_copy()` and
`__buffer_migrate_folio()`.

## reclaim.migrate-entries: Migration entries

- section: Migrating folios
- relevance: 4 - what a faulting thread sees mid-migration
- words: 90

What replaces a page table entry while its folio is being migrated, what does
a thread that faults on it do, which function puts the real entries back, and
what state (young, dirty, exclusive, write) survives the round trip? Start from
`try_to_migrate()` and `remove_migration_ptes()`.

## reclaim.migrate-rmap-lock-scope: Reverse-map lock across migration

- section: Migrating folios
- relevance: 3 - a lock inversion that only one path can hit
- words: 80

When the caller of `try_to_migrate()` already holds the reverse-map lock and
says so with a flag, what usage between unmapping and remapping is unsafe, and
what is correct? Name the in-tree caller that does it. Start from
`TTU_RMAP_LOCKED`.

## reclaim.migrate-state-copy: State carried across

- section: Migrating folios
- relevance: 3 - each subsystem has something to move
- words: 90

What is carried from the old folio to the new one by `folio_migrate_flags()`
and by `__folio_migrate_mapping()`: which flags, the LRU generation and
reference bits, the swap cache entry, the statistics? What is deliberately not
copied?

## reclaim.migrate-memcg: Charge transfer in migration

- section: Migrating folios
- relevance: 4 - the source folio ends with no charge
- words: 80

How does a folio's memory cgroup charge move to the new folio in migration,
what state is the old folio left in, and what usage of the old folio afterwards
is unsafe, and what is correct? Start from `mem_cgroup_migrate()` and
`migrate_folio_done()`.

## reclaim.migrate-movable-ops: Movable non-LRU pages

- section: Migrating folios
- relevance: 2 - a few drivers
- words: 80

How do pages that are not on an LRU list (balloon, zsmalloc) take part in
migration: how are they marked, which operations must their owner supply, and
how are they isolated and put back? Start from `struct movable_operations`.

## reclaim.migrate-isolation-count: Empty isolation lists

- section: Migrating folios
- relevance: 3 - an empty list does not mean nothing qualified
- words: 70

When code collects folios onto a list for migration, what usage of "the list is
empty" is unsafe, and what is correct? Start from
`collect_longterm_unpinnable_folios()` in `mm/gup.c`.

# Writeback

## reclaim.writeback-tags: Page cache tags

- section: Tags and flags
- relevance: 5 - wrong tag handling loses data or livelocks sync
- words: 80

Which tags does the page cache keep for writeback, which mark of the tree is
each, and what does each mean? A table. Start from `PAGECACHE_TAG_DIRTY` in
`include/linux/fs.h`.

## reclaim.writeback-tag-lifecycle: Tag lifecycle

- section: Tags and flags
- relevance: 5 - each transition is one function
- words: 110

Which function sets and which clears each writeback tag, from a folio being
dirtied to its writeback ending: what do the dirty_folio implementations do,
what copies one tag to another and for which kind of sync, and what does
starting writeback do to each tag? Start from `folio_mark_dirty()`,
`tag_pages_for_writeback()` and `__folio_start_writeback()`.

## reclaim.writeback-iter: Writeback iteration

- section: Tags and flags
- relevance: 4 - the old helper and the old callback are gone
- words: 100

How does a filesystem's `->writepages` walk the dirty folios of a mapping in
this tree: which iterator does it use, which tag does the iterator follow for
which kind of writeback, what state is a folio in when it is handed out, and
how are errors and early termination reported? Start from `wbc_to_tag()`.

## reclaim.writeback-tag-usage: Keeping the to-write tag

- section: Tags and flags
- relevance: 3 - a sync that revisits a folio needs the tag
- words: 70

What usage of `folio_start_writeback()` loses a folio from a data-integrity
sync that has to come back to it, and what is correct? Start from
`__folio_start_writeback()`.

## reclaim.writeback-flags: Dirty and writeback flags

- section: Tags and flags
- relevance: 4 - the order of the flag changes is the protocol
- words: 100

In what order must a writer clear the dirty flag, set the writeback flag,
unlock the folio and end writeback, what does `folio_clear_dirty_for_io()` do
to page table entries and accounting, and how is a folio that could not be
written made dirty again? Start from `folio_redirty_for_writepage()`.

## reclaim.dirty-throttling: Dirty throttling

- section: Throttling writers
- relevance: 3 - a large mechanism with two domains
- words: 110

How does `balance_dirty_pages()` decide whether and how long to pause a task
that dirties pages: which thresholds does it compute, for which two domains,
what is the free-run region, and which of the two domains' results is used?
Start from `struct dirty_throttle_control`.

## reclaim.wb-domain-usage: Domain of a throttle control

- section: Throttling writers
- relevance: 3 - the global domain is wrong when the cgroup domain was selected
- words: 80

In code that is handed a `struct dirty_throttle_control`, what access to
`global_wb_domain` is unsafe, which in-tree accesses to it are intentional and
correct, and what should a tracepoint use? Start from `dtc_dom()` and
`domain_dirty_limits()`.

# Memory cgroup charge

## reclaim.memcg-charge-api: Charging a folio

- section: The charge
- relevance: 5 - what the folio points at has changed
- words: 110

Which functions charge a folio to a memory cgroup (at a fault, on adding to the
page cache, at swap-in, for hugetlb), what is stored in the folio's
`memcg_data`, which references does a charged folio hold, and is anything
charged at the root? Start from `charge_memcg()` and `commit_charge()`.

## reclaim.memcg-offline: Offlining a memory cgroup

- section: The charge
- relevance: 5 - folios no longer pin a dead cgroup the way people remember
- words: 110

What happens to the folios charged to a memory cgroup when it goes offline:
what is redirected to the parent, what happens to the LRU lists and under which
locks, what differs under the multi-generation LRU, and what can
`folio_memcg()` return during the window? Start from
`memcg_reparent_objcgs()`.

## reclaim.memcg-lookup: Folio to memory cgroup

- section: The charge
- relevance: 5 - the binding can change under a reader
- words: 100

What must a caller hold for the result of `folio_memcg()` to stay the folio's
memory cgroup, and what for the pointer merely to stay valid memory? What do
`folio_memcg_check()` and `get_mem_cgroup_from_folio()` add? Start from the
comment above `folio_memcg()` in `include/linux/memcontrol.h`.

## reclaim.memcg-lruvec-lock: Locking a folio's lruvec

- section: The charge
- relevance: 4 - lock, recheck, and an RCU section that outlives the call
- words: 90

How does `folio_lruvec_lock()` make sure it has locked the right lruvec, what
else is held on return and which function releases it, and how does code that
locks many folios in a row avoid relocking? Start from
`folio_lruvec_relock_irq()`.

## reclaim.memcg-uncharge: Uncharging

- section: The charge
- relevance: 4 - the pairing rules and one ordering rule
- words: 90

Where is a folio uncharged on the free path, what must have happened to a large
folio before it is uncharged and why, which paths transfer a charge instead of
uncharging, and what does uncharging do to the counters and to the folio? Start
from `uncharge_folio()` and `folio_unqueue_deferred_split()`.

## reclaim.memcg-ids-and-refs: Identifiers and references

- section: The charge
- relevance: 4 - two ids, and a lookup that returns an unpinned pointer
- words: 100

Which numeric identifiers does a memory cgroup have, where is each used, and
how long does each stay valid after the cgroup is removed? What does a lookup
by identifier return, and what must the caller do to keep using the result
after leaving the RCU section? Start from `mem_cgroup_from_private_id()`.

## reclaim.memcg-stock: Per-CPU charge caches

- section: The charge
- relevance: 3 - explains why a removed cgroup lingers
- words: 80

What do the per-CPU charge caches hold, what reference keeps a cached memory
cgroup alive, when are they drained, and what is the consequence of a missed
drain: a leak, a delayed free or a use after free? Start from `consume_stock()`
and `drain_all_stock()`.

## reclaim.memcg-limits: Enforcing the limits

- section: The charge
- relevance: 4 - reclaim, retries and the OOM killer all hang off one function
- words: 110

What does `try_charge_memcg()` do when a charge would exceed the hard limit:
what it tries and how many times, when it invokes the OOM killer, which
allocations are let through regardless, and how is going over the high limit
handled and where?
