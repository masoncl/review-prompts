# Questions: MM Memory Allocation

- guide: mm-alloc.md
- title: MM Memory Allocation

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/mm-alloc-measurement.md` is the
wider set the readers were measured on and `catalogue/mm-alloc-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## alloc.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## alloc.core-files: Core files

- section: Finding your way
- relevance: 4 - internal declarations have moved between headers

A table and nothing else, job to file: the GFP bit definitions; the helpers that test a mask; the
page allocator; its mm-internal declarations (the internal flags, the allocation context, the
functions that return pages without a reference); the slab allocator and its internal header; the
code shared by all kmalloc caches; mempools; vmalloc; the boot allocator; zone and watermark
initialisation; memory policy; allocation profiling. Where the name of a file does not suggest the
job it holds, say so in the row.

## alloc.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to the function to start reading from: allocate pages with a
reference; allocate pages without one; free pages; allocate and free one slab object; kmalloc
above the largest cache; allocate from any context; allocate a physically contiguous range; take
an element from a mempool; resize a vmalloc area; allocate before the page allocator is up.

# GFP masks

## alloc.gfp-composite-sleep: Composite masks and sleeping

- section: GFP masks
- relevance: 4 - every allocation carries one, and the test people write by hand is often the wrong one

A table of the composite masks to choose among (`GFP_ATOMIC`, `GFP_KERNEL`, `GFP_NOWAIT`,
`GFP_NOIO`, `GFP_NOFS`, `GFP_USER`): whether the caller may sleep, and whether the request may
enter direct reclaim, only wake the background reclaim thread, or neither. Which bits decide
whether an allocation may sleep? Start from `include/linux/gfp_types.h`.

## alloc.gfp-scope: memalloc scopes

- section: GFP masks
- relevance: 4 - the mask a function receives is not the mask the allocator uses

Which scoped interfaces narrow the GFP mask of every allocation a task makes inside the scope, and
which bits does each remove? Where do the page allocator and the slab allocator apply the scope,
and what may a function that is handed a mask therefore not assume about the mask the allocator
uses? Start from `current_gfp_context()` and `memalloc_nofs_save()`.

## alloc.reclaim-reentry: Locks shared with reclaim

- section: GFP masks
- relevance: 4 - the deadlock needs memory pressure to show

What are the requirements for a blocking allocation made while holding a lock that memory reclaim
can also take, in order to assure safe usage? How does lockdep learn about the dependency without
memory pressure? Start from `fs_reclaim_acquire()` and `might_alloc()`.

## alloc.gfp-mask-tests: Testing a mask

- section: GFP masks
- relevance: 3 - a comparison against a composite misfires inside a scope

Which helper tells code that is handed a GFP mask whether it may sleep, and which whether it may
take a spinning lock? What are the requirements for a test of a GFP mask against a composite
constant in order to assure safe usage? Name in-tree comparisons that meet them. Start from
`include/linux/gfp.h`.

## alloc.kswapd-wakeup-locks: kswapd wakeup locks

- section: GFP masks
- relevance: 3 - a mask that cannot sleep can still take locks

Which locks can `wakeup_kswapd()` take, and what may a caller that passes `__GFP_KSWAPD_RECLAIM`
therefore not hold, even with a mask that cannot sleep? Does `gfp_nested_mask()` keep or drop the
bit? Start from `wakeup_kswapd()` and `fill_pool()` in `lib/debugobjects.c`.

## alloc.gfp-propagation: Wrappers that change a mask

- section: GFP masks
- relevance: 3 - dropping the caller's bits changes context silently

What are the requirements for a helper that passes on its caller's GFP mask with bits added or
removed in order to assure safe usage? Name in-tree helpers that narrow or widen a caller's mask,
and say what each changes. Start from `kmalloc_gfp_adjust()` and `mempool_adjust_gfp()`.

## alloc.user-page-zeroing: Zeroing pages for user space

- section: GFP masks
- relevance: 3 - wrong only on architectures with aliasing caches

How does zeroing through `__GFP_ZERO` differ from zeroing with `clear_user_highpage()` or
`folio_zero_user()`? What are the requirements for zeroing a page that will be mapped into user
space in order to assure safe usage, and what does `user_alloc_needs_zeroing()` tell its caller?
Start from `user_alloc_needs_zeroing()`.

## alloc.pool-placement-usage: Serving from a private pool

- section: GFP masks
- relevance: 2 - only code that intercepts allocations is exposed

What are the requirements for code that serves an allocation from memory it set aside earlier in
order to assure safe usage? Which GFP bits and cache flags does `__kfence_alloc()` test before it
serves a request, and which GFP bits does `__alloc_contig_verify_gfp_mask()` reject? Start from
`__kfence_alloc()` and `__alloc_contig_verify_gfp_mask()`.

## alloc.nowait-error-code: No-wait failure error code

- section: GFP masks
- relevance: 2 - callers treat the two error codes differently

Which error code does `__filemap_get_folio_mpol()` return when a request with `FGP_NOWAIT` fails
to allocate, and what do its callers do with that code? Start from the `FGP_NOWAIT` handling in
`__filemap_get_folio_mpol()`.

# Page allocator layers and references

## alloc.page-alloc-layers: Layers of the page allocator

- section: Page allocator layers and references
- relevance: 4 - the layer decides the reference count and the policy applied

What does this tree call the layers between `alloc_pages()` or `folio_alloc()` and a page coming
off a free list, and at which layer is each of these applied: the memory policy, the reference
count, the task's scope and cpuset, the per-CPU list? What does a caller that enters at a lower
layer therefore skip? Start from `alloc_pages_mpol()` and `__alloc_frozen_pages_noprof()`.

## alloc.alloc-flags: Internal allocation flags

- section: Page allocator layers and references
- relevance: 4 - the flag names a reader remembers may have changed

From what in the request is each of the page allocator's internal allocation flags derived, and
which functions compute them? Which of the flags may a caller outside the page allocator pass in,
and through which entry point? Start from `ALLOC_NOLOCK` in `mm/page_alloc.h`.

## alloc.frozen-pages: Frozen page allocators

- section: Page allocator layers and references
- relevance: 4 - the two families look alike and differ by one in the count

What does this tree call the page allocator functions that hand back a page whose reference
count is zero and where are they declared, which free function pairs with them, and what do the
bulk and the contiguous-range allocators return (with a reference or without, compound or not)?
Start from `mm/page_alloc.h`.

## alloc.frozen-usage: Using frozen pages

- section: Page allocator layers and references
- relevance: 4 - nothing in a diff shows which kind a pointer is

What are the requirements for a page obtained with a zero reference count, such as one from
`__alloc_frozen_pages_noprof()`, in order to assure safe usage? Name in-tree code that converts
one kind to the other. Start from `set_page_refcounted()`.

## alloc.free-path: Freeing pages

- section: Page allocator layers and references
- relevance: 4 - the entry points differ in what they do to the reference count

What does this tree call the layers between `__free_pages()` or `folio_put()` and the buddy
lists, which entry points drop a reference and which expect the count to be zero already, and
when does a freed page go to a per-CPU list and when straight to the buddy lists? Start from
`free_frozen_pages()` and `free_pages_prepare()`.

## alloc.direct-map-restore: Pages off the direct map

- section: Page allocator layers and references
- relevance: 2 - a few users, but the ordering error is a crash in an unrelated task

When a page has been removed from the kernel's direct map, in what order must restoring the
mapping and freeing the page happen, and why? Name in-tree code that shows it. Start from
`set_direct_map_invalid_noflush()` and `mm/secretmem.c`.

## alloc.static-key-hotplug: Static keys near the allocator

- section: Page allocator layers and references
- relevance: 2 - deadlocks only during CPU bring-up

Which static key operations take the CPU hotplug lock, and which locks do
`static_branch_enable_cpuslocked()` and `static_key_enable_cpuslocked()` still take? What are the
requirements for calling a static key operation from a path that an allocation can reach in order
to assure safe usage? Start from `static_branch_enable()`.

# Free lists and pageblocks

## alloc.pcp-lists: Per-CPU page lists

- section: Free lists and pageblocks
- relevance: 4 - most allocations and frees never reach the buddy lists

Which orders and migrate types do the per-CPU page lists hold, and what do the `high` and `batch`
limits of a list decide? When do pages move between the per-CPU lists and the buddy lists? Start
from `struct per_cpu_pages`, `rmqueue_pcplist()` and `free_frozen_page_commit()`.

## alloc.pcp-lock-wrappers: Locking a per-CPU list

- section: Free lists and pageblocks
- relevance: 3 - a bare lock call is wrong on uniprocessor and on RT

Which wrappers take the lock of a per-CPU page list, what do they do besides locking, and what
happens on a uniprocessor build? What are the requirements for taking that lock in order to assure
safe usage? Start from `pcp_spin_trylock()` and `pcp_spin_lock_nopin()`.

## alloc.pageblock-flags: Pageblock flags

- section: Free lists and pageblocks
- relevance: 3 - a page larger than a pageblock covers several

How is isolation of a pageblock represented in `enum pageblock_bits`? Which function sets the
migrate type of one pageblock, and which must be used for a page that spans several? What are the
requirements for the free list a page sits on, relative to the migrate type of its pageblock, in
order to assure safe usage? Start from `enum pageblock_bits` and `set_pageblock_migratetype()`.

## alloc.migratetype-fallback: Migrate type fallback

- section: Free lists and pageblocks
- relevance: 3 - the fallback code has been rewritten and renamed

What does this tree call the functions that find a fallback when the free list for the requested
migrate type is empty? What is the difference between claiming a whole pageblock and stealing one
page, and what decides which happens? What must a change there keep true of the pageblock's type
and the pages left on its lists? Start from `__rmqueue()`, `find_suitable_fallback()` and
`try_to_claim_block()`.

## alloc.movable-contract: Movable allocations

- section: Free lists and pageblocks
- relevance: 3 - an unmovable page in a movable block defeats compaction and hot-unplug

What does passing `__GFP_MOVABLE` promise about the pages, and how does the bit together with
`__GFP_RECLAIMABLE` choose a free list, both bits set included? What are the requirements for a
driver that registers `struct movable_operations` in order to assure safe usage? Start from
`gfp_migratetype()`.

# The slow path and failure

## alloc.slowpath-order: Slow path steps

- section: The slow path and failure
- relevance: 4 - a change has to go in the right place in the sequence

In what order does the slow path try waking background reclaim, the reserves, compaction, direct
reclaim and the OOM killer after the fast path fails, what decides whether compaction or reclaim
comes first, and which watermark do the fast path and the slow path each test against? Start
from `__alloc_pages_slowpath()`.

## alloc.can-fail: Requests that can fail

- section: The slow path and failure
- relevance: 4 - decides whether a NULL check is needed, dead code or missing

Which page allocation requests can return NULL, and which does the slow path retry without bound?
What does each of `__GFP_NORETRY`, `__GFP_RETRY_MAYFAIL` and `__GFP_NOFAIL` need from the rest of
the mask to have any effect, and what does the allocator do with a `__GFP_NOFAIL` request it
cannot honour? Start from `__alloc_pages_may_oom()` and the "Reclaim modifiers" comment in
`include/linux/gfp_types.h`.

## alloc.oom-killer-skipped: OOM killer exceptions

- section: The slow path and failure
- relevance: 4 - decides whether a request fails or waits for memory to be freed

For which requests does `__alloc_pages_may_oom()` return without invoking the OOM killer, and what
does the slow path do with such a request next?

## alloc.slowpath-jumps: Slow path backward jumps

- section: The slow path and failure
- relevance: 3 - a retry that changes nothing loops forever, and the cached starting zone can go stale

Which backward jumps in `__alloc_pages_slowpath()` can be taken a bounded number of times and what
bounds each, and which have no bound? What does a jump to the `retry` label reuse that a jump to
the `restart` label recomputes, and which outside changes do `check_retry_cpuset()` and
`check_retry_zonelist()` detect? Start from `__alloc_pages_slowpath()`, `check_retry_cpuset()` and
`check_retry_zonelist()`.

## alloc.slowpath-retry-checks: Checks before a repeated retry

- section: The slow path and failure
- relevance: 3 - a retry that does not pass the checks keeps a starting zone that has gone stale

Where in `__alloc_pages_slowpath()` are `check_retry_cpuset()` and `check_retry_zonelist()`
called, and which backward jumps pass through these calls and which do not?

# Watermarks

## alloc.watermarks: Watermark levels

- section: Watermarks
- relevance: 4 - reclaim and allocation both steer by them

Which accessor returns one of a zone's watermark levels, and how does what it returns differ from
the stored value? What triggers watermark boosting, and what clears it? Start from
`__setup_per_zone_wmarks()` and `boost_watermark()`.

## alloc.watermark-check: The watermark test

- section: Watermarks
- relevance: 4 - the formula has terms people forget

In `__zone_watermark_ok()`, what is subtracted from the free count as unusable, how does each
reserve-access flag lower the mark, and what more is required for an order above zero? Start from
`__zone_watermark_ok()`.

## alloc.lowmem-reserve: The low-memory reserve

- section: Watermarks
- relevance: 4 - the array's indices are read backwards more often than not

What does `zone->lowmem_reserve[j]` protect and from whom, what do the zone and the index `j` each
stand for, and how does the value enter the watermark test? Start from
`setup_per_zone_lowmem_reserve()`.

## alloc.vmstat-drift: Per-CPU counter drift

- section: Watermarks
- relevance: 3 - on many CPUs the error exceeds the gap between watermarks

Which read of a zone's free page count leaves out the per-CPU deltas and which includes them,
when must code pay for the exact one and how does in-tree code decide that, and where is the
cheap one used on purpose? Start from `zone_page_state_snapshot()`, `percpu_drift_mark` and
`pgdat_balanced()`.

## alloc.watermark-init-order: Watermarks early in boot

- section: Watermarks
- relevance: 3 - a zero watermark passes every test

When during boot are the zone watermarks first set, what do watermark tests return before then,
and what must code that can run earlier do about it? Start from `init_per_zone_wmark_min()`.

# Any-context allocation

## alloc.nolock-page-alloc: Any-context page allocation

- section: Any-context allocation
- relevance: 4 - a newer interface with a narrow contract

Which GFP bits and orders does `alloc_pages_nolock()` accept from its caller, and which bits does
it add for itself? When does it give up without trying? Start from `alloc_pages_nolock()` and
`gfp_nolock` in `mm/page_alloc.c`.

## alloc.nolock-usage: Locks on the trylock-only path

- section: Any-context allocation
- relevance: 4 - one unconditional lock breaks every caller

What does the page allocator require of a helper reachable from `get_page_from_freelist()` when
the request is trylock-only, and how does the helper find out? Do any helpers there take a lock
with no such test, and if so, what allows it? For which conditions may such a helper bail out?
Start from `ALLOC_NOLOCK` and `alloc_nolock_allowed()`.

## alloc.nolock-free: Any-context freeing

- section: Any-context allocation
- relevance: 3 - the page can sit on a side list until someone else frees

Which functions free pages from any context, what happens to the page when the per-CPU or zone
lock cannot be taken, and who finishes the job later and when? Start from `free_pages_nolock()`
and `FPI_NOLOCK`.

## alloc.kmalloc-nolock: Any-context kmalloc

- section: Any-context allocation
- relevance: 4 - a newer interface with a narrow contract

Which GFP bits and sizes does `kmalloc_nolock()` accept, and from which contexts may it be called?
When does it return NULL without trying, and how does the slab slow path tell such a request from
an ordinary one? Start from `SLAB_ALLOC_NOLOCK` and `alloc_flags_allow_spinning()` in `mm/slab.h`.

## alloc.nolock-free-pairing: Pairing any-context allocation and free

- section: Any-context allocation
- relevance: 4 - the wrong pairing leaves tracking tools out of step

Which free functions may follow `kmalloc_nolock()`, and what are the requirements for an object
passed to `kfree_nolock()` in order to assure safe usage? Name in-tree code that frees an object
from `kmalloc_nolock()` with a function other than `kfree_nolock()`.

## alloc.kmemleak-registration: kmemleak registration

- section: Any-context allocation
- relevance: 3 - the test changed from the mask to a separate flag word

Which slab allocations does the allocator not register with kmemleak, and what does it test to
decide? What do `kmemleak_not_leak()`, `kmemleak_ignore()`, `kmemleak_free()` and
`kmemleak_no_scan()` do with an object that was never registered, and which locks do they take on
the way?

## alloc.slub-nolock-retry: Slab retry without spinning

- section: Any-context allocation
- relevance: 3 - a trylock can fail every time

What does `___slab_alloc()` require of a jump back to retry when the request may not spin? Under
which conditions does a trylock on that path fail, and can such a condition last over every retry?
Start from `___slab_alloc()`.

# The slab allocator

## alloc.slab-architecture: Layers of the slab allocator

- section: The slab allocator
- relevance: 5 - the per-CPU layer a reader remembers may not be the one in this tree

What does this tree call the layers between a slab allocation and the page allocator: what sits
per CPU, what is shared per node and where does it hang off the cache, and which caches have no
per-CPU layer at all? Start from `struct slub_percpu_sheaves`, `struct node_barn` and `struct
kmem_cache_node` in `mm/slub.c`.

## alloc.slab-alloc-path: Slab allocation path

- section: The slab allocator
- relevance: 4 - a change has to know which layer it is in

What does this tree call the functions on the slab allocation path from the per-CPU fast path to a
new slab, and at which of them are a NUMA node request and a request served from emergency
reserves honoured? Start from `slab_alloc_node()` and `___slab_alloc()`.

## alloc.slab-free-path: Slab free path

- section: The slab allocator
- relevance: 4 - the fast path is no longer a compare-and-exchange on a per-CPU slab

What does this tree call the functions on the slab free path from `kfree()` or
`kmem_cache_free()` down, how does a free find its cache and its slab, and what happens to an
object from a remote node or when the per-CPU layer is full? Start from `slab_free()`,
`free_to_pcs()` and `__slab_free()`.

## alloc.slab-overlay: The slab descriptor

- section: The slab allocator
- relevance: 4 - it is laid over the page structure, and fields under a config option are invisible in most builds

How is a slab page told from any other page in this tree? What must a field added to `struct slab`
not overlap in `struct page`, and how does the build check it? Which state of a new slab does
`allocate_slab()` set itself, and why? Start from `mm/slab.h`, `enum slab_flags` and
`allocate_slab()`.

## alloc.slab-locks: Slab locks

- section: The slab allocator
- relevance: 4 - the order is written down and lockdep does not see all of it

What is the slab allocator's lock order and what kind of lock is each, which of them may only be
tried and from which contexts, and what differs on a preemptible-RT kernel? Start from the
comment at the top of `mm/slub.c`.

## alloc.slab-hooks: Allocation and free hooks

- section: The slab allocator
- relevance: 3 - a specialised path that skips one leaves a tool out of step

What must a specialised slab allocation or free path call so that KASAN, KMSAN, kmemleak,
zeroing, allocation tags and the cgroup charge stay in step, in which functions are those hooks
gathered, and when a late hook fails what must the abort path undo? Start from
`slab_post_alloc_hook()`, `slab_free_hook()` and `memcg_alloc_abort_single()`.

## alloc.slab-obj-exts: Per-object extensions

- section: The slab allocator
- relevance: 3 - the field shares storage with the page's cgroup word

Where can a slab's vector of `struct slabobj_ext` live, and what do the low bits of the field that
points to it mean? What must be true of that field when the slab's pages go back to the page
allocator? Start from `struct slabobj_ext`, `alloc_slab_obj_exts()` and `free_slab_obj_exts()`.

## alloc.slab-obj-exts-recursion: Allocation of the extension vector

- section: The slab allocator
- relevance: 3 - the vector is itself a slab allocation that could ask for a vector

How does `alloc_slab_obj_exts()` allocate the vector, and what keeps that allocation from needing
a vector of its own?

## alloc.slab-freepointer: Free pointers

- section: The slab allocator
- relevance: 3 - a raw store works until hardening or tagging is enabled

Where does a free object keep the pointer to the next free object, and how is it encoded under
`CONFIG_SLAB_FREELIST_HARDENED`? What are the requirements for code in `mm/slub.c` that reads or
writes the free pointer of an object, or touches a freed object that may carry a KASAN tag, in
order to assure safe usage? Start from `get_freepointer()` and `set_freepointer()`.

## alloc.typesafe-by-rcu: Type-safe-by-RCU caches

- section: The slab allocator
- relevance: 4 - the flag delays freeing the slab, not the object

What does `SLAB_TYPESAFE_BY_RCU` guarantee and what does it not? What are the requirements for a
lockless reader that finds an object in such a cache in order to assure safe usage, and what may a
constructor be relied on for? Start from the comment at the flag's definition in
`include/linux/slab.h`.

# kmalloc memory

## alloc.kmalloc-caches: kmalloc caches

- section: kmalloc memory
- relevance: 4 - which cache serves a request decides its neighbours

Which GFP bits does `kmalloc_type()` use to select a cache type, and what partitions the normal
caches and on what key? How is a request above `KMALLOC_MAX_CACHE_SIZE` served, and how does
`kfree()` recognise it later? Start from `kmalloc_type()`, `kmalloc_caches` and
`KMALLOC_MAX_CACHE_SIZE`.

## alloc.kmalloc-alignment: kmalloc alignment

- section: kmalloc memory
- relevance: 4 - reviewers keep reporting a guarantee as an accident

What alignment does `kmalloc()` guarantee, for a power-of-two size and for other sizes, where is
that documented and how is it enforced when the caches are created, and do the debugging options
(red zones, user tracking, KASAN) weaken it? Start from `create_boot_cache()` and
`calculate_sizes()`.

## alloc.kmalloc-page-ownership: Pages behind kmalloc memory

- section: kmalloc memory
- relevance: 4 - the buffer shares its page with strangers

What are the requirements for code that uses the `struct page` behind a kmalloc buffer in order to
assure safe usage? What is the reference count of a slab page? Start from `sendpage_ok()` and
`sg_set_buf()`.

## alloc.kmalloc-zone-bits: Zone bits passed to kmalloc

- section: kmalloc memory
- relevance: 3 - one of the zone bits selects a cache and another is silently dropped

What does kmalloc do with each of the zone bits in the mask: which select a cache, which are
stripped and with what warning, and when is the warning not seen? Start from
`KMALLOC_NOT_NORMAL_BITS`, `GFP_SLAB_BUG_MASK` and `kmalloc_fix_flags()`.

## alloc.krealloc-zeroing: Zeroing in krealloc

- section: kmalloc memory
- relevance: 3 - reviewers ask for a test that does not belong here

When `krealloc()` can resize in place, which bytes does it zero on a grow and on a shrink, which
of the init-on-alloc and init-on-free settings does it consult, and how does it know the size
the caller last asked for? Start from `__do_krealloc()`.

## alloc.kvmalloc: kvmalloc fallback

- section: kmalloc memory
- relevance: 3 - the fallback has its own rules about masks and contexts

How does `__kvmalloc_node_noprof()` decide between kmalloc and vmalloc, and how does
`kmalloc_gfp_adjust()` change the caller's mask for the first attempt? Which masks make it skip
the fallback? Start from `__kvmalloc_node_noprof()` and `kmalloc_gfp_adjust()`.

## alloc.kvfree-contexts: Contexts for kvfree

- section: kmalloc memory
- relevance: 3 - the fallback has its own rules about masks and contexts

From which contexts may `kvfree()` and `kvfree_atomic()` each be called?

# Mempools and vmalloc

## alloc.mempool-guarantee: Mempool guarantees

- section: Mempools and vmalloc
- relevance: 4 - decides whether a NULL check is dead code or a missing one is a crash

With which GFP masks can `mempool_alloc()` return NULL and with which does it wait until it
succeeds, and what does that mean for error handling at the call site? Start from
`mempool_alloc_noprof()` in `mm/mempool.c`.

## alloc.vmalloc-gfp: vmalloc and GFP masks

- section: Mempools and vmalloc
- relevance: 3 - the page-table allocations underneath do not take the caller's mask

How does vmalloc honour a no-FS or no-IO request when it allocates the page tables underneath?
Which bits does it reject or fix up, and at which entry points? From which contexts may `vfree()`
be called? Start from `__vmalloc_node_range_noprof()` and `vmalloc_fix_flags()`.

## alloc.vrealloc-zeroing: Zeroing in vrealloc

- section: Mempools and vmalloc
- relevance: 3 - the rule differs from krealloc's

When `vrealloc()` resizes in place, which bytes does it zero on a shrink and on a grow, which of
the init-on-alloc and init-on-free settings does it consult and why, and how does it know the size
the caller last asked for? Start from `vrealloc_node_align_noprof()`.

## alloc.vrealloc-kasan: KASAN in vrealloc

- section: Mempools and vmalloc
- relevance: 2 - one function

What alignment do the KASAN poison and unpoison functions require of the addresses passed to them?
What does `kasan_vrealloc()` do for an in-place resize whose old or new size does not meet that
alignment? Start from `kasan_vrealloc()`.

# Boot-time allocation

## alloc.memblock-conventions: Memblock range parameters

- section: Boot-time allocation
- relevance: 3 - both conventions use the same type, so the compiler cannot help

Does memblock pass a range as a base and a size or as a start and an end, and if it uses both,
which convention do `memblock_add()` and `memmap_init_reserved_range()` each use? What in a
prototype tells a caller which convention applies? Start from `memblock_add()` and
`memmap_init_reserved_range()` in `mm/memblock.c`.

## alloc.memblock-lifetime: Memblock lifetime

- section: Boot-time allocation
- relevance: 3 - calling it too late or keeping a pointer too long

What do the memblock allocation functions do on failure? What happens to memblock's own data and
code after boot, and under which configuration do they survive? How must memory obtained from
memblock be freed once the page allocator is up? Start from `memblock_alloc()`,
`memblock_free_all()` and `__init_memblock`.

## alloc.memblock-window: Memblock availability window

- section: Boot-time allocation
- relevance: 3 - calling it too late or keeping a pointer too long

Until which point in boot may `memblock_alloc()` be called, and what does a call made after
`memblock_free_all()` do?

## alloc.early-boot-globals: mm globals early in boot

- section: Boot-time allocation
- relevance: 2 - a few call sites

Until which point in boot are `high_memory`, the zone boundaries and the node states in
`node_states` not yet valid, which function sets each, and what should code that runs earlier use
instead? Start from `free_area_init()` and `memblock_end_of_DRAM()`.

# Cgroup charging and statistics

## alloc.memcg-opt-in: Opting in to cgroup charging

- section: Cgroup charging and statistics
- relevance: 3 - an uncharged allocation lets a container exceed its limit

Which cache flags and GFP bits opt a slab allocation in to memory cgroup charging, and is an
object charged when only one of them is set? What does a failure to charge do to the allocation?
Start from `memcg_slab_post_alloc_hook()` and `__memcg_kmem_charge_page()`.

## alloc.active-memcg: Choosing the cgroup

- section: Cgroup charging and statistics
- relevance: 3 - the default is the current task, which is wrong for work done on behalf of others

How does the charge path choose which cgroup pays for a kernel allocation, and in which contexts
is the override ignored or the charge skipped? What are the requirements for `set_active_memcg()`
in code that allocates on behalf of another task in order to assure safe usage? Start from
`set_active_memcg()` and `current_obj_cgroup()`.

## alloc.vmstat-node-vs-memcg: Node and cgroup statistics

- section: Cgroup charging and statistics
- relevance: 3 - the helpers differ in which counters they touch

A table to choose from, for `mod_node_page_state()`, `mod_lruvec_state()`,
`lruvec_stat_mod_folio()`, `mod_lruvec_page_state()` and `mod_lruvec_kmem_state()`: which update
only the node counter, which also the memory cgroup's, and what decides it when the folio or
object has no cgroup.

## alloc.deferred-charge-stats: Statistics across a late charge

- section: Cgroup charging and statistics
- relevance: 2 - one or two paths change a folio's cgroup after allocation

What does `kmem_cache_charge()` do to the statistics of an object that was allocated uncharged and
already counted, and from which counters does the free path later subtract? Start from
`kmem_cache_charge()` in `mm/slub.c`.

# NUMA nodes and memory policy

## alloc.mempolicy-vs-node: Policy-aware and node-specific allocation

- section: NUMA nodes and memory policy
- relevance: 3 - swapping one for the other silently moves pages to other nodes

Which page and folio allocation entry points apply the task's memory policy, which apply a VMA's,
and which bypass both? What are the requirements for replacing one of these entry points with
another in order to assure safe usage, and how does in-tree code choose when it is given a node id
that may be `NUMA_NO_NODE`? Start from `alloc_pages_node()`, `vma_alloc_folio()` and
`___kmalloc_large_node()`.

## alloc.node-id-validation: Node ids from outside

- section: NUMA nodes and memory policy
- relevance: 3 - the lookup has no bounds check

What must be checked about a node id that comes from user space or firmware before it is passed
to `NODE_DATA()` or to an allocation function, and what does the lookup give for a node that is
possible but offline? Name in-tree code that does the check. Start from `do_pages_move()`.

## alloc.node-iteration: Iterating over nodes

- section: NUMA nodes and memory policy
- relevance: 3 - online is not the same as having memory

Which node iterators include nodes without memory and which should an allocation loop use, what
is the upper bound for a raw loop over node ids, and what may code that runs before the node
states are populated at boot rely on? Start from `for_each_node_state()` and `nr_node_ids`.

## alloc.memoryless-nodes: Memoryless nodes

- section: NUMA nodes and memory policy
- relevance: 3 - only fails on hardware few people test on

What do `numa_node_id()` and `numa_mem_id()` each return on a CPU whose node has no memory, and
what can a lookup of the slab allocator's per-node structure return there? Start from
`get_node()` and `get_from_partial_node()` in `mm/slub.c`.

# Model gaps

## alloc.model-gaps: Other mistakes models make

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
