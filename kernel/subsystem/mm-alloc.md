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
  `wakeup_kswapd()` in `mm/vmscan.c`, which calls `wake_up_interruptible()` and
  enters the scheduler via `try_to_wake_up()`. This means even non-sleeping
  allocations can take scheduler and timer locks. Code that may allocate while
  holding scheduler or timer internal locks (runqueue lock, hrtimer base lock)
  or the kswapd waitqueue lock, or that can be entered from arbitrary locking
  context, must not pass `__GFP_KSWAPD_RECLAIM` unless it can show the context
  is safe; otherwise use flags without reclaim bits, e.g. `__GFP_NOWARN`.
  Debugobjects `fill_pool()` in `lib/debugobjects.c` starts from
  `__GFP_HIGH | __GFP_NOWARN` and adds `__GFP_KSWAPD_RECLAIM` only when
  `preemptible()` or before `SYSTEM_SCHEDULING`. Ordinary `GFP_ATOMIC` /
  `GFP_NOWAIT` use under a `spinlock_t` or in interrupt context is the
  documented purpose of those flags; under a `raw_spinlock_t` or
  `preempt_disable()` it is fine only on !PREEMPT_RT. `gfp_nested_mask()` in
  `include/linux/gfp.h` is the standard way to inherit the caller's
  reclaim/IO/FS context for nested allocations. It preserves
  `__GFP_KSWAPD_RECLAIM` if the caller had it, so it does not address the
  wakeup problem above
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

**Placement constraints** (see "Physical address zone modifiers" and "Page
mobility and placement hints" in `include/linux/gfp_types.h`):
- `GFP_ZONEMASK` (`__GFP_DMA | __GFP_HIGHMEM | __GFP_DMA32 | __GFP_MOVABLE`)
  selects the physical memory zone. Code that intercepts allocations and serves
  memory from a pre-allocated pool (e.g., KFENCE in `mm/kfence/core.c`) must
  skip requests with zone constraints it cannot satisfy
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
`__alloc_pages_noprof()` wraps this and calls `set_page_refcounted()` to return
refcount 1. The `*_frozen_*()` variants (`__alloc_frozen_pages_noprof()`,
`alloc_frozen_pages_nolock_noprof()`) return frozen pages for callers that
manage refcount themselves (slab, hugetlb, the mempolicy wrappers). CMA gets
its frozen pages from `alloc_contig_frozen_range()`. Compaction and
`alloc_pages_bulk` get frozen pages from lower-level paths and call
`set_page_refcounted()` themselves. **REPORT as bugs**: passing a frozen page
to code expecting refcount 1 without calling `set_page_refcounted()`, or
calling `set_page_refcounted()` on a page intended to stay frozen.

## Zone Watermarks and lowmem_reserve

`zone[i].lowmem_reserve[j]` protects zone `i` (not zone `j`) from
over-consumption by allocations targeting zone `j`. The effective watermark is
`watermark[wmark] + lowmem_reserve[j]` (see `__zone_watermark_ok()` in
`mm/page_alloc.c`). A zone's own entry is always 0, which
`__zone_watermark_ok()` relies on whenever `highest_zoneidx` equals the zone's
own index. **REPORT as bugs**: code that expects a non-zero reserve from
`zone->lowmem_reserve[zone_idx(zone)]`, or that assumes `lowmem_reserve[j]`
protects zone `j`.

**Per-CPU vmstat counter drift:** `zone_page_state()` omits per-CPU deltas; on
many-CPU systems the error can exceed watermark gaps. The kswapd balance check
(`pgdat_balanced()` in `mm/vmscan.c`) open-codes the remedy: if
`zone->percpu_drift_mark` is set and `zone_page_state()` is below it, it
re-reads with `zone_page_state_snapshot()`. `zone_watermark_ok_safe()` no
longer exists. `zone_watermark_ok()` and `zone_watermark_fast()` deliberately
use the cheap `zone_page_state()`. Flag changes to kswapd sleep/balance
decisions that drop the drift-mark re-read; do not require it in allocator fast
paths. `should_reclaim_retry()` in `mm/page_alloc.c` always uses the snapshot.

## Zone Watermark Initialization Ordering

Zone watermarks are zero until `init_per_zone_wmark_min()` runs as a
`postcore_initcall()` (`mm/page_alloc.c`). Before that, `zone_watermark_ok()`
trivially passes, masking the need for reclaim/acceptance. Code reachable
during early boot must handle `wmark == 0` as "not yet initialized" (use a
fallback threshold or unconditionally perform the required work).

## Layered vmstat Accounting (Node vs Memcg)

`lruvec_stat_mod_folio()` / `mod_lruvec_page_state()` update both node and
memcg counters only when `folio_memcg(folio)` is non-NULL; otherwise they
update only the node counter. `mod_node_page_state()` is always node-only;
`mod_lruvec_state()` is always both (when memcg is enabled).

**Stat reconciliation on deferred charging:** when a folio is allocated
without a memcg and stats are recorded, only the node counter increments.
If later charged (e.g., `kmem_cache_charge()` in `mm/slub.c`), the post-
charge path must subtract from the node counter and re-add via the lruvec
interface to populate the memcg counter, or the free path will underflow it.

Review any code path that changes a folio's memcg association after allocation
for stat counters recorded before the association existed.

## Slab Page Overlay Initialization and Cleanup

`struct slab` overlays `struct page` (verified by `SLAB_MATCH()` assertions in
`mm/slab.h`; the folio match is transitive). The page allocator does NOT zero
metadata fields, so every field -- especially conditionally-compiled ones
(`CONFIG_*` ifdefs) invisible in most builds -- must be initialized before use,
in `allocate_slab()` in `mm/slub.c` or, for the freelist, in
`build_slab_freelist()`.

On free, `slab->obj_exts` shares storage with `folio->memcg_data`. Leftover
sentinel values (e.g., `OBJEXTS_ALLOC_FAIL`) trigger `VM_BUG_ON_FOLIO()` or
`free_page_is_bad()`. `free_slab_obj_exts()` in `unaccount_slab()` must be
called unconditionally (not gated on `mem_alloc_profiling_enabled()` or
`memcg_kmem_online()`) because both can change at runtime between alloc and
free. It is idempotent (checks for NULL).

## Trylock-Only Allocation Paths (ALLOC_NOLOCK)

`alloc_pages_nolock()` / `alloc_frozen_pages_nolock()` set `ALLOC_NOLOCK`.
Callers may pass only `__GFP_ACCOUNT` plus bits already in `gfp_nolock`
(anything else trips a `VM_WARN_ON_ONCE()` in `__alloc_frozen_pages_noprof()`,
which then ORs `gfp_nolock` in), so by contract no reclaim bit is ever set and
`gfpflags_allow_spinning()` returns false. Helpers in
`get_page_from_freelist()` must check `ALLOC_NOLOCK` or
`gfpflags_allow_spinning()` and skip unconditional locks, or use a coarse
bailout only for **transient** conditions (persistent bailouts permanently
break the path).

**REPORT as bugs**: helpers reachable from `get_page_from_freelist()` that can
take a spinning lock on the `ALLOC_NOLOCK` path, that is, not protected by an
`ALLOC_NOLOCK` / `gfpflags_allow_spinning()` check, by the up-front
`alloc_nolock_allowed()` bailout, or by an alloc flag or GFP bit that
`gfp_nolock` can never produce (`ALLOC_KSWAPD`, `ALLOC_HIGHATOMIC`,
`__GFP_DIRECT_RECLAIM`). `reserve_highatomic_pageblock()`,
`_deferred_grow_zone()` and the `wakeup_kswapd()` call in `rmqueue()` take
locks with no such check and are correct for that reason.

## Memblock Range Parameter Conventions

Memblock uses two conventions: `(base, size)` for `memblock_add()`,
`memblock_remove()`, etc., and `(start, end)` for
`memmap_init_reserved_range()` (static in `mm/memblock.c`),
`__memblock_find_range_*()`. Both parameters are `phys_addr_t` -- no compiler
type safety. Common mistake: passing `end` where `size` is expected (or vice
versa) in loops computing both `start = region->base` and
`end = start + region->size`. Check the function's parameter name (`size` vs
`end`) at each call site.

## Realloc Zeroing Lifecycle

`want_init_on_free()` and `want_init_on_alloc()` are independent settings
(`include/linux/mm.h`), and the two in-place realloc paths treat them
differently.

`vrealloc_node_align_noprof()` in `mm/vmalloc.c` zeroes `[new_size, old_size)`
on an in-place shrink when `want_init_on_free() || want_init_on_alloc(flags)`,
and therefore does not zero on an in-place grow. Zeroing on
`want_init_on_alloc()` during shrink is required there because a subsequent
in-place grow must not re-expose stale data. **Common mistake** (vrealloc):
checking only `want_init_on_free()` on shrink -- misses the `init_on_alloc`
case.

`__do_krealloc()` in `mm/slub.c` is different. It gates only on
`want_init_on_alloc(flags)`, zeroing `[orig_size, new_size)` on a tracked
in-place grow and otherwise `[new_size, ks)` up to the full object size. It
never tests `want_init_on_free()`; do not report that as missing.

## kmalloc Alignment Guarantees

`kmalloc()` makes a documented alignment guarantee:

- The returned address is aligned to at least `ARCH_KMALLOC_MINALIGN`.
- **For power-of-two sizes the alignment is at least the size itself.**
  `kmalloc(PAGE_SIZE, ...)` is therefore always `PAGE_SIZE`-aligned, and
  `PAGE_ALIGNED()` / `IS_ALIGNED(p, PAGE_SIZE)` on it is always true.
- For other sizes the alignment is at least the largest power-of-two divisor
  of the size.

This is a property of the API, not an artifact of the current implementation.
See `Documentation/core-api/memory-allocation.rst`, the `kmalloc()` kernel-doc
in `include/linux/slab.h`, and commit 59bb47985c1d ("mm, sl[aou]b: guarantee
natural alignment for kmalloc(power-of-two)").

It is enforced by construction:

- `create_boot_cache()` in `mm/slab_common.c` raises the cache alignment to
  `1U << (ffs(size) - 1)` for any `SLAB_KMALLOC` cache, i.e. to the size for
  power-of-two sizes.
- Allocations larger than `KMALLOC_MAX_CACHE_SIZE` bypass the slab caches and
  go straight to the page allocator, so they are at least page-aligned.

**Debug options do not weaken it.** `calculate_sizes()` in `mm/slub.c` rounds
the redzone padding up to the cache alignment (`s->red_left_pad =
ALIGN(s->red_left_pad, s->align)`) and then sizes each object to
`ALIGN(size, s->align)`. Holding the guarantee under debug was the point of
59bb47985c1d.

**Do NOT report** that memory from `kmalloc()`/`kzalloc()` of a power-of-two
size may be insufficiently aligned, that its alignment is "not guaranteed", or
that `SLUB_DEBUG` / redzones / `KASAN` / `kmemleak` / `SLAB_STORE_USER` can
shift an object off its natural alignment. Callers that depend on the
alignment, e.g. via `PAGE_ALIGNED()` or by masking low address bits, are
correct to do so; finding such a caller is not evidence of a bug.

A genuine alignment finding requires an alignment the allocator can actually
return: verify the requested size is not a power of two, or that the required
alignment exceeds it, and quote the code that misbehaves at the alignment
actually guaranteed for that size.

## Suitability of kmalloc Memory

kmalloc memory is physically contiguous and shares its backing pages with
unrelated objects. That second property, not alignment, determines where it
cannot be used.

**Not usable when the caller treats the backing page as its own**: it takes or
drops a page reference (`get_page()`, `try_get_page()`, `put_page()`; a page
reference never pins a slab object, and since v6.14 slab pages have a zero
refcount, so these warn or return early), sets page flags (`SetPage*()`),
reads or writes `struct page` fields other than the flags (`->mapping`,
`->private`, `->lru`; `struct slab` in `mm/slab.h` overlays them), maps the
page to userspace (`vm_insert_page()`, `remap_pfn_range()`, a `->fault`
handler), has the network stack splice it in by reference (`sendmsg()` with
`MSG_SPLICE_PAGES`, which replaced `->sendpage()` in v6.5; callers test
`sendpage_ok()`, which rejects slab pages, and fall back to copying), or hands
it to a hypervisor or firmware interface that reclaims or frees whole page
frames. Neighbouring objects in the same page are corrupted or exposed, or the
buffer is freed and reused while the caller believes it still holds a
reference.

Looking the page up is not the problem. `virt_to_page()` and `page_to_pfn()`
on a kmalloc buffer are routine: `sg_set_buf()` and `dma_map_single()` both
call `virt_to_page()` on the buffer they are given, and kmalloc memory is a
normal argument to both. A finding needs the caller to then do one of the
things above with the page, not merely to have converted the address.

**`__GFP_DMA32` does not select a DMA32 kmalloc cache.** It is absent from
`KMALLOC_NOT_NORMAL_BITS`, and `kmalloc_type()` in `include/linux/slab.h`
branches only on `__GFP_DMA`, `__GFP_RECLAIMABLE` and `__GFP_ACCOUNT`. A
`GFP_DMA32` kmalloc can return memory above 4G, silently breaking
32-bit-addressable DMA or an interface taking a 32-bit physical address. The
flag is in `GFP_SLAB_BUG_MASK`, so `new_slab()` and the large-kmalloc path
strip it through `kmalloc_fix_flags()`, which prints "Unexpected gfp ... Fix
your code!" and dumps the stack. An allocation served from an existing slab or
sheaf triggers nothing, so the warning is intermittent and easily missed in
testing.

**Above `KMALLOC_MAX_CACHE_SIZE`** the allocation is served by the page
allocator, with that path's order limits and failure behaviour.

Physical contiguity, `virt_to_phys()` / `__pa()` / `__va()`, `virt_to_page()`
to build a scatterlist, DMA mapping, and page-size alignment of a power-of-two
allocation are all sound on kmalloc memory and are **not** grounds for a
finding.

## kmemleak Tracking Symmetry

`kfree_nolock()` may only free objects from `kmalloc_nolock()`. `kmalloc()`
followed by `kfree_nolock()` skips `kmemleak_free()` / `kfence_free()` and
leaves stale tracking behind (false leak reports). The reverse is allowed since
v7.0 (c4d6d7829817): `kmalloc_nolock()` objects may be freed with `kfree()` /
`kfree_rcu()`, as `kernel/bpf/bpf_local_storage.c` does.

SLUB skips kmemleak registration for `kmalloc_nolock()` allocations only:
`slab_post_alloc_hook()` tests `alloc_flags_allow_spinning(ac->alloc_flags)`,
which is `!(alloc_flags & SLAB_ALLOC_NOLOCK)` in `mm/slab.h`, not the GFP mask
(since v7.2; before that the test was `gfpflags_allow_spinning(flags)`). A
plain `kmalloc(sz, __GFP_NOWARN)` with no reclaim bits is still registered.
Since v7.0 `kmemleak_not_leak()`, `kmemleak_ignore()` and `kmemleak_free()`
silently ignore unregistered objects; `kmemleak_no_scan()` still warns. In a
`SLAB_ALLOC_NOLOCK` path kmemleak calls must still be skipped, because kmemleak
takes spinlocks: see `if (allow_spin) kmemleak_not_leak(vec)` in
`alloc_slab_obj_exts()`.

## Quick Checks

- **NUMA node ID validation before `NODE_DATA()`**: `NODE_DATA(nid)` has no
  bounds check. User-provided node IDs need: `nid >= 0 && nid < MAX_NUMNODES
  && node_state(nid, N_MEMORY)`. See `do_pages_move()` in `mm/migrate.c`
- **`get_node(s, numa_mem_id())`** can return NULL on systems with memory-less
  nodes (see `get_node()` and the `!n` check in `get_from_partial_node()` in
  `mm/slub.c`). A missing NULL check causes a NULL-pointer dereference that
  only triggers on NUMA systems with memory-less nodes
- **Node mask selection for allocation loops**: `for_each_online_node()`
  includes memoryless nodes. Use `for_each_node_state(nid, N_MEMORY)` for
  memory allocation. During early boot, `N_MEMORY` may not be populated yet
  (`free_area_init()` in `mm/mm_init.c` sets it); use memblock ranges instead
- **NUMA node count vs node ID range**: `num_node_state()` returns a count,
  not an upper bound on IDs (IDs can be sparse). Use `nr_node_ids` as the
  upper bound for raw iteration, or `for_each_node_state(nid, N_MEMORY)`
- **NUMA mempolicy-aware vs node-specific allocation**: `alloc_pages_node()`
  bypasses task NUMA policy (`set_mempolicy()`; a VMA policy from `mbind()`
  applies only on paths that look it up: `vma_alloc_folio()`, or
  `get_vma_policy()` plus `folio_alloc_mpol()` as in swap-in, shmem and
  hugetlb). Replacing `alloc_pages()` / `folio_alloc()` with `*_node()`
  variants silently drops mempolicy — invisible in testing, pages land on wrong
  nodes. Branch: mempolicy-aware for `NUMA_NO_NODE`, node-specific for explicit
  node. See `___kmalloc_large_node()` in `mm/slub.c`
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
- **`__GFP_MOVABLE` mobility contract**: pages allocated with `__GFP_MOVABLE`
  MUST be reclaimable or migratable. Common mistake:
  `struct movable_operations` registered conditionally
  (`#ifdef CONFIG_COMPACTION`) while `__GFP_MOVABLE` passed unconditionally.
  **REPORT as bugs**: `__GFP_MOVABLE` on pages with no migration support
- **Page allocator retry-loop termination**: every `goto retry` in
  `__alloc_pages_slowpath()` that precedes the `__alloc_pages_may_oom()` call
  must modify state preventing the same path next iteration (clear flag, set
  bool, use bounded function). Without a guard, infinite loop prevents OOM
  killer. Verify `&= ~FLAG` not `&= FLAG`. The two retries after the OOM step
  (while the OOM killer makes progress, and for `__GFP_NOFAIL`) are
  intentionally unbounded
- **Page allocator retry vs restart seqcount consistency**: `retry` reuses
  cached `ac->preferred_zoneref`; external state (cpuset nodemask,
  zonelists) can change. A `goto retry` that can execute more than once must
  come after a `check_retry_cpuset()` / `check_retry_zonelist()` test that
  redirects to `restart` when stale. One-shot retries guarded by a bool or
  flag that is cleared first (`can_retry_reserves`, `compact_first`,
  `ALLOC_NOFRAGMENT`) may sit above it; the comment above the first check in
  `__alloc_pages_slowpath()` states exactly this. Otherwise allocator loops on
  stale zone iteration
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
  wrappers (`pcp_spin_trylock()`, `pcp_spin_lock_nopin()`), not bare
  `spin_trylock()`. On `CONFIG_SMP=n` the UP `spin_trylock()` never fails, so
  `pcp_spin_trylock()` always returns NULL there and callers take the slow
  path. A bare `spin_trylock()` would appear to succeed on UP while an
  interrupted holder is inside the critical section, corrupting the PCP
  lists. `pcp_spin_trylock()` also pins the task to the CPU for the lookup
  plus lock; `pcp_spin_lock_nopin()` is for callers already handed a specific
  CPU's pcp pointer
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
- **`static_branch_enable()` / `static_branch_disable()` /
  `static_branch_inc()` / `static_branch_dec()` on allocation paths**: these
  acquire `cpus_read_lock()` internally (`static_branch_likely()` /
  `static_branch_unlikely()` take nothing and are everywhere in the fast
  paths). Calling from page allocator during CPU bringup deadlocks (bringup
  holds `cpu_hotplug_lock` for write). Use `*_cpuslocked()` variants or defer
  via `schedule_work()`
- **Early boot use of MM globals**: `high_memory` and zone PFNs are zero
  until `free_area_init()`. Use `memblock_end_of_DRAM()` instead of
  `__pa(high_memory)` in `__init` code. Guard `high_memory` with
  `IS_ENABLED(CONFIG_HIGHMEM)`. See `mm/cma.c`
- **Early boot memory allocation failures**: functions executed only early in the boot
  process (e.g., marked with `__init`) usually do not need to handle memory
  allocation failures gracefully. At this stage, physical memory should be
  available, and an allocation failure typically means the system cannot boot
  anyway. Complex error handling, cleanup logic, or returning `-ENOMEM` in
  these functions is often unnecessary dead code.
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
- **Direct map restore before page free**: when a page has been removed from
  the kernel direct map (via `set_direct_map_invalid_noflush()`, declared
  through `include/linux/set_memory.h` and implemented per-arch), the direct
  map entry must be restored with `set_direct_map_default_noflush()` before the
  page is freed back to the allocator. Freeing first creates a window where
  another task allocates the page and faults via the still-invalid direct map.
  See `secretmem_fault()` and `secretmem_free_folio()` in `mm/secretmem.c`
