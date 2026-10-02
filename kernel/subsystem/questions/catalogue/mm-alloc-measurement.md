# Questions: MM Memory Allocation (measurement set)

- guide: mm-alloc.md
- title: MM Memory Allocation

A wide set of questions about kernel memory allocation: GFP masks, the page
allocator, the slab allocator and kmalloc, mempools, vmalloc resizing and the
boot allocator. It is used to measure what a model already knows before
deciding what the built guide should spend its words on. The hand-written guide
it will replace is 3,482 words. Run it with `build-guides.py --no-sources
--check-memory --questions` pointed at this directory. The trimmed set a guide
is built from is `../mm-alloc.md`. Format:
`../../../docs/subsystem-questions.md`.

# Where to look

## alloc.core-files: Core files

- section: Finding your way
- relevance: 4 - internal declarations have moved between headers
- words: 130

Which files hold the GFP bit definitions and the helpers that test a mask, the
page allocator and its mm-internal declarations, the slab allocator and its
internal header, the code shared by all kmalloc caches, mempools, vmalloc, the
boot allocator, zone and watermark initialisation, memory policy, and
allocation profiling? A table.

## alloc.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 130

For each job (allocate pages with a reference, allocate pages without one,
free pages, allocate and free one slab object, kmalloc above the largest cache,
allocate from any context, allocate a physically contiguous range, take an
element from a mempool, resize a vmalloc area, allocate before the page
allocator is up), which function do you start reading from? A table.

## alloc.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - several guarantees are stated only there
- words: 60

Which files under `Documentation/` are the authority on choosing a GFP mask,
on the scoped no-FS and no-IO interface, on allocation profiling, on zones and
nodes, and on boot-time allocation?

# GFP masks

## alloc.gfp-composites: Composite masks

- section: What a mask says
- relevance: 4 - every allocation carries one, and the composition is tree-specific
- words: 130

Give a table for `GFP_ATOMIC`, `GFP_KERNEL`, `GFP_NOWAIT`, `GFP_NOIO`,
`GFP_NOFS` and `GFP_USER`: the modifier bits each is built from, whether the
caller may sleep, and whether it may enter direct reclaim, only wake the
background reclaim thread, or neither. Start from
`include/linux/gfp_types.h`.

## alloc.gfp-sleep-bit: The bit that allows sleeping

- section: What a mask says
- relevance: 4 - the test people write by hand is often the wrong one
- words: 60

Which single bit decides whether an allocation may sleep, what is the pair of
reclaim bits called, and what may a no-IO allocation still reclaim?

## alloc.gfp-retry-modifiers: Retry modifiers

- section: What a mask says
- relevance: 4 - decides whether a NULL check is needed
- words: 110

What do `__GFP_NORETRY`, `__GFP_RETRY_MAYFAIL` and `__GFP_NOFAIL` each promise
about how hard the allocator tries and whether it can return NULL, what do they
need from the other bits in the mask to have any effect, and what does the
allocator do with a no-fail request it cannot honour? Start from the "Reclaim
modifiers" comment in `include/linux/gfp_types.h`.

## alloc.gfp-watermark-modifiers: Reserve access

- section: What a mask says
- relevance: 3 - says how deep into the reserves a request can go
- words: 100

How do `__GFP_HIGH`, `__GFP_MEMALLOC`, `__GFP_NOMEMALLOC`, a request that cannot
block, a task with `PF_MEMALLOC` and an OOM victim each change how far below
the minimum watermark an allocation may go? Name the internal allocation flag
each becomes. Start from `alloc_flags_slowpath()` and `__gfp_pfmemalloc_flags()`.

## alloc.gfp-zone-bits: Zone selection

- section: What a mask says
- relevance: 3 - a constraint that is dropped is silent
- words: 90

Which bits select the physical zone, how is the highest usable zone computed
from them, which combinations are rejected, and is the bit that forbids falling
back to another node part of the same mask constant? Start from `GFP_ZONEMASK`
and `gfp_zone()`.

## alloc.pool-placement-usage: Serving from a private pool

- section: What a mask says
- relevance: 2 - only code that intercepts allocations is exposed
- words: 80

Code that intercepts allocations and serves some of them from memory it set
aside earlier cannot honour every placement request. What usage is unsafe, and
which bits and cache flags does correct in-tree code test before serving from
its pool? Start from `__kfence_alloc()` and `__alloc_contig_verify_gfp_mask()`.

## alloc.movable-contract: Movable allocations

- section: What a mask says
- relevance: 3 - an unmovable page in a movable block defeats compaction and hot-unplug
- words: 70

What does passing `__GFP_MOVABLE` promise about the pages, how does the bit
together with `__GFP_RECLAIMABLE` choose a free list, and what usage by a
driver that registers `struct movable_operations` is unsafe? Start from
`gfp_migratetype()`.

## alloc.gfp-scope: Scoped constraints

- section: Context and scope
- relevance: 4 - the mask a function receives is not the mask the allocator uses
- words: 100

Which scoped interfaces change the GFP mask of every allocation a task makes
inside the scope, which task flag does each set, which bits does each remove,
and where in the page allocator and in the slab allocator is the scope applied?
Start from `current_gfp_context()` and `memalloc_nofs_save()`.

## alloc.gfp-mask-tests: Testing a mask

- section: Context and scope
- relevance: 3 - a comparison against a composite misfires inside a scope
- words: 90

Code handed a GFP mask sometimes needs to know whether it may sleep or may take
a spinning lock. Which helpers answer that and which bits does each test? What
way of testing a mask is unsafe once a scoped constraint has narrowed it, and
which in-tree comparisons against a composite constant are nevertheless
correct? Start from `include/linux/gfp.h`.

## alloc.kswapd-wakeup-locks: Waking background reclaim

- section: Context and scope
- relevance: 3 - a mask that cannot sleep can still take locks
- words: 110

Which bit asks for the background reclaim thread to be woken, which locks can
the wakeup take, and which callers must therefore not pass it? Name in-tree
code that adds the bit only under a condition, and say whether
`gfp_nested_mask()` keeps or drops it. Start from `wakeup_kswapd()` and
`fill_pool()` in `lib/debugobjects.c`.

## alloc.atomic-contexts: Non-blocking allocation contexts

- section: Context and scope
- relevance: 3 - the answer differs on a preemptible-RT kernel
- words: 80

Under which lock types and preemption states is a non-blocking allocation from
the page or slab allocator allowed, on a preemptible-RT kernel and otherwise,
and what should code use when it cannot meet that? Start from
`Documentation/locking/locktypes.rst` and
`Documentation/core-api/memory-allocation.rst`.

## alloc.reclaim-reentry: Blocking allocation under a lock

- section: Context and scope
- relevance: 4 - the deadlock needs memory pressure to show
- words: 90

What goes wrong when a blocking allocation is made while holding a lock that
reclaim, writeback or a shrinker can also take, how does lockdep learn about
the dependency without memory pressure, and what are the accepted ways out?
Start from `fs_reclaim_acquire()` and `might_alloc()`.

## alloc.gfp-propagation: Wrappers that change a mask

- section: Context and scope
- relevance: 3 - dropping the caller's bits changes context silently
- words: 60

When a helper takes the caller's GFP mask and adds or removes bits of its own,
what usage is unsafe and what is correct? Name in-tree helpers that
deliberately narrow or widen a caller's mask. Start from `kmalloc_gfp_adjust()`
and `mempool_adjust_gfp()`.

## alloc.nowait-error-code: Failure under a no-wait request

- section: Context and scope
- relevance: 2 - callers treat the two error codes differently
- words: 50

When a path that was asked not to wait fails to allocate, which error code do
its callers expect and why? Start from the `FGP_NOWAIT` handling in
`__filemap_get_folio_mpol()`.

## alloc.memcg-opt-in: Opting in to cgroup charging

- section: Charging a cgroup
- relevance: 3 - an uncharged allocation lets a container exceed its limit
- words: 80

Which two ways opt a slab allocation in to memory cgroup charging, where in the
slab allocation path is the charge made, how are page allocations with the
accounting bit charged, and is an object from an accounted cache charged when
the call's mask lacks the bit? Start from `memcg_slab_post_alloc_hook()` and
`__memcg_kmem_charge_page()`.

## alloc.active-memcg: Choosing the cgroup

- section: Charging a cgroup
- relevance: 3 - the default is the current task, which is wrong for work done on behalf of others
- words: 90

How does the charge path choose which cgroup pays for a kernel allocation,
which interface overrides the choice for a stretch of code and how is the
previous value restored, which kinds of caller need it, and in which contexts
is the charge skipped? Start from `set_active_memcg()` and
`current_obj_cgroup()`.

## alloc.vmstat-node-vs-memcg: Node and cgroup statistics

- section: Charging a cgroup
- relevance: 3 - the helpers differ in which counters they touch
- words: 90

For `mod_node_page_state()`, `mod_lruvec_state()`, `lruvec_stat_mod_folio()`,
`mod_lruvec_page_state()` and `mod_lruvec_kmem_state()`: which update only the
node counter, which also the memory cgroup's, and what decides it when the
folio or object has no cgroup? A table.

## alloc.deferred-charge-stats: Statistics across a late charge

- section: Charging a cgroup
- relevance: 2 - one or two paths change a folio's cgroup after allocation
- words: 70

When memory is allocated uncharged, counted in a statistic, and only later
charged to a cgroup, what must the charging path do to the counters so that
the free path does not underflow one? Start from `kmem_cache_charge()` in
`mm/slub.c`.

# The page allocator

## alloc.page-alloc-layers: Layers of the page allocator

- section: Entry and layers
- relevance: 4 - the layer decides the reference count and the policy applied
- words: 120

List the layers a request passes through from `alloc_pages()` or
`folio_alloc()` down to a page coming off a free list, naming the function at
each layer and what it adds (memory policy, reference count, scope and cpuset,
fast path, slow path, per-CPU list, buddy). Start from `alloc_pages_mpol()` and
`__alloc_frozen_pages_noprof()`.

## alloc.noprof-wrappers: Profiling wrappers

- section: Entry and layers
- relevance: 3 - a new wrapper written the old way is attributed to the wrong line
- words: 80

What does the `_noprof` suffix on an allocation function mean, what does the
macro of the plain name do, how must a new function that wraps an allocator be
written so that allocations are attributed to its callers, and how does an
allocation made by the profiling code itself avoid recursion? Start from
`alloc_hooks()` and `Documentation/mm/allocation-profiling.rst`.

## alloc.frozen-pages: Pages without a reference

- section: Entry and layers
- relevance: 4 - the two families look alike and differ by one in the count
- words: 100

Which page allocator functions hand back a page whose reference count is zero,
where are they declared, which function raises the count to one, which frees
such a page, and which in-tree users ask for pages that way? Say what the bulk
and the contiguous-range allocators return. Start from `mm/page_alloc.h`.

## alloc.frozen-usage: Using frozen pages

- section: Entry and layers
- relevance: 4 - nothing in a diff shows which kind a pointer is
- words: 70

What usage of a page obtained with a zero reference count is unsafe, and what
that looks similar is correct? Name in-tree code that converts one kind to the
other. Start from `set_page_refcounted()`.

## alloc.alloc-flags: Internal allocation flags

- section: Entry and layers
- relevance: 4 - the flag names a reader remembers may have changed
- words: 130

Give a table of the internal `ALLOC_` flags the page allocator passes between
its functions, saying what each allows or forbids and what sets it, and say
which of them an outside caller may pass in. Which structure carries the
parameters that stay fixed for one request? Start from `mm/page_alloc.h`.

## alloc.fresh-page-state: State of a fresh page

- section: Entry and layers
- relevance: 3 - users that overlay the page structure inherit what is left
- words: 90

What does the allocator set up in a page before handing it out (reference
count, private field, poisoning and tags, zeroing, owner tracking, compound
metadata), in which function, and which fields of the page structure does it
leave as they were? Start from `prep_new_page()` and `post_alloc_hook()`.

## alloc.high-order-noncompound: High-order pages without compound metadata

- section: Entry and layers
- relevance: 3 - freeing part of one or freeing it with the wrong order corrupts the free lists
- words: 90

What does a high-order allocation without `__GFP_COMP` return, what must be
done before its pages are freed or referenced one by one, and what does
`__free_pages()` do when someone else still holds a reference on the first
page? Start from `split_page()` and `alloc_pages_exact()`.

## alloc.contig-alloc: Contiguous ranges

- section: Entry and layers
- relevance: 3 - CMA, hugetlb and virtio-mem all depend on it
- words: 100

Which functions allocate a physically contiguous range of pages, what do they
do to the pageblocks in the range while they work, which GFP bits do they
accept, and what do the frozen forms return? Start from `alloc_contig_range()`
and `alloc_contig_pages()`.

## alloc.slowpath-order: Slow path steps

- section: The slow path
- relevance: 4 - a change has to go in the right place in the sequence
- words: 130

List in order what `__alloc_pages_slowpath()` tries after the fast path fails,
from recomputing the allocation flags to the OOM killer, naming the function
for each step, and say which watermark the fast path and the slow path each
test against.

## alloc.failure-rules: Requests that can fail

- section: The slow path
- relevance: 4 - decides whether error handling is dead code or missing
- words: 100

Which page allocation requests can return NULL and which retry without bound:
by order relative to `PAGE_ALLOC_COSTLY_ORDER`, by whether the caller can
direct-reclaim, by the retry modifiers, and for an order above the maximum?
When is the OOM killer not invoked? Start from `__alloc_pages_may_oom()`.

## alloc.slowpath-retry: Backward jumps in the slow path

- section: The slow path
- relevance: 3 - a retry that changes nothing loops forever and blocks the OOM killer
- words: 90

What must be true of a backward jump to the retry label in the slow path for
the loop to terminate, which retries are one-shot and how is each guarded, and
which are deliberately unbounded? Start from `__alloc_pages_slowpath()`.

## alloc.slowpath-restart: Stale zone iteration

- section: The slow path
- relevance: 3 - the cached starting zone can go stale while looping
- words: 80

What does a retry in the slow path reuse that a restart recomputes, which
outside changes make it stale, and where must a repeated retry sit relative to
the checks that detect them? Start from `check_retry_cpuset()` and
`check_retry_zonelist()`.

## alloc.watermarks: Watermark levels

- section: Watermarks
- relevance: 4 - reclaim and allocation both steer by them
- words: 100

Which watermark levels does a zone have, where are they stored, how are they
computed from the sysctls, what is watermark boosting and what triggers it, and
which accessor should code use to read a level? Start from
`__setup_per_zone_wmarks()` and `boost_watermark()`.

## alloc.watermark-check: The watermark test

- section: Watermarks
- relevance: 4 - the formula has terms people forget
- words: 110

What does `__zone_watermark_ok()` compute: which pages count as free, what is
subtracted as unusable, how do the reserve-access flags lower the mark, and
what more is required for an order above zero? How do `zone_watermark_ok()` and
`zone_watermark_fast()` differ from it?

## alloc.lowmem-reserve: The low-memory reserve

- section: Watermarks
- relevance: 4 - the array's indices are read backwards more often than not
- words: 80

What does `zone->lowmem_reserve[j]` protect and from whom, how does it enter
the watermark test, what is a zone's entry for its own index, and what reading
of the array is wrong? Start from `setup_per_zone_lowmem_reserve()`.

## alloc.vmstat-drift: Per-CPU counter drift

- section: Watermarks
- relevance: 3 - on many CPUs the error exceeds the gap between watermarks
- words: 90

Which read of a zone's free page count leaves out the per-CPU deltas and which
includes them, which callers need the exact one and how do they decide when to
pay for it, and which deliberately use the cheap one? Start from
`zone_page_state_snapshot()`, `percpu_drift_mark` and `pgdat_balanced()`.

## alloc.watermark-init-order: Watermarks early in boot

- section: Watermarks
- relevance: 3 - a zero watermark passes every test
- words: 60

When during boot are the zone watermarks first set, what do watermark tests
return before then, and what must code that can run earlier do about it? Start
from `init_per_zone_wmark_min()`.

## alloc.pcp-lists: Per-CPU page lists

- section: Free lists
- relevance: 4 - most allocations and frees never reach the buddy lists
- words: 100

How are the per-CPU page lists organised: which orders and migrate types they
hold, what `high` and `batch` mean and how they adapt, what protects the lists,
and when pages move between them and the buddy lists? Start from
`struct per_cpu_pages`, `rmqueue_pcplist()` and `free_frozen_page_commit()`.

## alloc.pcp-lock-wrappers: Locking a per-CPU list

- section: Free lists
- relevance: 3 - a bare lock call is wrong on uniprocessor and on RT
- words: 90

Which wrappers take the lock of a per-CPU page list, what do they do besides
locking, what happens on a uniprocessor build, and what usage of the lock
without them is unsafe? Start from `pcp_spin_trylock()` and
`pcp_spin_lock_nopin()`.

## alloc.buddy-lists: Buddy free lists

- section: Free lists
- relevance: 3 - what a free page looks like to code that finds one by PFN
- words: 90

How is a free page recorded in the buddy allocator: where its order is kept,
how it is marked, which lock covers that, and what may code that holds no lock
conclude from reading them? Start from `buddy_order()`, `buddy_order_unsafe()`
and `__free_one_page()`.

## alloc.migratetype-fallback: Migrate type fallback

- section: Free lists
- relevance: 3 - the fallback code has been rewritten and renamed
- words: 110

When the free list for the requested migrate type is empty, in what order does
`__rmqueue()` try the alternatives, what is the difference between claiming a
whole pageblock and stealing one page, and what is remembered between calls
when a batch is refilled under one hold of the zone lock? Start from
`find_suitable_fallback()` and `try_to_claim_block()`.

## alloc.pageblock-flags: Pageblock flags

- section: Free lists
- relevance: 3 - a page larger than a pageblock covers several
- words: 90

What is recorded per pageblock, how is isolation represented, which function
sets the migrate type of one pageblock and which must be used for a page that
spans several, and what goes wrong if the free list a page sits on disagrees
with its pageblock's type? Start from `enum pageblock_bits` and
`set_pageblock_migratetype()`.

## alloc.free-path: Freeing pages

- section: Free lists
- relevance: 4 - the entry points differ in what they do to the reference count
- words: 110

List the layers a page passes through when it is freed, from `__free_pages()`
or `folio_put()` to the buddy lists: which function drops the reference, which
prepares and checks the page, when it goes to a per-CPU list and when straight
to the buddy, and what the internal free flags ask for. Start from
`free_frozen_pages()` and `free_pages_prepare()`.

## alloc.free-page-checks: Checks on free and on allocation

- section: Free lists
- relevance: 3 - leftover state in the page structure is reported here
- words: 80

Which fields and flags of a page must be clear when it is freed, which checks
run always and which only with debugging enabled, and what is reported when one
fails? Start from `free_page_is_bad()` and `PAGE_FLAGS_CHECK_AT_FREE`.

## alloc.nolock-page-alloc: Any-context page allocation

- section: Any-context allocation
- relevance: 4 - a newer interface with a narrow contract
- words: 110

Which entry points allocate pages from any context, NMI and re-entry from
inside the allocator included? Which GFP bits may the caller pass and which are
added for it, which orders are allowed, when does it give up without trying,
and which parts of the normal path does it skip? Start from
`alloc_pages_nolock()` and `gfp_nolock` in `mm/page_alloc.c`.

## alloc.nolock-usage: Locks on the trylock-only path

- section: Any-context allocation
- relevance: 4 - one unconditional lock breaks every caller
- words: 100

What may a helper reachable from `get_page_from_freelist()` not do when the
request is trylock-only, how does it find out, and which helpers take a lock
with no such test and are nevertheless correct? Why must a bail-out be for a
transient condition only? Start from `ALLOC_NOLOCK` and
`alloc_nolock_allowed()`.

## alloc.nolock-free: Any-context freeing

- section: Any-context allocation
- relevance: 3 - the page can sit on a side list until someone else frees
- words: 80

Which functions free pages from any context, what happens to the page when the
per-CPU or zone lock cannot be taken, and who finishes the job later? Start
from `free_pages_nolock()` and `FPI_NOLOCK`.

## alloc.mempolicy-vs-node: Policy-aware and node-specific allocation

- section: Nodes
- relevance: 3 - swapping one for the other silently moves pages to other nodes
- words: 90

Which page and folio allocation entry points apply the task's memory policy,
which apply a VMA's, and which bypass both? What conversion between them is
unsafe, and how does correct code choose when it is given a node id that may be
`NUMA_NO_NODE`? Start from `alloc_pages_node()`, `vma_alloc_folio()` and
`___kmalloc_large_node()`.

## alloc.node-id-validation: Node ids from outside

- section: Nodes
- relevance: 3 - the lookup has no bounds check
- words: 50

What must be checked about a node id that comes from user space or firmware
before it is passed to `NODE_DATA()` or to an allocation function? Name in-tree
code that does it. Start from `do_pages_move()`.

## alloc.node-iteration: Iterating over nodes

- section: Nodes
- relevance: 3 - online is not the same as having memory
- words: 80

Which node iterators include nodes without memory, which should an allocation
loop use, what is the upper bound for a raw loop over node ids, and what is
available before the node states are populated at boot? Start from
`for_each_node_state()` and `nr_node_ids`.

## alloc.memoryless-nodes: Memoryless nodes

- section: Nodes
- relevance: 3 - only fails on hardware few people test on
- words: 70

What do `numa_node_id()` and `numa_mem_id()` each return on a CPU whose node
has no memory, and what can a lookup of the slab allocator's per-node structure
return there? Start from `get_node()` and `get_from_partial_node()` in
`mm/slub.c`.

## alloc.user-page-zeroing: Zeroing pages for user space

- section: Special cases
- relevance: 3 - wrong only on architectures with aliasing caches
- words: 70

How does zeroing through `__GFP_ZERO` differ from zeroing with
`clear_user_highpage()` or `folio_zero_user()`, on which architectures does the
difference matter, and which helper tells a caller that it must zero for itself?
Start from `user_alloc_needs_zeroing()`.

## alloc.direct-map-restore: Pages removed from the direct map

- section: Special cases
- relevance: 2 - a few users, but the ordering error is a crash in an unrelated task
- words: 60

When a page has been removed from the kernel's direct map, in what order must
restoring the mapping and freeing the page happen, and why? Name in-tree code
that shows it. Start from `set_direct_map_invalid_noflush()` and
`mm/secretmem.c`.

## alloc.static-key-hotplug: Static keys near the allocator

- section: Special cases
- relevance: 2 - deadlocks only during CPU bring-up
- words: 60

Which static key operations take the CPU hotplug lock and which take nothing,
what goes wrong when the first kind is called from an allocation path, and what
are the alternatives? Start from `static_branch_enable()`.

# The slab allocator

## alloc.slab-architecture: Layers of the slab allocator

- section: Structure
- relevance: 5 - the per-CPU layer a reader remembers may not be the one in this tree
- words: 130

Describe the layers an object passes through in the slab allocator, from the
per-CPU cache down to the page allocator: what the per-CPU structure holds,
what is shared per node, where partially used slabs are kept, and what happened
to per-CPU slabs and per-CPU partial lists. Start from
`struct slub_percpu_sheaves`, `struct node_barn` and `struct kmem_cache_node`
in `mm/slub.c`.

## alloc.slab-struct: The slab descriptor

- section: Structure
- relevance: 4 - it is laid over the page structure
- words: 100

What are the fields of `struct slab`, which fields of `struct page` does each
share storage with, how does the build check the layout, how is a slab page
told from any other page, and what do the slab's own flag bits mean? Start from
`mm/slab.h` and `enum slab_flags`.

## alloc.slab-overlay-init: Initialising the slab descriptor

- section: Structure
- relevance: 3 - fields under a config option are invisible in most builds
- words: 70

Which fields of a new slab does the slab allocator have to initialise itself
because the page allocator leaves them as they were, where is that done, and
what usage when adding a field is unsafe? Start from `allocate_slab()`.

## alloc.slab-locks: Slab locks

- section: Structure
- relevance: 4 - the order is written down and lockdep does not see all of it
- words: 100

List the slab allocator's locks in order, say what each protects and what kind
of lock it is, and say how interrupts and preemption are handled around each
and what differs on a preemptible-RT kernel. Start from the comment at the top
of `mm/slub.c`.

## alloc.slab-alloc-path: Slab allocation path

- section: Structure
- relevance: 4 - a change has to know which layer it is in
- words: 120

List the steps an allocation takes from `kmem_cache_alloc()` to a new slab,
naming the function at each: the per-CPU fast path, refilling from the node,
taking from a partial slab, allocating a new slab. Say where the NUMA node
request and a request served from emergency reserves are honoured. Start from
`slab_alloc_node()` and `___slab_alloc()`.

## alloc.slab-free-path: Slab free path

- section: Structure
- relevance: 4 - the fast path is no longer a compare-and-exchange on a per-CPU slab
- words: 120

List the steps a free takes from `kfree()` or `kmem_cache_free()`: finding the
cache, the hooks, the per-CPU fast path, what happens to an object from a
remote node or when the per-CPU cache is full, and the slow path that puts a
slab back on the partial list or discards it. Start from `slab_free()`,
`free_to_pcs()` and `__slab_free()`.

## alloc.slab-hooks: Allocation and free hooks

- section: Structure
- relevance: 3 - a specialised path that skips one leaves a tool out of step
- words: 100

Which hooks run on a slab object after allocation and before free (KASAN,
KMSAN, kmemleak, zeroing, allocation tags, cgroup charge), in which functions,
and when a late hook fails what must the abort path undo? Start from
`slab_post_alloc_hook()`, `slab_free_hook()` and `memcg_alloc_abort_single()`.

## alloc.slab-freepointer: Free pointers

- section: Structure
- relevance: 3 - a raw store works until hardening or tagging is enabled
- words: 90

Where does a free object keep the pointer to the next free object, how is it
encoded under `CONFIG_SLAB_FREELIST_HARDENED`, what must code in `mm/slub.c`
that touches a freed object do about KASAN tags, and which usage is unsafe?
Start from `get_freepointer()` and `set_freepointer()`.

## alloc.slab-obj-exts: Per-object extensions

- section: Structure
- relevance: 3 - the field shares storage with the page's cgroup word
- words: 110

What is the per-object extension vector of a slab, what uses it, where is it
stored and what do its low bits mean, when and with which flags is it
allocated, and what must be true of the field when the slab's pages go back to
the page allocator? Start from `struct slabobj_ext`, `alloc_slab_obj_exts()`
and `free_slab_obj_exts()`.

## alloc.kmalloc-caches: kmalloc caches

- section: kmalloc
- relevance: 4 - which cache serves a request decides its neighbours
- words: 120

How is a kmalloc request mapped to a cache: which cache types exist and which
GFP bits select them, what the size classes are, what partitions the normal
caches and on what key, where the largest cache ends, and how a larger request
is served and later recognised by `kfree()`. Start from `kmalloc_type()`,
`kmalloc_caches` and `KMALLOC_MAX_CACHE_SIZE`.

## alloc.kmalloc-alignment: kmalloc alignment

- section: kmalloc
- relevance: 4 - reviewers keep reporting a guarantee as an accident
- words: 100

What alignment does `kmalloc()` guarantee, for a power-of-two size and for
other sizes, where is that documented, how is it enforced when the caches are
created, and do the debugging options (red zones, user tracking, KASAN) weaken
it? Start from `create_boot_cache()` and `calculate_sizes()`.

## alloc.kmalloc-page-ownership: Pages behind kmalloc memory

- section: kmalloc
- relevance: 4 - the buffer shares its page with strangers
- words: 120

What usage of the page behind a kmalloc buffer is unsafe (references, page
flags, other page fields, mapping to user space, splicing into the network
stack), and what that looks similar is correct (address conversion,
scatterlists, DMA mapping)? What is the reference count of a slab page? Start
from `sendpage_ok()` and `sg_set_buf()`.

## alloc.kmalloc-zone-bits: Zone bits passed to kmalloc

- section: kmalloc
- relevance: 3 - one of the zone bits selects a cache and another is silently dropped
- words: 90

What does kmalloc do with each of the zone bits in the mask: which select a
cache, which are stripped and with what warning, and when is the warning not
seen? Start from `KMALLOC_NOT_NORMAL_BITS`, `GFP_SLAB_BUG_MASK` and
`kmalloc_fix_flags()`.

## alloc.typed-helpers: Typed allocation helpers

- section: kmalloc
- relevance: 3 - new code uses them and a reader may not recognise them
- words: 80

Which helpers allocate an object, an array or a structure with a flexible array
by type rather than by size, what do they return, what mask do they use when
none is given, and how do they and the older array helpers guard against
overflow? Start from `kmalloc_obj()` in `include/linux/slab.h`.

## alloc.krealloc-zeroing: Zeroing in krealloc

- section: kmalloc
- relevance: 3 - reviewers ask for a test that does not belong here
- words: 90

When `krealloc()` can resize in place, which bytes does it zero on a grow and
on a shrink, which of the init-on-alloc and init-on-free settings does it
consult, and how does it know the size the caller last asked for? Start from
`__do_krealloc()`.

## alloc.kvmalloc: kvmalloc

- section: kmalloc
- relevance: 3 - the fallback has its own rules about masks and contexts
- words: 90

How does `kvmalloc()` decide between kmalloc and vmalloc, how does it change
the caller's mask for the first attempt, which masks make it skip the fallback,
and from which contexts may `kvfree()` be called? Start from
`__kvmalloc_node_noprof()` and `kmalloc_gfp_adjust()`.

## alloc.kmalloc-nolock: Any-context kmalloc

- section: Any-context slab
- relevance: 4 - a newer interface with a narrow contract
- words: 110

What does `kmalloc_nolock()` promise and require: the contexts it may be called
from, the GFP bits it accepts, the sizes it serves, when it returns NULL without
trying, and how the slab slow path tells such a request from an ordinary one?
Start from `SLAB_ALLOC_NOLOCK` and `alloc_flags_allow_spinning()` in
`mm/slab.h`.

## alloc.nolock-free-pairing: Pairing any-context allocation and free

- section: Any-context slab
- relevance: 4 - the wrong pairing leaves tracking tools out of step
- words: 90

Which free functions may follow `kmalloc_nolock()` and which allocations may be
freed with `kfree_nolock()`? What usage is unsafe and why, and name in-tree code
that frees such objects with the ordinary functions.

## alloc.slub-nolock-retry: Retrying without spinning

- section: Any-context slab
- relevance: 3 - a trylock can fail every time
- words: 60

In the slab slow path, what must a jump back to retry do when the request may
not spin, and why can a trylock there fail deterministically? Start from
`___slab_alloc()`.

## alloc.kmemleak-registration: Leak tracking

- section: Any-context slab
- relevance: 3 - the test changed from the mask to a separate flag word
- words: 100

Which slab allocations does the allocator not register with kmemleak, and what
does it test to decide? What do `kmemleak_not_leak()`, `kmemleak_ignore()`,
`kmemleak_free()` and `kmemleak_no_scan()` do with an object that was never
registered, and why must kmemleak calls still be skipped on a path that may not
spin?

## alloc.cache-create: Creating a cache

- section: Caches
- relevance: 3 - the creation interface has changed shape
- words: 100

How is a slab cache created in this tree: what does `struct kmem_cache_args`
carry, which older entry points remain as wrappers, when is a new cache merged
with an existing one and what prevents it, and what does the user-copy region
restrict? Start from `__kmem_cache_create_args()` and `slab_unmergeable()`.

## alloc.typesafe-by-rcu: Type-safe-by-RCU caches

- section: Caches
- relevance: 4 - the flag delays freeing the slab, not the object
- words: 90

What does `SLAB_TYPESAFE_BY_RCU` guarantee and what does it not, what must a
lockless reader do after finding an object in such a cache, what may a
constructor be relied on for, and what usage is unsafe? Start from the comment
at the flag's definition in `include/linux/slab.h`.

## alloc.cache-destroy: Destroying a cache

- section: Caches
- relevance: 3 - module unload with frees still in flight
- words: 80

What does `kmem_cache_destroy()` do when objects are still allocated, what does
it wait for when frees were deferred through RCU, and what must a module do
before destroying a cache whose objects it frees with `kfree_rcu()`?

## alloc.kfree-rcu: Deferred freeing

- section: Caches
- relevance: 3 - the batching moved into the slab allocator
- words: 90

What path does `kfree_rcu()` take in this tree: where objects are batched, when
it falls back, what the one-argument form requires of the caller, and which
barrier waits for everything queued? Start from `kvfree_call_rcu()` and
`__kfree_rcu_sheaf()`.

# Other allocators

## alloc.mempool-guarantee: Mempool guarantees

- section: Mempools
- relevance: 4 - decides whether a NULL check is dead code or a missing one is a crash
- words: 80

With which GFP masks can `mempool_alloc()` return NULL and with which does it
wait until it succeeds, and what does that mean for error handling at the call
site? Start from `mempool_alloc_noprof()` in `mm/mempool.c`.

## alloc.mempool-internals: Mempool mechanics

- section: Mempools
- relevance: 3 - the mask the backing allocator sees is not the caller's
- words: 100

How does a mempool work: what it keeps in reserve, how `mempool_alloc()`
changes the caller's mask before calling the backing allocator and why, in what
order it tries the backing allocator and the reserve, where `mempool_free()`
puts an element, and what the preallocated and bulk forms are for. Start from
`mempool_adjust_gfp()` and `mempool_alloc_preallocated()`.

## alloc.vmalloc-gfp: vmalloc and GFP masks

- section: vmalloc
- relevance: 3 - the page-table allocations underneath do not take the caller's mask
- words: 90

Which GFP masks does vmalloc support, how are no-FS and no-IO requests honoured
given that page tables are allocated underneath, which bits are rejected or
fixed up, and from which contexts may `vfree()` be called? Start from
`__vmalloc_node_range_noprof()` and `vmalloc_fix_flags()`.

## alloc.vrealloc-zeroing: Zeroing in vrealloc

- section: vmalloc
- relevance: 3 - the rule differs from krealloc's
- words: 90

When `vrealloc()` resizes in place, which bytes does it zero on a shrink and on
a grow, which of the init-on-alloc and init-on-free settings does it consult
and why both, and which field records the size the caller last asked for? Start
from `vrealloc_node_align_noprof()`.

## alloc.vrealloc-kasan: KASAN in vrealloc

- section: vmalloc
- relevance: 2 - one function
- words: 50

What alignment do the KASAN poison and unpoison functions require, why does an
in-place vmalloc resize not meet it, and which helper handles that? Start from
`kasan_vrealloc()`.

## alloc.memblock-conventions: Memblock range parameters

- section: Boot
- relevance: 3 - both conventions use the same type, so the compiler cannot help
- words: 70

Which memblock functions take a base and a size and which take a start and an
end, and what mistake does that invite? Start from `memblock_add()` and
`memmap_init_reserved_range()` in `mm/memblock.c`.

## alloc.memblock-lifetime: Memblock lifetime

- section: Boot
- relevance: 3 - calling it too late or keeping a pointer too long
- words: 90

When is memblock usable, what do its allocation functions do on failure, when
is memory handed to the page allocator, what happens to memblock's own data and
code after boot, and how must memory obtained from it be freed once the page
allocator is up? Start from `memblock_alloc()`, `memblock_free_all()` and
`__init_memblock`.

## alloc.boot-stages: Allocators during boot

- section: Boot
- relevance: 3 - each allocator has a first moment it may be used
- words: 90

In what order do the boot allocator, the page allocator, the slab allocator and
vmalloc become usable during boot, how can code ask whether slab is up, and
which GFP bits are masked off allocations until the scheduler is running?
Start from `mm_core_init()`, `slab_is_available()` and `gfp_allowed_mask`.

## alloc.early-boot-globals: Globals not yet set

- section: Boot
- relevance: 2 - a few call sites
- words: 60

Which mm globals (the top of low memory, zone boundaries, node states) are not
yet valid early in boot, which function sets them, and what should early code
use instead? Start from `free_area_init()` and `memblock_end_of_DRAM()`.

# Changing the implementation

## alloc.change-page-alloc: Changing the page allocator

- section: What a change must preserve
- relevance: 3 - the allocator has users that depend on its internals
- words: 100

What must a change to the page allocator keep working besides allocation
itself: the trylock-only path, compaction and page isolation, memory hotplug,
CMA, free page reporting, tracepoints and counters user space reads, and the
debugging options that hook allocation and free? Name the tests that exercise
it.

## alloc.change-slab: Changing the slab allocator

- section: What a change must preserve
- relevance: 3 - several configurations compile different paths
- words: 100

What must a change to the slab allocator keep working besides the fast path:
the debugging path, the tiny configuration, preemptible-RT, the any-context
path, KFENCE, KASAN, kmemleak, cgroup charging and allocation profiling, memory
hotplug, and sysfs? Name the tests that exercise it. Start from
`lib/tests/slub_kunit.c`.
