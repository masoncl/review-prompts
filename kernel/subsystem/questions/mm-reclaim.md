# Questions: MM Reclaim, Swap, and Migration

- guide: mm-reclaim.md
- title: MM Reclaim, Swap, and Migration

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/mm-reclaim-measurement.md` is
the wider set the readers were measured on and `catalogue/mm-reclaim-measurement-results.md` says
what they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## reclaim.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## reclaim.core-files: Core files

- section: Finding your way
- relevance: 4 - the swap code has been split across new files

A table and nothing else, job to file: page reclaim; the multi-generation LRU; workingset
detection; shrinkers; the swap slot allocator; the swap cache and the table that stores it; swap
I/O; zswap; folio migration; device migration; dirty throttling; the memory cgroup charge code.
Where a reader is likely to look for a file that does not exist in this tree, say so in the row.
Start from `mm/vmscan.c` and `mm/swap.h`.

# Shrinking a folio list

## reclaim.folio-list-steps: Exit paths and step order

- section: Shrinking a folio list
- relevance: 5 - almost every reclaim change lands in this function

What does each exit of `shrink_folio_list()` do with a folio that a failed check sends to it?
Which steps between taking the folio lock and freeing the folio rely on an earlier step having
run? What must a new step do on its failure path?

## reclaim.references-check: Page table reference check

- section: Shrinking a folio list
- relevance: 4 - decides activate, keep or reclaim

What does `folio_check_references()` return for a folio that was referenced through page tables
once, more than once, or not at all, and how does the answer differ when the multi-generation LRU
is enabled? What does a return of minus one from `folio_referenced()` mean?

## reclaim.dirty-file-folios: Dirty folios in reclaim

- section: Shrinking a folio list
- relevance: 5 - what reclaim writes out has changed over time

What does reclaim do with a dirty file-backed folio, a dirty shmem folio and a dirty anonymous
folio it finds at the tail of the LRU: which of them does it write itself and through which
function, and what flag does it leave on the ones it does not write? Start from `pageout()`.

## reclaim.writeback-in-reclaim: Folios under writeback

- section: Shrinking a folio list
- relevance: 4 - the three cases decide whether reclaim waits

When `shrink_folio_list()` finds a folio under writeback, what are the cases it distinguishes, in
which of them does it wait, and what decides between them? Start from
`writeback_throttling_sane()` and `may_enter_fs()`.

## reclaim.anon-swap-step: Anonymous folios to swap

- section: Shrinking a folio list
- relevance: 4 - several early exits and a split fallback

In `shrink_folio_list()`, what is checked before an anonymous folio is given swap space, and what
happens to a large folio that cannot get contiguous slots? What does the code do to the folio
after `folio_alloc_swap()` succeeds, and why? Start from the call to `folio_alloc_swap()`.

## reclaim.remove-mapping: Detaching from the mapping

- section: Shrinking a folio list
- relevance: 5 - the order of the tests is what prevents data loss

Which locks does `__remove_mapping()` take for a page-cache folio and for a swap-cache folio? In
which order does it test the reference count and the dirty flag, and what does that order
guarantee?

## reclaim.remove-mapping-refcount: Reference count at removal

- section: Shrinking a folio list
- relevance: 5 - a path that holds one more reference than expected makes every removal fail

What reference count must a folio have for `__remove_mapping()` to detach it, and what does the
function leave behind in the slot? Start from `__remove_mapping()`.

## reclaim.workingset-shadows: Shadow entries

- section: Shrinking a folio list
- relevance: 4 - what is packed into them constrains memcg ids and node ids

What does `workingset_eviction()` pack into the value that reclaim leaves in place of an evicted
folio, and what does the packing constrain? Where is the value stored for a page-cache folio and
for a swapped-out folio? Start from `workingset_eviction()`.

## reclaim.refault-decision: Refault decision

- section: Shrinking a folio list
- relevance: 4 - a change to what a shadow entry holds changes which refaulted folios are activated

What does `workingset_refault()` decide from a shadow entry, and what does it do to the folio as a
result? Start from `workingset_refault()`.

# LRU lists and counters

## reclaim.isolation: LRU isolation

- section: LRU lists and counters
- relevance: 4 - the flag and the reference are the protocol

What do `folio_isolate_lru()` and `isolate_lru_folios()` do to a folio's flags and reference count
when they take it off an LRU list, and in what order? What makes them fail to isolate a folio?
Start from `folio_isolate_lru()` and `isolate_lru_folios()`.

## reclaim.isolation-limit: Isolation limit

- section: LRU lists and counters
- relevance: 4 - a reclaimer that skips the limit empties the LRU lists under many parallel allocations

What does `too_many_isolated()` in `mm/vmscan.c` limit, and what does a reclaimer do when the
limit is reached? Start from `too_many_isolated()` in `mm/vmscan.c`.

## reclaim.bounded-lru-scan: Scans under the LRU lock

- section: LRU lists and counters
- relevance: 3 - an unbounded skip loop holds a spinlock with interrupts off

What are the requirements for a loop that filters an LRU list while it holds the LRU lock, in
order to assure safe usage? Name in-tree code that shows it. Start from `isolate_lru_folios()`.

## reclaim.vmstat-counters: Reclaim counters

- section: LRU lists and counters
- relevance: 4 - where the counters live decides which helper updates them

Where are the scan, steal, refill, rotate and demote counters of reclaim kept, as global VM
events, as node statistics or as per-lruvec statistics, and which helper must therefore update
them? How is the counter for the kind of reclaimer selected? Start from `reclaimer_offset()`.

## reclaim.classic-mglru-pairing: Classic and MGLRU accounting

- section: LRU lists and counters
- relevance: 4 - a bug shows only when the other implementation is active

What accounting do `shrink_inactive_list()` and `evict_folios()` each do around their call to
`shrink_folio_list()`? A table that pairs each item of the one with its counterpart in the other.
Which counters does only one of the two update?

# Scan balance, throttling and kswapd

## reclaim.scan-balance: Anon and file balance

- section: Scan balance, throttling and kswapd
- relevance: 4 - the inputs have been reworked more than once

What inputs decide how `get_scan_count()` splits scanning between anonymous and file folios, and
which conditions force one type to be skipped entirely?

## reclaim.memcg-protection: Memory cgroup protection

- section: Scan balance, throttling and kswapd
- relevance: 4 - protection scales the scan, it does not just skip

How do a memory cgroup's min and low settings affect a reclaim pass: where is the effective
protection computed and where is it tested, how does it scale the scan target, and when is low
protection overridden? Start from `mem_cgroup_calculate_protection()` and
`shrink_node_memcgs()`.

## reclaim.throttling: Reclaim throttling

- section: Scan balance, throttling and kswapd
- relevance: 4 - replaces the congestion waits people remember

For what reasons can a reclaimer be put to sleep by `reclaim_throttle()`, for how long and what
wakes it early, and which tasks are never throttled? Start from `enum vmscan_throttle_state`.

## reclaim.kswapd-loop: Background reclaim loop

- section: Scan balance, throttling and kswapd
- relevance: 4 - the termination conditions are subtle

In `balance_pgdat()`, what raises the scanning priority and what ends the loop?

## reclaim.kswapd-sleep: kswapd sleep and wakeup

- section: Scan balance, throttling and kswapd
- relevance: 4 - a wrong sleep check leaves kswapd asleep on an unbalanced node or awake on a balanced one

What does `kswapd_try_to_sleep()` check before kswapd sleeps, and what wakes kswapd? Start from
`kswapd_try_to_sleep()`.

## reclaim.kswapd-failures: kswapd failures and hopeless nodes

- section: Scan balance, throttling and kswapd
- relevance: 4 - the reset condition has been tightened

How does a node come to be treated as one the background reclaimer cannot balance, what do
direct reclaimers and wakeups do differently for such a node, and what resets the state? Start
from `kswapd_failures` in `struct pglist_data`.

## reclaim.kswapd-order-drop: kswapd reclaim order

- section: Scan balance, throttling and kswapd
- relevance: 3 - ignoring it causes massive overreclaim

When does `kswapd_shrink_node()` stop reclaiming for the allocation order that kswapd was woken
for? Which order must the calls to `pgdat_balanced()` that follow use? Start from
`kswapd_shrink_node()` and `pgdat_balanced()`.

## reclaim.zone-skip-consistency: Zones in balance checks

- section: Scan balance, throttling and kswapd
- relevance: 3 - a mismatch means an escape hatch never fires

Which zones does `for_each_managed_zone_pgdat()` leave out? What are the requirements for a loop
over a node's zones in a function of `mm/vmscan.c` that decides whether the node is balanced or
whether direct reclaim may go on, in order to assure safe usage? Start from
`for_each_managed_zone_pgdat()` and `allow_direct_reclaim()`.

# Shrinkers

## reclaim.shrinker-api: Shrinker callbacks and lifetime

- section: Shrinkers
- relevance: 4 - the registration API and the return values are easy to misuse

What must a shrinker's `count_objects` and `scan_objects` callbacks return when there is nothing
to free, when nothing can be freed now, and when reclaim should stop calling? What are the
requirements for the calls to `shrinker_alloc()`, `shrinker_register()` and `shrinker_free()` in
order to assure safe usage, and what keeps a shrinker alive while `do_shrink_slab()` calls it?
Start from `shrinker_alloc()` and `do_shrink_slab()`.

## reclaim.shrinker-flags: NUMA and memcg flags

- section: Shrinkers
- relevance: 4 - a callback that ignores the node or the cgroup it is passed frees the wrong objects

What do `SHRINKER_NUMA_AWARE` and `SHRINKER_MEMCG_AWARE` each change about what a shrinker's
callbacks are passed? Start from `shrink_slab()` in `mm/shrinker.c`.

# Multi-generation LRU

## reclaim.mglru-structure: Generations and tiers

- section: Multi-generation LRU
- relevance: 4 - the vocabulary everything else uses

What do a generation and a tier represent in the multi-generation LRU, and which sequence numbers
in `struct lru_gen_folio` bound the generations? Where in a folio are its generation and its
access count stored? Start from `struct lru_gen_folio`.

## reclaim.mglru-active-generations: Active generations

- section: Multi-generation LRU
- relevance: 4 - the statistics go wrong when a folio changes generation and its size is counted on the wrong side

Which generations does `lru_gen_is_active()` count as active for the statistics? Start from
`lru_gen_is_active()`.

## reclaim.mglru-enable: Runtime switch

- section: Multi-generation LRU
- relevance: 4 - code must behave while folios are on either kind of list

How is the multi-generation LRU switched on and off at run time, what state are the lists in
while the switch is in progress, and how must a path that is only valid for one of the two
implementations test for that? Start from `lru_gen_change_state()`.

## reclaim.mglru-refs-flags: Access tracking flags

- section: Multi-generation LRU
- relevance: 4 - three flags and a bit field are overloaded

How do the referenced flag, the workingset flag and the reference-count bits record accesses
through file descriptors and through page tables under the multi-generation LRU, and does the
code do what the comment says? Start from the comment on `LRU_REFS_FLAGS` in
`include/linux/mmzone.h` and from `lru_gen_set_refs()`.

## reclaim.mglru-tier-bits: Tier bits on generation change

- section: Multi-generation LRU
- relevance: 4 - stale bits inflate access counts

What are the requirements for the folio's access-tracking bits in code that moves a folio to
another generation, in order to assure safe usage? Which of `folio_update_gen()`,
`folio_inc_gen()` and `lru_gen_add_folio()` clear those bits and which keep them? Start from
`folio_update_gen()`, `folio_inc_gen()` and `lru_gen_add_folio()`.

## reclaim.mglru-aging: Generation aging

- section: Multi-generation LRU
- relevance: 4 - two ways of finding accessed folios, with different locking

Which locks do the page table walk in `walk_mm()` and the look-around in `lru_gen_look_around()`
each hold, and what may each therefore do to a folio's generation? When does
`try_to_inc_max_seq()` skip the page table walk or cut it short? Start from
`try_to_inc_max_seq()`, `walk_mm()` and `lru_gen_look_around()`.

## reclaim.mglru-eviction: Eviction and sorting

- section: Multi-generation LRU
- relevance: 4 - the sorting step moves folios without reclaiming them

In eviction under the multi-generation LRU, what does the sorting step do with a folio instead
of isolating it and for which folios, what bounds a scan, and what happens to the folios that
`shrink_folio_list()` rejects? Start from `evict_folios()`, `scan_folios()` and `sort_folio()`.

# Swap slots and the swap cache

## reclaim.swap-slot-state: Per-slot state

- section: Swap slots and the swap cache
- relevance: 5 - the count, the cache and the shadow have been unified

Where is the state of one swap slot kept: whether it is free, swapped out or cached, and its
reference count? Which formats can a slot's value take, and how are they told apart? Start from
`swap_table_get()`.

## reclaim.swap-entry-encoding: Swap entries in page tables

- section: Swap slots and the swap cache
- relevance: 4 - the helpers for non-present entries have been renamed

What type and which helpers does this tree use to read a non-present page table entry and to tell
a swap entry from the other kinds of non-present entry? Start from `include/linux/swapops.h` and
`include/linux/leafops.h`.

## reclaim.swap-count: Swap counts

- section: Swap slots and the swap cache
- relevance: 5 - who may raise a count from zero is a locking rule

Of the functions that raise and lower a swap slot's reference count, which is for a locked
swap-cache folio and which for a bare entry, and what must the caller of each hold? Start from
`folio_dup_swap()` and `swap_put_entries_direct()`.

## reclaim.swap-count-limits: Initial count and overflow

- section: Swap slots and the swap cache
- relevance: 5 - a slot freed before its first count is taken, or a count that wraps, loses data

What count does a freshly allocated swap slot start with, and what keeps such a slot from being
freed? What happens when a count overflows its field? Start from `folio_alloc_swap()`.

## reclaim.swap-cache-api: Swap cache operations

- section: Swap slots and the swap cache
- relevance: 5 - the locking and reference rules are new

A table of the swap cache operations, job to function: look a folio up, add one, delete one and
replace one, with what the caller must hold for each. Then: how many references does the swap
cache hold on a folio, and in which order are the folio lock and the cluster lock taken?

## reclaim.swapcache-identity: Swapbacked, swapcache and mapping

- section: Swap slots and the swap cache
- relevance: 5 - confusing the two flags corrupts the wrong structure

What do `folio_test_swapbacked()` and `folio_test_swapcache()` each return for a shmem folio in
the page cache, a shmem folio in the swap cache and an anonymous folio in the swap cache, and
which of the two must code test to choose between page-cache and swap-cache operations?

## reclaim.swapcache-mapping: Swap cache folio mapping

- section: Swap slots and the swap cache
- relevance: 5 - page-cache operations on the mapping of a swap-cache folio corrupt the wrong structure

What do `folio->mapping` and `folio_mapping()` each give for a folio in the swap cache, and what
may a caller do with the result? Start from `swap_space` in `mm/swap_state.c`.

## reclaim.swap-residency: Swap cache removal conditions

- section: Swap slots and the swap cache
- relevance: 4 - the release test can err in one direction only

Which conditions must hold before `folio_free_swap()` removes a folio from the swap cache? Can its
test for whether the slots are still in use report a slot as in use that is not, or the reverse,
and what does its return value therefore guarantee?

## reclaim.swap-cache-lookup-usage: Swap cache lookup rechecks

- section: Swap slots and the swap cache
- relevance: 5 - a swap entry value can come back naming different data

What are the requirements for using a folio that `swap_cache_get_folio()` returned for a swap
entry read from a page table, in order to assure safe usage? What must be rechecked under the page
table lock when the lookup found nothing? Name in-tree code that does each.

# Swap devices and allocation

## reclaim.swap-device-and-clusters: Swap device and clusters

- section: Swap devices and allocation
- relevance: 4 - what is per device and what is per cluster has moved

What state does `struct swap_info_struct` keep per device and what does `struct swap_cluster_info`
keep per cluster? A table of the swap locks: what each protects and the order they nest in. Start
from `struct swap_info_struct` and from `struct swap_cluster_info` in `mm/swap.h`.

## reclaim.swap-device-pinning: Swap device lifetime

- section: Swap devices and allocation
- relevance: 5 - use after free against swapoff, and the helper that skips the reference is the common one

What does `get_swap_device()` check and take, and what does that keep swapoff from freeing? What
are the requirements for calling `__swap_entry_to_info()` or `__swap_entry_to_cluster()` in order
to assure safe usage? Start from the comments above `get_swap_device()` in `mm/swapfile.c` and
above `swap_cache_has_folio()` in `mm/swap.h`.

## reclaim.swap-alloc: Slot allocation

- section: Swap devices and allocation
- relevance: 4 - the allocator has been rewritten around clusters

What state is a folio in when `folio_alloc_swap()` succeeds and when it fails, and what must the
caller do with a large folio that could not get slots? In what order does the allocator try
devices and clusters?

## reclaim.swap-alloc-local-lock: Allocator local lock

- section: Swap devices and allocation
- relevance: 3 - a sleeping call there is silent unless it really blocks

Which lock does the swap slot allocator hold while it uses `percpu_swap_cluster`, and what may
code that runs under that lock not do? How does `swap_cluster_populate()` proceed when it needs to
do that? Start from `percpu_swap_cluster` and `swap_cluster_populate()`.

## reclaim.swap-io: Swap I/O

- section: Swap devices and allocation
- relevance: 4 - the write and read paths have new plumbing

What do `swap_writeout()` and `swap_read_folio()` try before they touch the device? What are the
requirements for a caller that queues requests in a `struct swap_io_ctx`, in order to assure that
all of the I/O is sent? How does reclaim learn that writing to a swap device needs filesystem
context?

## reclaim.swap-ops: Swap device operations

- section: Swap devices and allocation
- relevance: 4 - a change to swap I/O has to work for every set of operations a device can have

What does a swap device's `struct swap_ops` decide, and what chooses the `struct swap_ops` of a
device? Start from `include/linux/swap_ops.h`.

# Swapping out and in

## reclaim.swap-out-sequence: Swap-out ordering

- section: Swapping out and in
- relevance: 4 - four subsystems each do one step

Between reclaim giving an anonymous folio swap space and the folio's memory being freed, in what
order are the page table entries replaced, the swap count raised, the data written and the
folio removed from the swap cache? What keeps the slots from being freed at each point, and what
is undone when unmapping or writing fails?

## reclaim.swapin-fault: Swap-in at a fault

- section: Swapping out and in
- relevance: 5 - each recheck is there for a race

In `do_swap_page()` for a real swap entry, what is rechecked after the folio is locked and what
after the page table lock is taken, and which race does each recheck close? In what order are the
swap count dropped, the page table entries installed and the folio released from the swap cache?

## reclaim.swapin-read-path: Reading a folio in

- section: Swapping out and in
- relevance: 5 - the two read paths differ in readahead and in the folio sizes they may return

Which functions does `do_swap_page()` call to read in a folio that the swap cache does not hold,
and what decides between them? Start from `do_swap_page()`.

## reclaim.swapin-large: Large folio swap-in

- section: Swapping out and in
- relevance: 4 - the error codes each mean something different

What does `swap_cache_alloc_folio()` return when the target slot is no longer swapped out, when
it already has a folio, and when another slot of a large range is unsuitable, which of these does
it handle itself and how, and what makes a range unsuitable? Start from
`__swap_cache_add_check()`.

## reclaim.swapin-conflict-usage: Retrying a swap-in

- section: Swapping out and in
- relevance: 4 - retrying the same order can loop forever

What does `swap_cache_alloc_folio()` return when a large folio conflicts with a slot in its range,
and what are the requirements for a caller that retries after that return, in order to assure safe
usage? Which callers can never see that return? Name in-tree code that shows the correct form.
Start from `shmem_swap_alloc_folio()`.

## reclaim.shmem-swap: Shmem and swap

- section: Swapping out and in
- relevance: 4 - a shmem folio changes caches under its lock

What must code hold to rely on which of the two caches, the page cache or the swap cache, a shmem
folio is in? What is stored in the page cache in the place of a shmem folio that has moved to the
swap cache, and how is a stale one detected? Start from `shmem_writeout()` and
`shmem_swapin_folio()`.

# Memory cgroup charge

## reclaim.memcg-charge-api: Charging a folio

- section: Memory cgroup charge
- relevance: 5 - what the folio points at has changed

Which function charges a folio at a fault, which on adding to the page cache, which at swap-in and
which for hugetlb? What does a charged folio's `memcg_data` hold, and which reference does the
folio hold through it? Start from `charge_memcg()` and `commit_charge()`.

## reclaim.memcg-limits: Enforcing the limits

- section: Memory cgroup charge
- relevance: 4 - reclaim, retries and the OOM killer all hang off one function

When a charge would exceed the hard limit, for which allocations does `try_charge_memcg()` succeed
regardless, and what does a successful return therefore guarantee about the limit? When does it
invoke the OOM killer?

## reclaim.memcg-high-limit: High limit handling

- section: Memory cgroup charge
- relevance: 4 - the high limit is acted on later and elsewhere, so a charge path cannot rely on it

What does `try_charge_memcg()` do when a charge takes a memory cgroup over its high limit, and
where is the task throttled or made to reclaim for it? Start from `try_charge_memcg()`.

## reclaim.memcg-stock: Per-CPU charge caches

- section: Memory cgroup charge
- relevance: 3 - explains why a removed cgroup lingers

What do the per-CPU charge caches hold, and what reference keeps a cached memory cgroup alive?
When are the caches drained? Start from `consume_stock()` and `drain_all_stock()`.

## reclaim.memcg-uncharge: Uncharging a folio

- section: Memory cgroup charge
- relevance: 4 - the pairing rules and one ordering rule

Where is a folio uncharged on the free path, what must have happened to a large folio before it
is uncharged and why, and which paths transfer a charge instead of uncharging? Start from
`uncharge_folio()` and `folio_unqueue_deferred_split()`.

## reclaim.swap-memcg: Swap accounting

- section: Memory cgroup charge
- relevance: 5 - the record lives in a new place

When a folio is given swap space, which memory cgroup does `__mem_cgroup_try_charge_swap()`
charge, and which when the folio's own one is offline? Where is the owner of each slot recorded,
and when is the swap charge released? Start from `__mem_cgroup_try_charge_swap()`.

## reclaim.swap-memcg-usage: Swap charge and cgroup id

- section: Memory cgroup charge
- relevance: 4 - a mismatch leaks a counter permanently

What are the requirements for the memory cgroup id that swap charging records for a slot and that
swap uncharging later looks up, in order to assure safe usage? Start from
`__mem_cgroup_try_charge_swap()` and `__mem_cgroup_uncharge_swap()`.

# Memory cgroup lookup and lifetime

## reclaim.memcg-lookup: Looking up a folio's cgroup

- section: Memory cgroup lookup and lifetime
- relevance: 5 - the binding can change under a reader

What must a caller hold for the result of `folio_memcg()` to stay the folio's memory cgroup, and
what for the pointer merely to stay valid memory? What do `folio_memcg_check()` and
`get_mem_cgroup_from_folio()` add? Start from the comment above `folio_memcg()` in
`include/linux/memcontrol.h`.

## reclaim.memcg-lruvec-lock: Locking a folio's lruvec

- section: Memory cgroup lookup and lifetime
- relevance: 4 - lock, recheck, and an RCU section that outlives the call

How does `folio_lruvec_lock()` make sure it has locked the right lruvec, what else is held on
return and which function releases it, and how does code that locks many folios in a row avoid
relocking? Start from `folio_lruvec_relock_irq()`.

## reclaim.memcg-offline: Offlining a memory cgroup

- section: Memory cgroup lookup and lifetime
- relevance: 5 - folios no longer pin a dead cgroup the way people remember

When a memory cgroup goes offline, what does `memcg_reparent_objcgs()` move to the parent, and
which locks does it hold while it moves the LRU lists, with and without the multi-generation LRU?
What can `folio_memcg()` return for a folio of that cgroup while the move is in progress? Start
from `memcg_reparent_objcgs()`.

## reclaim.memcg-ids-and-refs: Identifiers and references

- section: Memory cgroup lookup and lifetime
- relevance: 4 - two ids, and a lookup that returns an unpinned pointer

Which numeric identifiers does a memory cgroup have, and how long does each stay valid after the
cgroup is removed? What must a caller of `mem_cgroup_from_private_id()` do to keep using the
result after it leaves the RCU section? Start from `mem_cgroup_from_private_id()`.

# Migration

## reclaim.migrate-api: Migration API

- section: Migration
- relevance: 4 - the return value and the list contents are easy to misread

What does `migrate_pages()` return and what does it leave on the list it was given, after a
partial failure and after an error? What must the caller do with the folios left there? Start from
`migrate_pages()`.

## reclaim.migrate-modes: Blocking by mode

- section: Migration
- relevance: 4 - a caller that cannot sleep must pass a mode that does not block

On what may migration block in each mode of `enum migrate_mode`? Start from
`include/linux/migrate_mode.h`.

## reclaim.migrate-phases: Phases of one migration

- section: Migration
- relevance: 4 - failure handling differs by phase

Migrating one folio is split into an unmap phase and a move phase. What does each do, what state
is recorded between them and where, and what is undone if either fails? Start from
`migrate_folio_unmap()` and `migrate_folio_move()`.

## reclaim.migrate-refcount: Expected references

- section: Migration
- relevance: 4 - extra references make migration fail, not wait

How does migration decide that nobody else is using a folio: which function computes the
expected reference count, where is the count frozen, and what is returned when it does not
match? Start from `folio_migrate_mapping()`.

## reclaim.migrate-entries: Migration entries

- section: Migration
- relevance: 4 - what a faulting thread sees mid-migration

What replaces a page table entry while its folio is being migrated, and what does a thread that
faults on it do? Which state of the old page table entry does `remove_migration_ptes()` restore,
and which does it not? Start from `try_to_migrate()` and `remove_migration_ptes()`.

## reclaim.migrate-callback: The migrate callback

- section: Migration
- relevance: 4 - a filesystem contract

What locks and state are the two folios in when an address space's `migrate_folio` operation is
called, and what must the operation return?

## reclaim.migrate-callback-choice: Ready-made migrate callbacks

- section: Migration
- relevance: 4 - the wrong ready-made callback skips the private data or the buffers of a folio

Which of the ready-made implementations of the `migrate_folio` operation is for which kind of
mapping, and what does migration do for a mapping that provides none? Start from `migrate_folio()`
and `buffer_migrate_folio()` in `mm/migrate.c`.

## reclaim.migrate-callback-sleeps: Sleeping in migrate callbacks

- section: Migration
- relevance: 4 - safe for small folios, a bug for large ones

Which of the generic migration helpers can sleep, and for which folios? What are the requirements
for calling them from a `migrate_folio` callback in order to assure safe usage? Start from
`folio_mc_copy()` and `__buffer_migrate_folio()`.

## reclaim.migrate-rmap-lock-scope: Reverse-map lock across migration

- section: Migration
- relevance: 3 - a lock inversion that only one path can hit

What are the requirements for a caller that passes `TTU_RMAP_LOCKED` to `try_to_migrate()`, in
order to assure safe usage? Name the in-tree caller that does it. Start from `TTU_RMAP_LOCKED`.

## reclaim.migrate-memcg: Charge transfer in migration

- section: Migration
- relevance: 4 - the source folio ends with no charge

How does `mem_cgroup_migrate()` move a folio's memory cgroup charge to the new folio, and what
state does it leave the old folio's `memcg_data` in? What are the requirements for code that
handles the old folio afterwards, in order to assure safe usage? Start from `mem_cgroup_migrate()`
and `migrate_folio_done()`.

## reclaim.migrate-isolation-count: Collecting folios for migration

- section: Migration
- relevance: 3 - an empty list does not mean nothing qualified

What does `collect_longterm_unpinnable_folios()` return, and what does an empty list after it
guarantee about the folios it examined? Start from `collect_longterm_unpinnable_folios()` in
`mm/gup.c`.

# Writeback tags, flags and throttling

## reclaim.writeback-tag-transitions: Tag lifecycle

- section: Writeback tags, flags and throttling
- relevance: 5 - wrong tag handling loses data or livelocks sync

A table of the tags the page cache keeps for writeback: what each means, and the one function
that sets it and the one that clears it, from a folio being dirtied to its writeback ending.
Then: what copies one tag to another and for which kind of sync, and what does starting
writeback do to each tag? Start from `PAGECACHE_TAG_DIRTY` in `include/linux/fs.h`,
`folio_mark_dirty()`, `tag_pages_for_writeback()` and `__folio_start_writeback()`.

## reclaim.writeback-tag-usage: Keeping the to-write tag

- section: Writeback tags, flags and throttling
- relevance: 3 - a sync that revisits a folio needs the tag

What does `__folio_start_writeback()` do with the to-write tag, and what are the requirements for
its caller in order to assure that a data-integrity sync comes back to the folio? Start from
`__folio_start_writeback()`.

## reclaim.writeback-iter: Writeback iteration

- section: Writeback tags, flags and throttling
- relevance: 4 - the old helper and the old callback are gone

Which tag does `writeback_iter()` follow for which kind of writeback, what state is a folio in
when it is handed out, and how are errors and early termination reported? Start from
`wbc_to_tag()`.

## reclaim.writeback-flags: Dirty and writeback flags

- section: Writeback tags, flags and throttling
- relevance: 4 - the order of the flag changes is the protocol

In what order must a writer clear the dirty flag, set the writeback flag, unlock the folio and
end writeback, what does `folio_clear_dirty_for_io()` do to page table entries and accounting,
and how is a folio that could not be written made dirty again? Start from
`folio_redirty_for_writepage()`.

## reclaim.wb-domain-usage: Dirty throttle domains

- section: Writeback tags, flags and throttling
- relevance: 3 - the global domain is wrong when the cgroup domain was selected

What are the requirements for code that is handed a `struct dirty_throttle_control` and reads a
domain's dirty limits, in order to assure safe usage? When may such code read `global_wb_domain`
directly, and which domain must a tracepoint use? Start from `dtc_dom()` and
`domain_dirty_limits()`.

# Model gaps

## reclaim.model-gaps: Other mistakes models make

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
