# What the mm-alloc measurement found

Three models were asked the 90 questions in `mm-alloc-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). This is why the build set in
`../mm-alloc.md` holds the questions it does. The readers are labelled A, B and
C. Reader C is the most current (it assumed 6.14 to 7.0), reader A sits in the
middle (6.12 to 6.19) and reader B is a few releases older (6.10 to 6.12).
Which models they were does not matter here.

## How it differs from the other guides

The hand-written `mm-alloc.md` is one of the guides that was checked line by
line against this tree, so its hazards are real and most of them are kept as
questions. What it lacks is a map: it never says which file holds what, what
the layers of the page and slab allocators are called, or how an object travels
through the slab allocator. That is exactly where all three readers were out of
date, because both allocators have been reorganised recently. So the build set
adds the map and pays for it by dropping what readers A and C already answer.

## What all three readers got wrong: names and layouts that moved

- **`mm/page_alloc.h` exists.** It holds the `ALLOC_` flags,
  `struct alloc_context`, the frozen-page API and the buddy helpers. All three
  put them in `mm/internal.h`, and two said outright that there is no such
  file. Allocation profiling is `mm/alloc_tag.c`; all three said lib/alloc_tag.c.
- **The allocation-flag helpers were renamed.** There is no
  gfp_to_alloc_flags(); the slow path calls `alloc_flags_slowpath()`, beside
  `alloc_flags_nonblocking()`, `alloc_flags_cma()` and
  `alloc_flags_nofragment()`. Reader B still had ALLOC_HARDER and ALLOC_HIGH;
  the flags are `ALLOC_NON_BLOCK` and `ALLOC_MIN_RESERVE`.
- **The trylock-only path.** The flag is `ALLOC_NOLOCK` and the free flag
  `FPI_NOLOCK`. Readers A and C said ALLOC_TRYLOCK and FPI_TRYLOCK, reader B
  offered try_alloc_pages(). None knew what `gfp_nolock` holds or what
  `alloc_nolock_allowed()` tests. All three said no outside caller can pass an
  `ALLOC_` flag; `__alloc_frozen_pages_noprof()` takes a fifth argument and
  accepts `ALLOC_NOLOCK | ALLOC_NO_CODETAG`. A page that cannot be freed
  without spinning waits on the per-zone list `zone->trylock_free_pages` until
  the next ordinary free drains it; reader B described a per-CPU list and a
  work item.
- **Contiguous allocation.** The refcounted `alloc_contig_range()` and
  `alloc_contig_pages()` warn and fail on `__GFP_COMP`; readers A and C said
  they return a compound page. Only the frozen forms
  (`alloc_contig_frozen_range()`, `alloc_contig_frozen_pages()`) do, and no
  reader was sure those exist. Isolation is a separate `PB_migrate_isolate`
  bit, not a migrate type written over the old one as readers A and B said.
- **Per-CPU page list locking.** On a uniprocessor build `pcp_spin_trylock()`
  is defined as NULL, so every request goes to the buddy lists. Readers A and
  C said the uniprocessor trylock always succeeds and named two helpers that
  are gone; reader B called the lock a no-op there and offered a
  pcp_spin_lock() that never existed.
- **The slab allocator's layers.** Readers A and C know sheaves and barns;
  reader B partly. All three put the barn inside `struct kmem_cache_node`; it
  is `s->per_node[node].barn`. Not every cache has sheaves
  (`calculate_sheaf_capacity()` returns 0 for debug caches, the tiny
  configuration and two cache flags). Names one reader or another still used
  that are gone: cache_from_obj(), get_partial(), __slab_alloc_node(),
  do_slab_free(), put_cpu_partial(), kmalloc_large(). `kfree()` finds the slab
  with `page_slab()`.
- **Per-object extensions.** `struct slabobj_ext` is a one-word union with a
  stride, not a struct of two pointers. There is no __GFP_NO_OBJ_EXT; recursion
  is prevented by the `SLAB_ALLOC_NO_OBJ_EXT` allocation flag and the
  `KMALLOC_NO_OBJ_EXT` caches. The vector can live in leftover slab space or
  inside the objects.
- **kmalloc cache partitioning.** The option is
  `CONFIG_KMALLOC_PARTITION_CACHES`, fifteen copies beside the normal cache,
  keyed by code location and a seed or by a compiler-supplied type token. All
  three described the older random-cache option keyed by return address.
- **Any-context kmalloc.** The slab code does not look at the GFP mask to tell
  such a request; it tests `SLAB_ALLOC_NOLOCK` in the allocation context with
  `alloc_flags_allow_spinning()`. Readers A and C said they did not recognise
  either name. The kmemleak skip tests the same flag.
- **Memblock after boot.** `memblock_free()` hands pages to the page allocator
  once slab is up; memblock_free_late() is gone; `__init_memblock` is
  `__meminit`, so it survives with memory hotplug.
- **vmalloc and scopes.** Page-table allocations ignore the caller's mask, so
  `memalloc_apply_gfp_scope()` wraps them in a scope; `vmalloc_fix_flags()` is
  called from two entry points only.
- **Memory policy.** `alloc_pages_mpol()` is static; the task policy is chosen
  in `alloc_frozen_pages_noprof()` in `mm/mempolicy.c`, which uses the default
  policy in interrupt context and with `__GFP_THISNODE`. There is no
  __alloc_pages_node().

## What all three got wrong: facts that would change a verdict

- **`__GFP_NOFAIL` can return NULL.** Without direct reclaim the slow path
  warns once and fails. Readers A and C also described a warning for order
  above one that exists only in a comment.
- **Reserve access.** `ALLOC_NON_BLOCK` lowers the mark only together with
  `ALLOC_MIN_RESERVE`, so a plain no-wait request gets nothing;
  `ALLOC_HIGHATOMIC` needs `__GFP_HIGH`; an OOM victim's mark is halved once.
- **Where the task's scope is applied.** Only the page allocator calls
  `current_gfp_context()`, and it does so before the fast path. Reader A said
  the fast path runs unscoped; readers B and C thought the slab allocator
  applies the scope as well. It never does.
- **Debug-object pool refill** adds the wake-kswapd bit only when preemptible
  or before the scheduler runs. Two readers said it never has the bit, the
  third gave a different condition.
- **Moving a charge to a cgroup late**: the order of the counter updates in
  `memcg_slab_post_charge()` and the helpers it uses.
- **`NODE_DATA()` is allocated for every possible node**, so it is not NULL for
  an offline one; `get_node()` reads `s->per_node[node].node`, and the slab
  node mask follows `N_MEMORY`.

## What only some readers got wrong

- Readers B and C: setting both mobility bits is harmless or lets one win. It
  selects the high-atomic free list, with a debug-only warning.
- Readers A and C: static-key inc and dec take the CPU hotplug lock only when
  the count crosses zero. They take it on every call, and the cpuslocked forms
  can still sleep.
- Readers A and C: kmemleak's not-leak and ignore calls warn on an object that
  was never registered. They are silent; only the no-scan call warns.
- Reader A: a slab free path built on a per-CPU slab; `kmalloc_gfp_adjust()`
  adds no-retry; an in-place krealloc grow always zeroes; vrealloc zeroes on
  grow; zone_watermark_ok_safe() still exists.
- Reader B, as well as the above: a slab page has a reference count of one and
  carries a slab page flag; only order zero uses the per-CPU lists; compaction
  always precedes reclaim; the typed allocation helpers do not exist;
  `kmalloc_gfp_adjust()` and `mempool_adjust_gfp()` are not real; `kfree_nolock()`
  may free ordinary kmalloc memory; mempool strips the zeroing bit; a no-IO
  allocation may compact.
- Reader C: `kmalloc_flex()` fails when the counter cannot hold the count. Only
  its kernel-doc says so; the code sets the counter after allocating and never
  checks it.

## What readers A and C already knew

The composite masks and which bit allows sleeping, the contexts a non-blocking
allocation is allowed in, the watermark formula and the low-memory reserve, the
buddy free lists, high-order pages without compound metadata, the order the
allocators come up at boot, type-safe-by-RCU caches, iterating over nodes, the
mempool guarantee, the direct-map ordering. Reader B was wrong or vague on
nearly all of these, mostly in names.

## Where the hand-written guide is stale

It was checked against this tree, so very little. It carries two commit SHAs
and several "since vX.Y" remarks, which a built guide cannot. Its list of
helpers that lock without testing for the trylock-only path leaves out
`node_reclaim()` and `rmqueue_pcplist()`. Its advice to use the cpuslocked
static-key forms does not say they still take a mutex. It does not mention
`kfree_rcu_nolock()`. It names no file for the `ALLOC_` flags and says nothing
of the fifth argument of `__alloc_frozen_pages_noprof()`. Everything else that
is new in the built guide is addition, not correction.

## Left out of the build set

Because readers A and C answer them: `alloc.docs`, `alloc.gfp-sleep-bit`,
`alloc.gfp-zone-bits`, `alloc.atomic-contexts`, `alloc.watermark-check`,
`alloc.watermarks`, `alloc.buddy-lists`, `alloc.high-order-noncompound`,
`alloc.boot-stages`, `alloc.typesafe-by-rcu`, `alloc.change-page-alloc`.

For space, although some reader is wrong: `alloc.gfp-watermark-modifiers` (the
names are in `alloc.alloc-flags`), `alloc.noprof-wrappers`,
`alloc.fresh-page-state`, `alloc.contig-alloc`, `alloc.pcp-lists`,
`alloc.free-page-checks`, `alloc.slab-alloc-path`, `alloc.typed-helpers`,
`alloc.cache-create`, `alloc.cache-destroy`, `alloc.kfree-rcu`,
`alloc.mempool-internals`, `alloc.change-slab`. If the built guide comes in
under its size these are the candidates to add back, `alloc.contig-alloc` and
`alloc.typed-helpers` first.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too, and an answer sent back
for length counts as rewritten, which overstates reader B's gap; the
corrections are what count.

```
reader A: 245 corrections, 36% rewritten on average
reader B: 219 corrections, 76% rewritten on average
reader C: 213 corrections, 23% rewritten on average

question                         reader A     reader B     reader C
alloc.core-files                  4% ( 7)      2% ( 4)      7% ( 4)
alloc.entry-points                2% ( 2)     17% ( 3)      3% ( 2)
alloc.docs                       20% ( 0)     36% ( 0)     23% ( 0)
alloc.gfp-composites              5% ( 3)     10% ( 1)      0% ( 2)
alloc.gfp-sleep-bit               0% ( 0)     63% ( 1)     31% ( 1)
alloc.gfp-retry-modifiers        23% ( 2)     81% ( 3)     41% ( 4)
alloc.gfp-watermark-modifiers    41% ( 4)     88% ( 3)     18% ( 4)
alloc.gfp-zone-bits              17% ( 1)     83% ( 3)      7% ( 1)
alloc.pool-placement-usage       58% ( 3)     78% ( 1)      9% ( 2)
alloc.movable-contract           20% ( 1)     75% ( 1)     18% ( 3)
alloc.gfp-scope                  51% ( 2)     54% ( 3)      4% ( 4)
alloc.gfp-mask-tests             34% ( 1)     74% ( 2)     11% ( 1)
alloc.kswapd-wakeup-locks        53% ( 2)     74% ( 3)     21% ( 3)
alloc.atomic-contexts             9% ( 1)     71% ( 2)      0% ( 0)
alloc.reclaim-reentry            25% ( 1)     83% ( 1)      3% ( 1)
alloc.gfp-propagation            51% ( 1)     94% ( 6)     25% ( 1)
alloc.nowait-error-code          65% ( 1)     86% ( 1)     33% ( 1)
alloc.memcg-opt-in               33% ( 2)     76% ( 1)     37% ( 2)
alloc.active-memcg               61% ( 3)     87% ( 5)     28% ( 2)
alloc.vmstat-node-vs-memcg        9% ( 1)     47% ( 3)      2% ( 1)
alloc.deferred-charge-stats      43% ( 2)     93% ( 1)     45% ( 2)
alloc.page-alloc-layers          32% ( 4)     79% ( 6)     23% ( 4)
alloc.noprof-wrappers            25% ( 2)     75% ( 2)     37% ( 1)
alloc.frozen-pages               48% ( 5)     86% ( 3)     57% ( 3)
alloc.frozen-usage               40% ( 2)     79% ( 2)     29% ( 1)
alloc.alloc-flags                26% ( 6)     91% ( 5)     42% (10)
alloc.fresh-page-state           17% ( 2)     83% ( 1)     34% ( 1)
alloc.high-order-noncompound      0% ( 0)     71% ( 1)      7% ( 1)
alloc.contig-alloc               43% ( 4)     82% ( 1)     62% ( 3)
alloc.slowpath-order             42% ( 8)     79% ( 3)      9% ( 4)
alloc.failure-rules              49% ( 4)     86% ( 4)     18% ( 1)
alloc.slowpath-retry             46% ( 2)     81% ( 1)     11% ( 3)
alloc.slowpath-restart           59% ( 4)     78% ( 1)     15% ( 1)
alloc.watermarks                 30% ( 4)     79% ( 2)     11% ( 2)
alloc.watermark-check             2% ( 2)     79% ( 3)      0% ( 0)
alloc.lowmem-reserve             14% ( 1)     71% ( 1)      0% ( 0)
alloc.vmstat-drift               25% ( 3)     71% ( 1)     16% ( 2)
alloc.watermark-init-order       11% ( 0)     66% ( 1)     25% ( 2)
alloc.pcp-lists                  34% ( 5)     89% ( 3)     49% ( 3)
alloc.pcp-lock-wrappers          56% ( 3)     81% ( 1)     61% ( 3)
alloc.buddy-lists                12% ( 1)     72% ( 1)     14% ( 1)
alloc.migratetype-fallback       14% ( 1)     83% ( 1)     44% ( 3)
alloc.pageblock-flags            52% ( 5)     82% ( 4)      2% ( 3)
alloc.free-path                  58% ( 4)     83% ( 3)     14% ( 2)
alloc.free-page-checks           49% ( 2)     75% ( 3)     15% ( 1)
alloc.nolock-page-alloc          59% ( 9)     85% ( 6)     26% ( 7)
alloc.nolock-usage               60% ( 5)     91% ( 2)     36% ( 4)
alloc.nolock-free                55% ( 4)     89% ( 1)     52% ( 1)
alloc.mempolicy-vs-node          41% ( 2)     85% ( 4)     22% ( 5)
alloc.node-id-validation         18% ( 1)     86% ( 1)     27% ( 2)
alloc.node-iteration              5% ( 1)     61% ( 1)     15% ( 3)
alloc.memoryless-nodes           31% ( 2)     61% ( 2)     38% ( 4)
alloc.user-page-zeroing          16% ( 2)     76% ( 3)      6% ( 2)
alloc.direct-map-restore         13% ( 1)     70% ( 1)      3% ( 1)
alloc.static-key-hotplug         36% ( 3)     78% ( 3)     25% ( 2)
alloc.slab-architecture          19% ( 6)     78% ( 1)     12% ( 6)
alloc.slab-struct                31% ( 3)     90% ( 1)     11% ( 1)
alloc.slab-overlay-init          59% ( 3)     75% ( 1)     17% ( 1)
alloc.slab-locks                 43% ( 4)     95% ( 1)     81% ( 1)
alloc.slab-alloc-path            68% ( 5)     82% ( 1)     24% ( 1)
alloc.slab-free-path             41% ( 7)     82% ( 6)     36% ( 7)
alloc.slab-hooks                 60% ( 2)     92% ( 2)     10% ( 2)
alloc.slab-freepointer           68% ( 3)     80% ( 2)     12% ( 1)
alloc.slab-obj-exts              63% ( 4)     85% ( 3)     56% ( 3)
alloc.kmalloc-caches             46% ( 5)     82% ( 4)     56% ( 4)
alloc.kmalloc-alignment          32% ( 2)     71% ( 3)     11% ( 1)
alloc.kmalloc-page-ownership     37% ( 2)     83% ( 5)     30% ( 4)
alloc.kmalloc-zone-bits          48% ( 1)     85% ( 4)     16% ( 1)
alloc.typed-helpers              42% ( 2)     88% ( 1)     32% ( 1)
alloc.krealloc-zeroing           77% ( 3)     79% ( 1)     18% ( 1)
alloc.kvmalloc                   61% ( 4)     77% ( 2)     28% ( 2)
alloc.kmalloc-nolock             55% ( 6)     86% ( 3)     35% ( 6)
alloc.nolock-free-pairing        55% ( 2)     86% ( 3)      8% ( 1)
alloc.slub-nolock-retry          74% ( 1)     91% ( 2)     22% ( 1)
alloc.kmemleak-registration      57% ( 3)     85% ( 3)     37% ( 2)
alloc.cache-create               43% ( 5)     81% ( 3)     27% ( 4)
alloc.typesafe-by-rcu            14% ( 2)     80% ( 1)     18% ( 2)
alloc.cache-destroy              45% ( 2)     86% ( 1)     11% ( 1)
alloc.kfree-rcu                  44% ( 2)     89% ( 4)     14% ( 1)
alloc.mempool-guarantee          31% ( 2)     68% ( 2)      0% ( 1)
alloc.mempool-internals          49% ( 4)     77% ( 3)     16% ( 3)
alloc.vmalloc-gfp                78% ( 4)     91% ( 3)     46% ( 5)
alloc.vrealloc-zeroing           49% ( 1)     81% ( 1)      3% ( 1)
alloc.vrealloc-kasan             60% ( 1)     71% ( 1)     29% ( 1)
alloc.memblock-conventions       34% ( 1)     74% ( 5)     51% ( 4)
alloc.memblock-lifetime          19% ( 2)     70% ( 3)     24% ( 4)
alloc.boot-stages                 0% ( 0)     73% ( 3)      0% ( 0)
alloc.early-boot-globals         45% ( 1)     74% ( 2)     24% ( 2)
alloc.change-page-alloc           1% ( 2)     39% ( 4)     23% ( 4)
alloc.change-slab                34% ( 4)     61% ( 8)     51% ( 6)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `alloc.slab-alloc-path`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `alloc.gfp-sleep-bit`, `alloc.watermarks`, `alloc.watermark-check`, `alloc.pcp-lists`, `alloc.typesafe-by-rcu`.

## Questions reorganised

Subjects now: GFP masks; page allocator layers and references; free lists and pageblocks; the slow
path and failure; watermarks; any-context allocation (both allocators together); the slab allocator;
kmalloc memory; mempools and vmalloc; boot-time allocation; charging a cgroup; nodes. 74 questions
became 70, none dropped. Merged: `alloc.gfp-composites` and `alloc.gfp-sleep-bit` into
`alloc.gfp-composite-sleep`; `alloc.gfp-retry-modifiers` and `alloc.failure-rules` into
`alloc.can-fail`; `alloc.slowpath-retry` and `alloc.slowpath-restart` into `alloc.slowpath-jumps`;
`alloc.slab-struct` and `alloc.slab-overlay-init` into `alloc.slab-overlay`. The "list the layers"
and "list the steps" questions now ask what this tree calls each layer and what is applied there.
