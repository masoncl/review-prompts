# MM Memory Allocation

## GFP Flags Context

Using the wrong GFP flag causes sleeping in atomic context (deadlock/BUG),
filesystem or IO recursion (deadlock), or silent allocation failures when the
caller assumes success. Verify the allocation context matches the flag.

The Reclaim column indicates which memory reclaim mechanisms are available.
"kswapd only" means the allocation wakes the background kswapd thread but never
blocks waiting for reclaim to complete. "Full" means the caller may also perform
direct reclaim synchronously, blocking until pages are freed.

| Flag | Sleeps | Reclaim | Key Flags | Use Case |
|------|--------|---------|-----------|----------|
| GFP_ATOMIC | No | kswapd only | `__GFP_HIGH \| __GFP_KSWAPD_RECLAIM` | IRQ/spinlock context, lower watermark access |
| GFP_KERNEL | Yes | Full (direct + kswapd) | `__GFP_RECLAIM \| __GFP_IO \| __GFP_FS` | Normal kernel allocation |
| GFP_NOWAIT | No | kswapd only | `__GFP_KSWAPD_RECLAIM \| __GFP_NOWARN` | Non-sleeping, likely to fail |
| GFP_NOIO | Yes | Direct + kswapd, no IO | `__GFP_RECLAIM` | Avoid block IO recursion |
| GFP_NOFS | Yes | Direct + kswapd, no FS | `__GFP_RECLAIM \| __GFP_IO` | Avoid filesystem recursion |

See "Useful GFP flag combinations" in `include/linux/gfp_types.h`.

**Notes:**
- `__GFP_RECLAIM` = `__GFP_DIRECT_RECLAIM | __GFP_KSWAPD_RECLAIM`
- GFP_NOIO can still direct-reclaim clean page cache and slab pages (no physical IO)
- Prefer `memalloc_nofs_save()`/`memalloc_noio_save()` over GFP_NOFS/GFP_NOIO
- `__GFP_KSWAPD_RECLAIM` (present in `GFP_NOWAIT` and `GFP_ATOMIC`) triggers
  `wakeup_kswapd()` in `mm/vmscan.c`, which calls `wake_up_interruptible()`
  and enters the scheduler via `try_to_wake_up()`. This means even non-sleeping
  allocations can take scheduler and timer locks. Code that allocates under
  scheduler-internal locks (e.g., hrtimer base lock, runqueue lock) or with
  preemption disabled must strip `__GFP_KSWAPD_RECLAIM` or use bare flags like
  `__GFP_NOWARN` to avoid lock recursion. See `gfp_nested_mask()` in
  `include/linux/gfp.h` for the standard approach to constraining nested
  allocation flags
- `current_gfp_context()` in `include/linux/sched/mm.h` strips `__GFP_IO`
  and/or `__GFP_FS` when the task runs under a scoped
  `memalloc_noio_save()` or `memalloc_nofs_save()` constraint. After
  narrowing, a `GFP_KERNEL` allocation becomes `GFP_NOIO` or `GFP_NOFS`,
  which still include `__GFP_DIRECT_RECLAIM` (can sleep). Testing the
  narrowed value against a composite constant like
  `(gfp & GFP_KERNEL) != GFP_KERNEL` misclassifies these as atomic,
  because the stripped `__GFP_IO`/`__GFP_FS` bits cause the comparison to
  fail. Use the single-flag helpers instead: `gfpflags_allow_blocking(gfp)`
  tests `__GFP_DIRECT_RECLAIM` (can this allocation sleep?),
  `gfpflags_allow_spinning(gfp)` tests `__GFP_RECLAIM` (can this
  allocation take locks?). See `include/linux/gfp.h`

**Placement constraints** (see "Page mobility and placement hints" in
`include/linux/gfp_types.h`):
- `GFP_ZONEMASK` (`__GFP_DMA | __GFP_HIGHMEM | __GFP_DMA32 | __GFP_MOVABLE`)
  selects the physical memory zone. Code that intercepts allocations and serves
  memory from a pre-allocated pool (e.g., KFENCE in `mm/kfence/core.c`, swiotlb
  in `kernel/dma/swiotlb.c`) must skip requests with zone constraints it cannot
  satisfy
- `__GFP_THISNODE` forces the allocation to the requested NUMA node with no
  fallback. It is NOT part of `GFP_ZONEMASK` -- checking only `GFP_ZONEMASK`
  misses this constraint. Pool-based allocators on NUMA systems must also check
  `__GFP_THISNODE` when their pool pages may not reside on the caller's
  requested node
- When stripping placement flags for validation, use the full set as in
  `__alloc_contig_verify_gfp_mask()` in `mm/page_alloc.c`:
  `GFP_ZONEMASK | __GFP_RECLAIMABLE | __GFP_WRITE | __GFP_HARDWALL |
  __GFP_THISNODE | __GFP_MOVABLE`

## __GFP_ACCOUNT

Incorrect memcg accounting lets a container allocate kernel memory without being
charged, bypassing its memory limit. Review any new `__GFP_ACCOUNT` usage or
`SLAB_ACCOUNT` cache creation.

- Slabs created with `SLAB_ACCOUNT` are charged to memcg automatically via
  `memcg_slab_post_alloc_hook()` in `mm/slub.c`, even without explicit
  `__GFP_ACCOUNT` in the allocation call

**Validation:**
1. When using `__GFP_ACCOUNT`, ensure the correct memcg is charged
   - `old = set_active_memcg(memcg); work; set_active_memcg(old)`
2. Most usage does not need `set_active_memcg()`, but:
   - Kthreads switching context between many memcgs may need it
   - Helpers operating on objects (e.g., BPF maps) with stored memcg may need it
3. Ensure new `__GFP_ACCOUNT` usage is consistent with surrounding code

## Mempool Allocation Guarantees

`mempool_alloc()` retries forever when `__GFP_DIRECT_RECLAIM` is set (GFP_KERNEL,
GFP_NOIO, GFP_NOFS) -- NULL checks are dead code. Without it (GFP_ATOMIC,
GFP_NOWAIT) it can fail -- missing NULL checks cause crashes. Match error
handling to the GFP flag (see `mempool_alloc_noprof()` in `mm/mempool.c`).

## Frozen vs Refcounted Page Allocation

`get_page_from_freelist()` returns pages with refcount 0 ("frozen").
`__alloc_pages_noprof()` wraps this and calls `set_page_refcounted()` to
return refcount 1. The `_frozen_` variants (`__alloc_frozen_pages_noprof()`,
`alloc_frozen_pages_nolock_noprof()`) return frozen pages for callers that
manage refcount themselves (compaction, bulk allocation). **REPORT as bugs**:
passing a frozen page to code expecting refcount 1 without calling
`set_page_refcounted()`, or calling `set_page_refcounted()` on a page
intended to stay frozen.

## Zone Watermarks and lowmem_reserve

`zone[i].lowmem_reserve[j]` protects zone `i` (not zone `j`) from
over-consumption by allocations targeting zone `j`. The effective watermark
is `watermark[wmark] + lowmem_reserve[j]` (see `__zone_watermark_ok()` in
`mm/page_alloc.c`). A zone's own entry is always 0. **REPORT as bugs**:
indexing `lowmem_reserve` with the zone's own index, or assuming
`lowmem_reserve[j]` protects zone `j`.

**Per-CPU vmstat counter drift:** `zone_page_state()` omits per-CPU deltas;
on many-CPU systems the error can exceed watermark gaps. When
`zone->percpu_drift_mark` is set and the cached value is below it, code must
use `zone_page_state_snapshot()`. Refactorings replacing higher-level
watermark APIs with direct `zone_page_state()` + `__zone_watermark_ok()`
silently drop this safety check. See `should_reclaim_retry()` in
`mm/page_alloc.c` and `pgdat_balanced()` in `mm/vmscan.c`.

## Zone Watermark Initialization Ordering

Zone watermarks are zero until `init_per_zone_wmark_min()` runs as a
`postcore_initcall` (`mm/page_alloc.c`). Before that, `zone_watermark_ok()`
trivially passes, masking the need for reclaim/acceptance. Code reachable
during early boot must handle `wmark == 0` as "not yet initialized" (use a
fallback threshold or unconditionally perform the required work).

## Layered vmstat Accounting (Node vs Memcg)

`lruvec_stat_mod_folio()` / `mod_lruvec_page_state()` update both node and
memcg counters only when `folio_memcg(folio)` is non-NULL; otherwise they
update only the node counter. `mod_node_page_state()` is always node-only;
`mod_lruvec_state()` is always both.

**Stat reconciliation on deferred charging:** when a folio is allocated
without a memcg and stats are recorded, only the node counter increments.
If later charged (e.g., `kmem_cache_charge()` in `mm/slub.c`), the post-
charge path must subtract from the node counter and re-add via the lruvec
interface to populate the memcg counter, or the free path will underflow it.

Review any code path that changes a folio's memcg association after allocation
for stat counters recorded before the association existed.

## Slab Page Overlay Initialization and Cleanup

`struct slab` overlays `struct page`/`struct folio` (verified by `SLAB_MATCH`
assertions in `mm/slab.h`). The page allocator does NOT zero metadata fields,
so `allocate_slab()` in `mm/slub.c` must initialize every field -- especially
conditionally-compiled ones (`CONFIG_*` ifdefs) invisible in most builds.

On free, `slab->obj_exts` shares storage with `folio->memcg_data`. Leftover
sentinel values (e.g., `OBJEXTS_ALLOC_FAIL`) trigger `VM_BUG_ON_FOLIO` or
`free_page_is_bad()`. `free_slab_obj_exts()` in `unaccount_slab()` must be
called unconditionally (not gated on `mem_alloc_profiling_enabled()` or
`memcg_kmem_online()`) because both can change at runtime between alloc and
free. It is idempotent (checks for NULL).

## Trylock-Only Allocation Paths (ALLOC_TRYLOCK)

`alloc_pages_nolock()` / `alloc_frozen_pages_nolock()` set `ALLOC_TRYLOCK` and clear
reclaim GFP flags (`gfpflags_allow_spinning()` returns false). Helpers in
`get_page_from_freelist()` must check `ALLOC_TRYLOCK` or
`gfpflags_allow_spinning()` and skip unconditional locks, or use a coarse
bailout only for **transient** conditions (persistent bailouts permanently
break the path).

**REPORT as bugs**: helpers reachable from `get_page_from_freelist()` using
`spin_lock()` without `ALLOC_TRYLOCK` / `gfpflags_allow_spinning()` checks.

## Memblock Range Parameter Conventions

Memblock uses two conventions: `(base, size)` for `memblock_add()`,
`memblock_remove()`, etc., and `(start, end)` for `reserve_bootmem_region()`,
`__memblock_find_range_*()`. Both parameters are `phys_addr_t` -- no compiler
type safety. Common mistake: passing `end` where `size` is expected (or vice
versa) in loops computing both `start = region->base` and
`end = start + region->size`. Check the function's parameter name (`size` vs
`end`) at each call site.

## Realloc Zeroing Lifecycle

In-place realloc shrink path must zero `[new_size, old_size)` when
`want_init_on_free()` OR `want_init_on_alloc(flags)` is true. These are
independent settings (`include/linux/mm.h`). Zeroing on `want_init_on_alloc`
during shrink is required because a subsequent in-place grow must not
re-expose stale data.

**Common mistake:** checking only `want_init_on_free()` on shrink -- misses
the `init_on_alloc` case. See `vrealloc_node_align_noprof()` in
`mm/vmalloc.c` and `__do_krealloc()` in `mm/slub.c`.

## kmemleak Tracking Symmetry

Allocation/free APIs must pair symmetrically for kmemleak: `kmalloc()` with
`kfree()`/`kfree_rcu()`, `kmalloc_nolock()` with `kfree_nolock()`. Mixing
them causes "Trying to color unknown object" warnings or false leak reports.

SLUB skips kmemleak registration when `!gfpflags_allow_spinning(flags)` (no
`__GFP_RECLAIM` bits). `kmemleak_not_leak()`, `kmemleak_ignore()`, and
`kmemleak_no_scan()` all warn on unregistered objects. When an allocation
path conditionally skips registration, all subsequent kmemleak state-change
calls must be guarded by the same condition.

## Quick Checks

- **NUMA node ID validation before `NODE_DATA()`**: `NODE_DATA(nid)` has no
  bounds check. User-provided node IDs need: `nid >= 0 && nid < MAX_NUMNODES
  && node_state(nid, N_MEMORY)`. See `do_pages_move()` in `mm/migrate.c`
- **`get_node(s, numa_mem_id())`** can return NULL on systems with memory-less
  nodes (see `get_node()` and `get_barn()` in `mm/slub.c`). A missing NULL
  check causes a NULL-pointer dereference that only triggers on NUMA systems
  with memory-less nodes
- **Node mask selection for allocation loops**: `for_each_online_node()`
  includes memoryless nodes. Use `for_each_node_state(nid, N_MEMORY)` for
  memory allocation. During early boot, `N_MEMORY` may not be populated yet
  (`free_area_init()` in `mm/mm_init.c` sets it); use memblock ranges instead
- **NUMA node count vs node ID range**: `num_node_state()` returns a count,
  not an upper bound on IDs (IDs can be sparse). Use `nr_node_ids` as the
  upper bound for raw iteration, or `for_each_node_state(nid, N_MEMORY)`
- **NUMA mempolicy-aware vs node-specific allocation**: `alloc_pages_node()`
  / `__alloc_pages_node()` bypass task NUMA policy (`mbind()`,
  `set_mempolicy()`). Replacing `alloc_pages()` / `folio_alloc()` with
  `_node` variants silently drops mempolicy — invisible in testing, pages
  land on wrong nodes. Branch: mempolicy-aware for `NUMA_NO_NODE`,
  node-specific for explicit node. See `___kmalloc_large_node()` in
  `mm/slub.c`
- **GFP flag propagation in allocation helpers**: when a function wraps
  an allocation and adds its own GFP flags (e.g., `__GFP_ZERO`,
  `__GFP_NOWARN`), it must preserve the caller's flags via bitwise OR,
  not replace them. Replacing the caller's `GFP_KERNEL` with
  `GFP_KERNEL | __GFP_ZERO` is correct; replacing it with just
  `__GFP_ZERO` drops reclaim and IO flags
- **SLUB `!allow_spin` retry loops**: in `___slab_alloc()` (`mm/slub.c`),
  `goto` back to retry after a trylock failure must check `!allow_spin`
  and return NULL. Trylock can fail deterministically (caller interrupted
  holder on same CPU), creating an infinite loop without a bail-out
- **KASAN tag reset in SLUB internals**: new `mm/slub.c` code accessing freed
  object memory (freelist linking, metadata) must call `kasan_reset_tag()`
  first. `kasan_slab_free()` poisons with a new tag; the old-tagged pointer
  triggers false use-after-free on ARM64 MTE. `set_freepointer()`/
  `get_freepointer()` handle this; generic helpers like `llist_add()` do not
- **`__GFP_MOVABLE` mobility contract**: pages allocated with
  `__GFP_MOVABLE` MUST be reclaimable or migratable. Common mistake:
  `movable_operations` registered conditionally (`#ifdef CONFIG_COMPACTION`)
  while `__GFP_MOVABLE` passed unconditionally. **REPORT as bugs**:
  `__GFP_MOVABLE` on pages with no migration support
- **Page allocator retry-loop termination**: every `goto retry` in
  `__alloc_pages_slowpath()` must modify state preventing the same path
  next iteration (clear flag, set bool, use bounded function). Without a
  guard, infinite loop prevents OOM killer. Verify `&= ~FLAG` not `&= FLAG`
- **Page allocator retry vs restart seqcount consistency**: `retry` reuses
  cached `ac->preferred_zoneref`; external state (cpuset nodemask,
  zonelists) can change. Every `goto retry` must call
  `check_retry_cpuset()` / `check_retry_zonelist()` to redirect to
  `restart` when stale. Otherwise allocator loops on stale zone iteration
- **Pageblock migratetype updates for high-order pages**: use
  `change_pageblock_range()` not bare `set_pageblock_migratetype()` for
  `order >= pageblock_order`. The bare function only updates the first
  pageblock; remaining ones keep stale migratetypes, causing freelist
  mismatches
- **Page allocator fallback cost in batched paths**: `rmqueue_bulk()` calls
  `__rmqueue()` in a loop under `zone->lock` with IRQs off. Fallback changes
  multiply across every page in the batch, causing latency spikes.
  `enum rmqueue_mode` caches failed levels across iterations. Evaluate any
  `__rmqueue_claim()`/`__rmqueue_steal()` change for per-iteration cost
- **PCP locking wrapper requirement**: `pcp->lock` must use PCP-specific
  wrappers (`pcp_spin_trylock()`, `pcp_spin_lock_maybe_irqsave()`), not bare
  `spin_lock()`. On `CONFIG_SMP=n`, `spin_trylock()` is a no-op; the PCP
  wrappers add `local_irq_save()`/`local_irq_restore()` to prevent IRQ
  reentrancy. Bare `spin_lock()` allows IRQ handler corruption of PCP lists
- **User page zeroing on cache-aliasing architectures**: `__GFP_ZERO` uses
  `clear_page()` which skips the dcache flush that `clear_user_highpage()`/
  `folio_zero_user()` provides. On cache-aliasing architectures, user-mapped
  pages need the flush. Use `user_alloc_needs_zeroing()` to check. Any
  optimization replacing `clear_user_highpage()` with `__GFP_ZERO` is wrong
  on these architectures
- **KASAN granule alignment in vmalloc poison/unpoison**: `kasan_poison()`/
  `kasan_unpoison()` require `KASAN_GRANULE_SIZE`-aligned addresses. In
  realloc paths, `vm->requested_size` is arbitrary — passing `p + old_size`
  directly triggers splats. Use `kasan_vrealloc()` which handles partial
  granule boundaries
- **`static_branch_*()` on allocation paths**: these acquire
  `cpus_read_lock()` internally. Calling from page allocator during CPU
  bringup deadlocks (bringup holds `cpu_hotplug_lock` for write). Use
  `_cpuslocked` variants or defer via `schedule_work()`
- **Early boot use of MM globals**: `high_memory` and zone PFNs are zero
  until `free_area_init()`. Use `memblock_end_of_DRAM()` instead of
  `__pa(high_memory)` in `__init` code. Guard `high_memory` with
  `IS_ENABLED(CONFIG_HIGHMEM)`. See `mm/cma.c`
- **NOWAIT error code translation**: NOWAIT callers expect `-EAGAIN` (retry
  in blocking context), not `-ENOMEM` (fatal). When downgrading GFP to
  NOWAIT, translate allocation failure to `-EAGAIN`. See
  `__filemap_get_folio_mpol()` `FGP_NOWAIT` in `mm/filemap.c`
- **GFP_KERNEL under locks in reclaim-reachable paths**: `GFP_KERNEL` can
  trigger direct reclaim, re-entering MM through swap-out, writeback, or slab
  shrinking. Deadlock if the allocation holds a lock reclaim also acquires.
  Move allocations outside the critical section or use `GFP_NOWAIT`/`GFP_ATOMIC`
- **Slab freelist pointer access must use accessors**: with
  `CONFIG_SLAB_FREELIST_HARDENED`, freelist pointers are XOR-encoded. Raw
  writes (`*(void **)ptr = NULL`) store un-encoded values that decode to
  garbage. Use `get_freepointer()` / `set_freepointer()` for all access
- **Slab post-alloc/free hook symmetry**: `slab_post_alloc_hook()` runs
  KASAN, kmemleak, KMSAN, alloc tagging, and memcg hooks. When a late hook
  fails, the error-free path must undo all that already ran. Compare any
  specialized free/abort path against `slab_free()` for the required hook
  sequence
- **SLUB bulk free staging buffer flush**: `free_to_pcs_bulk()` destructively
  moves objects from the caller's array to a staging buffer (`p[i] = p[--size]`).
  The staging buffer becomes the only reference. Every exit path must flush it
  if `remote_nr > 0` — missing a flush is a permanent leak
- **Direct map restore before page free**: when a page has been removed from
  the kernel direct map (via `set_direct_map_invalid_noflush()` in
  `include/linux/set_memory.h`), the direct map entry must be restored with
  `set_direct_map_default_noflush()` before the page is freed back to the
  allocator. Freeing first creates a window where another task allocates the
  page and faults via the still-invalid direct map. See `secretmem_fault()`
  and `secretmem_free_folio()` in `mm/secretmem.c`
