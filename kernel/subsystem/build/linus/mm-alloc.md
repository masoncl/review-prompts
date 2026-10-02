# MM Memory Allocation

## Main structures

### Objects and how they relate

- Per-CPU slab layer: there is no kmem_cache_cpu in this tree. Each
  `struct kmem_cache` has a per-CPU `struct slub_percpu_sheaves` with a `main`,
  a `spare` and an `rcu_free` `struct slab_sheaf`.
- `struct slab_sheaf`: an array of object pointers, not a slab. No slab is
  owned by a CPU; there is no per-CPU current slab and no per-CPU partial list.
- `struct node_barn`: per cache and per node, a stock of full and empty
  sheaves that CPUs swap with, loosely bounded by `MAX_FULL_SHEAVES` and
  `MAX_EMPTY_SHEAVES`. It sits between the per-CPU sheaves and
  `struct kmem_cache_node`.
- Slab allocation order: per-CPU sheaf, then barn, then node partial list, then
  a new slab. See `alloc_from_pcs()` and `___slab_alloc()` in `mm/slub.c`.
- Object held in a sheaf: free to its user, but still counted in `inuse` of its
  `struct slab`.
- Sheaves and barns are themselves kmalloc objects; kmalloc caches get theirs
  late, in `bootstrap_kmalloc_sheaves()`.
- Caller-owned sheaf: `kmem_cache_prefill_sheaf()` hands a `struct slab_sheaf`
  to the caller, linked to no CPU or barn until `kmem_cache_return_sheaf()`.
  For example `mt_get_sheaf()` in `lib/maple_tree.c`.
- `frozen` in `struct slab`: means the slab failed a consistency check and is
  never allocated from again. `SL_partial` marks a slab on the node partial
  list.
- `struct slabobj_ext`: a struct that holds one pointer-sized union. An object
  has one or two of them, depending on whether the slab needs an objcg and
  whether `slab_obj_ext_has_codetag()` is true.
- A free page is in one of these places: `struct free_area`, a
  `struct per_cpu_pages` list, `trylock_free_pages` in `struct zone`, where
  a `FPI_NOLOCK` free parks it when a lock cannot be taken, or, under
  `CONFIG_UNACCEPTED_MEMORY`, `unaccepted_pages` in `struct zone`.
- Page type of a free page: only pages in `struct free_area` carry
  `PGTY_buddy`. A page on a pcp list or on `trylock_free_pages` has no page
  type.
- `memcg_data` of a charged folio: holds a `struct obj_cgroup *` for LRU folios
  as well as kmem pages; `folio_memcg()` goes through `folio_objcg()`. In a
  slab the same word holds the `struct slabobj_ext` vector, flagged
  `MEMCG_DATA_OBJEXTS`.

## Where to look

**Core files**

| Job | File | Easy to miss |
|---|---|---|
| GFP bit definitions | `include/linux/gfp_types.h` | Also holds the composites such as `GFP_KERNEL` and `GFP_ATOMIC`; `include/linux/gfp.h` defines none of them. mm-only masks `GFP_BOOT_MASK`, `GFP_RECLAIM_MASK`, `GFP_SLAB_BUG_MASK` are in `mm/internal.h`. |
| Helpers that test a mask | `include/linux/gfp.h` | `gfp_migratetype()` is not here; it is in `mm/page_alloc.h`. There is no gfpflags_normal_context() in this tree. |
| Page allocator, mm-internal declarations | `mm/page_alloc.h` | Holds the `ALLOC_` flags (`ALLOC_NOLOCK`, `ALLOC_NO_CODETAG`), `struct alloc_context`, `__alloc_frozen_pages_noprof()`, `free_frozen_pages()` and also `__alloc_pages_noprof()`. `mm/internal.h` holds none of these and does not include `mm/page_alloc.h`; a file that uses both includes both, as `mm/slub.c` does. |
| What stays in `mm/internal.h` | `mm/internal.h` | `set_page_refcounted()`, `can_spin_trylock()`, `struct compact_control`, `struct capture_control`. |
| Slab internal header | `mm/slab.h` | Also holds slab's own flags (`SLAB_ALLOC_NOLOCK` and the other `SLAB_ALLOC_` and `SLAB_FREE_` values) and the inline `kmalloc_slab()`. `struct slab_alloc_context` is in `mm/slub.c`; it is a separate type from `struct alloc_context`. |
| Code shared by all kmalloc caches | `mm/slab_common.c` | Holds `kmalloc_caches[]`, `kmalloc_info[]`, `kmalloc_size_index[]`. `kmalloc_slab()` is in `mm/slab.h`; `__kmalloc_large_noprof()` is in `mm/slub.c`. |
| vmalloc | `mm/vmalloc.c` | mm-internal declarations are in `mm/vmalloc.h`. |
| Boot allocator hand-over | `mm/memblock.c`, `mm/mm_init.h` | `memblock_free_all()` is declared only in `mm/mm_init.h`; `memblock_free_pages()` is defined in `mm/mm_init.c`. |
| Allocation profiling | `mm/alloc_tag.c`, `include/linux/alloc_tag.h` | There is no alloc_tag.c under `lib/`; only `lib/codetag.c` is there. Page hooks `pgalloc_tag_add()` and `pgalloc_tag_sub()` are static in `mm/page_alloc.c`; slab hook `alloc_tagging_slab_alloc_hook()` is in `mm/slub.c`; `include/linux/pgalloc_tag.h` holds the page tag reference accessors, not these hooks. |
| Page allocator, slab allocator, mempools, zone and watermark initialisation, memory policy | — | Models have this right; see `mm/page_alloc.c`, `mm/slub.c`, `mm/mempool.c`, `mm/mm_init.c` (zones; the watermarks are set in `mm/page_alloc.c`), `mm/mempolicy.c`. |

**Entry points**

| Job | Start reading from | Easy to miss |
|---|---|---|
| Allocate pages with a reference | `alloc_pages_noprof()`; `alloc_pages_node_noprof()` in `mm/page_alloc.c` | `__alloc_pages_noprof()` is mm-internal: declared in `mm/page_alloc.h`, not exported, five arguments ending in `alloc_flags`. With `CONFIG_NUMA`, `alloc_pages_noprof()` is in `mm/mempolicy.c` and does not call it: it calls `alloc_frozen_pages_noprof()`, then `set_page_refcounted()`. `__get_free_pages()` is a macro over `get_free_pages_noprof()`. |
| Allocate pages without a reference | `__alloc_frozen_pages_noprof()` in `mm/page_alloc.c` | Fifth argument `alloc_flags`: any bit other than `ALLOC_NOLOCK` and `ALLOC_NO_CODETAG` hits a `WARN_ON()` and returns `NULL`; ordinary callers pass `ALLOC_DEFAULT`. `alloc_frozen_pages_noprof()` is in `mm/mempolicy.c` under `CONFIG_NUMA`, inline in `mm/page_alloc.h` otherwise. |
| Free pages | static `__free_frozen_pages()` in `mm/page_alloc.c` | `__free_pages()` reaches it through static `___free_pages()`; `free_frozen_pages()` calls it directly. It usually puts the page on a per-CPU list, not into `__free_one_page()`. |
| Allocate one slab object | `slab_alloc_node()` in `mm/slub.c` | Takes a `const struct slab_alloc_context *`. Tries `alloc_from_pcs()` for every cache, then `___slab_alloc()`; there is no struct kmem_cache_cpu in this tree. A cache for which `cache_has_sheaves()` is false falls through to `___slab_alloc()`. |
| Free one slab object | `slab_free()` in `mm/slub.c` | Tries `free_to_pcs()` first when `can_free_to_pcs()` allows, then `__slab_free()`. |
| kmalloc above the largest cache | `___kmalloc_large_node()` in `mm/slub.c` | Takes frozen pages (`alloc_frozen_pages_noprof()` or `__alloc_frozen_pages_noprof()`); `free_large_kmalloc()` returns them with `free_frozen_pages()`. |
| Allocate from any context, pages | `alloc_pages_nolock_noprof()` in `mm/page_alloc.c` | Frozen form `alloc_frozen_pages_nolock_noprof()`. The flag is `ALLOC_NOLOCK`, and `FPI_NOLOCK` on the free side (`free_pages_nolock()`, `free_frozen_pages_nolock()`); there is no ALLOC_TRYLOCK. |
| Allocate from any context, objects | `_kmalloc_nolock_noprof()` in `mm/slub.c` | `kmalloc_nolock_noprof()` is a macro in `include/linux/slab.h`. The body is static `__kmalloc_nolock_noprof()`; it returns `NULL` above `KMALLOC_MAX_CACHE_SIZE`. `__kmalloc_flags_noprof()` (defined in `mm/slub.c`, declared in `mm/slab.h`) picks this path when given `SLAB_ALLOC_NOLOCK`. |
| Allocate a physically contiguous range | `alloc_contig_frozen_range_noprof()` in `mm/page_alloc.c` | `alloc_contig_range_noprof()` is a wrapper: it rejects `__GFP_COMP`, then sets the references. `alloc_contig_pages_noprof()` wraps `alloc_contig_frozen_pages_noprof()` the same way. `cma_alloc()` in `mm/cma.c` reaches the frozen form through `cma_range_alloc()`. |
| Take an element from a mempool | `mempool_alloc_noprof()` in `mm/mempool.c` | The pool lock, `remove_element()` and the wait are in `mempool_alloc_from_pool()`, shared with `mempool_alloc_bulk_noprof()` and `mempool_alloc_preallocated()`. |
| Resize a vmalloc area | `vrealloc_node_align_noprof()` in `mm/vmalloc.c` | `vrealloc_noprof()` and `vrealloc_node_noprof()` are macros over it in `include/linux/vmalloc.h`. |
| Allocate before the page allocator is up | — | Models have this right; see `memblock_alloc_try_nid()` in `mm/memblock.c`. |

## GFP masks

**Composite masks and sleeping**

- Models have the table and the deciding bit right; see
  `include/linux/gfp_types.h` and `gfpflags_allow_blocking()` in
  `include/linux/gfp.h`.
- `GFP_TRANSHUGE_LIGHT`: a composite with neither reclaim bit (it is built
  with `& ~__GFP_RECLAIM`), so it neither sleeps nor wakes kswapd;
  `GFP_TRANSHUGE` adds back only `__GFP_DIRECT_RECLAIM`.

**memalloc scopes**

- Page allocator: `__alloc_frozen_pages_noprof()` in `mm/page_alloc.c` calls
  `current_gfp_context()` itself, after `gfp &= gfp_allowed_mask` and before
  `prepare_alloc_pages()`.
- `prepare_alloc_pages()`: does not narrow the mask; it calls `might_alloc()`
  on the mask it is given.
- Slab: `mm/slub.c` never calls `current_gfp_context()`;
  `slab_pre_alloc_hook()` does `flags &= gfp_allowed_mask`, `might_alloc()`
  and `should_failslab()`.
- Inside slab the mask is the caller's, scope not applied; the scope takes
  effect when `alloc_slab_page()` calls the page allocator and when a reclaim
  entry point builds `struct scan_control`.
- `memalloc_apply_gfp_scope()` callers: `__vmalloc_area_node()`, and code in
  `mm/kasan/shadow.c` and `mm/percpu-vm.c`, around page-table allocations
  that ignore the mask.
- Other allocators apply the scope themselves, for example
  `pcpu_alloc_noprof()` in `mm/percpu.c` and
  `alloc_contig_frozen_range_noprof()`; search for `current_gfp_context(`.

**Locks shared with reclaim**

- There is no __need_fs_reclaim() here; `__need_reclaim()` in
  `mm/page_alloc.c` tests `__GFP_DIRECT_RECLAIM`, `PF_MEMALLOC` and
  `__GFP_NOLOCKDEP`.
- `__GFP_FS`: tested in `fs_reclaim_acquire()` itself, after
  `current_gfp_context()`, and gates only `__fs_reclaim_map`.
- `__mmu_notifier_invalidate_range_start_map`: under `CONFIG_MMU_NOTIFIER`,
  `fs_reclaim_acquire()` acquires and releases it for every mask that passes
  `__need_reclaim()`, including `GFP_NOFS` and `GFP_NOIO`.
- `might_alloc()`: returns before `might_sleep_if()` when the task has
  `PF_MEMALLOC`.
- `__kmalloc_nolock_noprof()`: does not call `slab_pre_alloc_hook()`, so slab
  makes no `might_alloc()` call for it.
- Reclaim-side holders of `__fs_reclaim_map`:
  - `balance_pgdat()`: unconditionally, through `__fs_reclaim_acquire()`.
  - `__perform_reclaim()`, `__alloc_pages_direct_compact()`,
    `__node_reclaim()`, `shrink_all_memory()`: through
    `fs_reclaim_acquire()`, so only when the mask has `__GFP_FS`.
- Lockdep blind spot: an allocation whose effective mask lacks `__GFP_FS`
  never acquires `__fs_reclaim_map`, so a lock that reclaim takes whatever
  the mask is, outside an mmu notifier callback, gets no `might_alloc()`
  report under `GFP_NOFS` or `GFP_NOIO`.
- Priming: code teaches lockdep "reclaim takes L" at init by taking L between
  `fs_reclaim_acquire(GFP_KERNEL)` and `fs_reclaim_release(GFP_KERNEL)`, as
  `dma_resv_lockdep()` in `drivers/dma-buf/dma-resv.c` does.
- **Potentially unsafe usage**: relying on `GFP_NOFS` or
  `memalloc_nofs_save()` to keep reclaim away from a held lock.
  - Unsafe: when the reclaim code that takes the lock does not test
    `sc->gfp_mask`; direct reclaim still runs and still calls it.
  - Safe: when that code returns early without `__GFP_FS`, as
    `super_cache_scan()` in `fs/super.c` does.
  - Safe: when the mask lacks `__GFP_DIRECT_RECLAIM` or the task has
    `PF_MEMALLOC`; `__alloc_pages_slowpath()` then does not enter direct
    reclaim.

**Testing a mask**

- `gfpflags_allow_spinning()`: returns `gfp & __GFP_RECLAIM`, true if either
  reclaim bit is set.
- `mm/page_alloc.c` and `mm/slub.c` do not call it: trylock-only mode comes
  from `ALLOC_NOLOCK` in `mm/page_alloc.h` and `SLAB_ALLOC_NOLOCK` in
  `mm/slab.h`, set for `alloc_pages_nolock()` and `kmalloc_nolock()`
  requests.
- A mask with no reclaim bit passed to `alloc_pages()` or `kmalloc()`: still
  spins on locks, for example `zone->lock` in `rmqueue_buddy()`.
- `gfpflags_allow_spinning()` is tested outside the allocators, for example
  in `try_charge_memcg()` and `stack_depot_save_flags()`;
  `__reset_page_owner()` passes `__GFP_NOWARN` alone to make it false.
- `gfp_has_flags()` in `include/linux/gfp.h`: the helper for
  `(gfp & flags) == flags`; `gfp_has_io_fs()` is built on it.
- `__kvmalloc_node_noprof()`: has no test against `GFP_KERNEL`.
- In-tree subset tests against `GFP_KERNEL`, for example:
  - `nfs_release_folio()` in `fs/nfs/file.c`:
    `(current_gfp_context(gfp) & GFP_KERNEL) != GFP_KERNEL`, scope applied
    first.
  - `rpcauth_cache_shrink_scan()` in `net/sunrpc/auth.c`:
    `(sc->gfp_mask & GFP_KERNEL) != GFP_KERNEL`.
- `objpool_init_percpu_slots()` in `lib/objpool.c`: masks with
  `GFP_ATOMIC | GFP_KERNEL` and compares with `GFP_ATOMIC`, which also
  requires `__GFP_DIRECT_RECLAIM`, `__GFP_IO` and `__GFP_FS` to be clear.
- **Potentially unsafe usage**: `(gfp & GFP_ATOMIC) == GFP_ATOMIC` or
  `(gfp & GFP_NOWAIT) == GFP_NOWAIT` as a test for "cannot sleep"; the first
  is true for `GFP_KERNEL | __GFP_HIGH`, the second for
  `GFP_KERNEL | __GFP_NOWARN`.
  - Unsafe: when the result decides whether the code may sleep; the first
    test is also false for `GFP_NOWAIT`, the second for `GFP_ATOMIC`, and
    neither constant holds `__GFP_DIRECT_RECLAIM`, the bit that
    `gfpflags_allow_blocking()` tests.
  - Safe: `!gfpflags_allow_blocking(gfp)`, as `pcpu_alloc_noprof()` uses.
  - Safe: when neither result leads to a sleep that the mask does not
    allow: `ib_nl_make_request()` in `drivers/infiniband/core/sa_query.c`
    picks `GFP_ATOMIC` or `GFP_NOWAIT`, and
    `__page_pool_alloc_netmems_slow()` in `net/core/page_pool.c` only adds
    `__GFP_NOWARN`.
- **Potentially unsafe usage**: `gfp == GFP_KERNEL`.
  - Unsafe: when callers may add modifier bits and a false result picks the
    path that must not be taken.
  - Safe: when a false result only skips an optional step, as in
    `bpf_mem_cache_alloc_flags()`, which skips its `__alloc()` fallback.

**kswapd wakeup locks**

- `fill_pool()` in `lib/debugobjects.c`: starts from
  `__GFP_HIGH | __GFP_NOWARN` and adds `__GFP_KSWAPD_RECLAIM` when
  `preemptible() || system_state < SYSTEM_SCHEDULING`.
- `fill_pool()` without the bit: only in non-preemptible context once
  `system_state` has reached `SYSTEM_SCHEDULING`, where the caller may hold
  locks.
- `callback_lock` in `kernel/cgroup/cpuset.c`: `wakeup_kswapd()` can take it
  through `cpuset_zone_allowed()`, before any waitqueue test.
- `callback_lock` is reached only with cpusets enabled, `in_interrupt()`
  false, without `__GFP_HARDWALL`, on cpuset v1, for a node outside
  `current->mems_allowed`; see `cpuset_current_node_allowed()`.
- `wakeup_kswapd()` calls `wakeup_kcompactd()` only when the mask lacks
  `__GFP_DIRECT_RECLAIM`, in the branch for a hopeless node or a balanced
  node with no boosted watermark; `wakeup_kcompactd()` returns at once for
  order 0.
- Fast path: `rmqueue()` calls `wakeup_kswapd()` when `ALLOC_KSWAPD` is set
  and the zone has `ZONE_BOOSTED_WATERMARK`; `alloc_flags_nofragment()` sets
  `ALLOC_KSWAPD` from the mask.
- `gfp_nested_mask()`: keeps `__GFP_KSWAPD_RECLAIM` if the caller had it
  (both `GFP_KERNEL` and `GFP_ATOMIC` contain it) and never adds it.
- `gfp_nested_mask()` users do not strip the bit for the caller:
  `stack_depot_save_flags()` and `add_stack_record_to_list()` skip the
  allocation when `gfpflags_allow_spinning()` is false.
- Masks with neither reclaim bit, for example: `gfp_nolock` in
  `mm/page_alloc.c`, and the `__GFP_NOWARN` that `__reset_page_owner()`
  passes.

**Wrappers that change a mask**

- `kmalloc_gfp_adjust()`: in `mm/slub.c`, not `mm/util.c`.
- `kmalloc_gfp_adjust()` keeps `__GFP_KSWAPD_RECLAIM`, so without
  `__GFP_RETRY_MAYFAIL` the slab attempt of a large `kvmalloc()` cannot sleep
  but can still wake kswapd.
- `kmalloc_gfp_adjust()` callers: `__kvmalloc_node_noprof()` and
  `kvrealloc_node_align_noprof()`.
- `mempool_adjust_gfp()`: in `mm/mempool.c`; it takes a pointer to the mask.
  - Through the pointer: adds
    `__GFP_NOMEMALLOC | __GFP_NORETRY | __GFP_NOWARN` for every pass.
  - Return value: that mask without `__GFP_DIRECT_RECLAIM | __GFP_IO`, used
    for the first pass only.
- `vmalloc_gfp_adjust()` in `mm/vmalloc.c`: adds `__GFP_NOWARN`, and clears
  `__GFP_NOFAIL` for a high-order attempt.
- `vm_area_alloc_pages()`: also clears `__GFP_DIRECT_RECLAIM` for its
  large-order attempt.
- `pcpu_alloc_noprof()`: passes to its backing allocators only
  `gfp & (GFP_NOIO | __GFP_NORETRY | __GFP_NOWARN)`, after
  `current_gfp_context()`; `__GFP_NOFAIL` is dropped.
- There is no limit_gfp_mask() here; `thp_shmem_limit_gfp_mask()` in
  `include/linux/huge_mm.h` does that job for `mm/shmem.c`.
- There are no __GFP_NOFS or __GFP_NOIO bits; the restriction is the absence
  of `__GFP_FS` or `__GFP_IO`, so a wrapper keeps it by not setting them.
- **Potentially unsafe usage**: clearing `__GFP_NOFAIL` from the caller's
  mask.
  - Unsafe: when the attempt without the bit is the last one and its failure
    is returned to the caller; a `__GFP_NOFAIL` caller does not test for
    NULL.
  - Safe: `allocate_slab()` retries at the minimum order with the unmodified
    `flags`.
  - Safe: `__kvmalloc_node_noprof()` passes the unmodified `flags` to
    `__vmalloc_node_range_noprof()` for a size up to `INT_MAX`; for size up
    to `PAGE_SIZE` the bit is never cleared.
  - Safe: when the allocation is optional and the caller's request succeeds
    without it, as `alloc_slab_obj_exts()` with `OBJCGS_CLEAR_MASK`;
    `__memcg_slab_post_alloc_hook()` then returns the object uncharged.

**Zeroing pages for user space**

- `user_alloc_needs_zeroing()`: true when `cpu_dcache_is_aliasing()` or
  `cpu_icache_is_aliasing()`, even with init-on-alloc enabled; otherwise
  true only when `init_on_alloc` is off.
- Generic `vma_alloc_zeroed_movable_folio()` in `include/linux/highmem.h`:
  allocates without `__GFP_ZERO` and calls `clear_user_highpage()` only when
  `user_alloc_needs_zeroing()` is true.
- Architecture overrides of `vma_alloc_zeroed_movable_folio()` pass
  `__GFP_ZERO` instead; search `arch/` for the name.
- `__GFP_ZERO` for user-mapped memory also appears in generic code, for
  example `alloc_huge_zero_folio()` in `mm/huge_memory.c`.
- `folio_zero_user()`: clears up to three contiguous ranges through
  `clear_contig_highpages()`; the last range is the faulting page plus up to
  `FOLIO_ZERO_LOCALITY_RADIUS` pages on each side.
- `folio_zero_user()`: `clear_contig_highpages()` calls `might_sleep()`, so it
  needs a context that may sleep.
- `folio_zero_user()` rescheduling: on a preemptible model one range is one
  unit with no `cond_resched()` inside it.
- **Unsafe usage**: skipping the zeroing because
  `user_alloc_needs_zeroing()` is false, for a folio that did not just come
  from the page allocator; the function tests only the `init_on_alloc` key
  and cache aliasing.
  - Safe: a folio fresh from `vma_alloc_folio()`, as in `alloc_anon_folio()`
    and `vma_alloc_anon_folio_pmd()`.
  - Safe: zero unconditionally for a folio from a pool, as
    `hugetlb_no_page()`, `hugetlbfs_fallocate()` and `memfd_alloc_folio()` do
    with `folio_zero_user()`.

**Serving from a private pool**

- `__kfence_alloc()` tests, in order: `size > PAGE_SIZE`;
  `flags & GFP_ZONEMASK`; `__GFP_THISNODE` with `num_online_nodes() > 1`;
  cache flags `SLAB_CACHE_DMA | SLAB_CACHE_DMA32`; cache flag
  `SLAB_SKIP_KFENCE`.
- `__kfence_alloc()` does not test `SLAB_NOLEAKTRACE`,
  `SLAB_TYPESAFE_BY_RCU`, or any object-extension GFP bit.
- `SLAB_SKIP_KFENCE`: returns `NULL` without counting
  `KFENCE_COUNTER_SKIP_INCOMPAT`; the earlier tests count it.
- KFENCE object after allocation: still passes through
  `slab_post_alloc_hook()`; there `is_kfence_address()` skips the
  `memset()`, and `__memcg_slab_post_alloc_hook()` returns the object
  uncharged when its slab has no extension vector.
- KFENCE zeroing: `kfence_guarded_alloc()` zeroes the object itself when
  `slab_want_init_on_alloc()` is true.
- `__alloc_contig_verify_gfp_mask()` clears silently, without rejecting or
  warning: `GFP_ZONEMASK`, `__GFP_RECLAIMABLE`, `__GFP_WRITE`,
  `__GFP_HARDWALL`, `__GFP_THISNODE`, `__GFP_MOVABLE`.
- `__alloc_contig_verify_gfp_mask()` then returns `-EINVAL` for any bit
  outside this set:
  - reclaim: `__GFP_IO`, `__GFP_FS`, `__GFP_RECLAIM`
  - action: `__GFP_COMP`, `__GFP_RETRY_MAYFAIL`, `__GFP_NOWARN`,
    `__GFP_ZERO`, `__GFP_ZEROTAGS`, `__GFP_SKIP_ZERO`, `__GFP_SKIP_KASAN`
- Rejected, for example: `__GFP_NOFAIL`, `__GFP_NORETRY`, `__GFP_HIGH`,
  `__GFP_MEMALLOC`, `__GFP_NOMEMALLOC`, `__GFP_ACCOUNT`.
- Second mask, for compaction and migration: the reclaim bits plus
  `__GFP_RETRY_MAYFAIL` and `__GFP_NOWARN` from the caller, with
  `__GFP_MOVABLE | __GFP_RETRY_MAYFAIL` always added.
- `alloc_contig_frozen_range_noprof()`: the only caller; it applies
  `current_gfp_context()` before the check.

**No-wait failure error code**

- `__filemap_get_folio_mpol()` with `FGP_NOWAIT`: returns `ERR_PTR(-EAGAIN)`
  when the allocation or `filemap_add_folio()` fails with `-ENOMEM`; no
  other error is rewritten.
- Mask rewrite: `gfp &= ~GFP_KERNEL; gfp |= GFP_NOWAIT`, so `__GFP_IO` and
  `__GFP_FS` are cleared as well; it happens only in the `FGP_CREAT` branch.
- Callers that pass the code up: `iomap_write_begin()` in
  `fs/iomap/buffered-io.c` and `prepare_one_folio()` in `fs/btrfs/file.c`
  return `PTR_ERR(folio)`.
- Callers that discard the code: those that use `FGP_NOWAIT` for an optional
  extra folio skip it on any `IS_ERR()` result, for example in
  `fs/squashfs/file.c`, `fs/ubifs/file.c`, `fs/nfs/dir.c`.
- `pagecache_get_page()` in `mm/folio-compat.c`: turns every error into
  `NULL`, so `grab_cache_page_nowait()` callers never see `-EAGAIN`.

## Page allocator layers and references

**Layers of the page allocator**

- Chain with `CONFIG_NUMA`: `alloc_pages_noprof()` ->
  `alloc_frozen_pages_noprof()` -> `alloc_pages_mpol()` ->
  `__alloc_frozen_pages_noprof()` -> `get_page_from_freelist()` -> `rmqueue()`.
- `alloc_pages_mpol()`: static in `mm/mempolicy.c`, returns a frozen page.
  There is no alloc_pages_mpol_noprof().
- Reference count: set with `set_page_refcounted()` by the wrapper that calls
  the frozen form, for example `alloc_pages_noprof()` (with `CONFIG_NUMA`),
  `folio_alloc_mpol_noprof()`, `__alloc_pages_noprof()`,
  `alloc_pages_nolock_noprof()`.
- Without `CONFIG_NUMA`: no policy layer. `alloc_pages_noprof()` is an inline in
  `include/linux/gfp.h` that calls `alloc_pages_node_noprof()`.
- `__alloc_frozen_pages_noprof()` and `__alloc_pages_noprof()`: take five
  arguments, the last is `alloc_flags`; both are declared in
  `mm/page_alloc.h`.
- `__alloc_pages_noprof()`: has no `EXPORT_SYMBOL()`. There is no
  __alloc_pages_node_noprof(); public entries that take a node are, for
  example, `alloc_pages_node_noprof()` and `__folio_alloc_noprof()`.
- `get_page_from_freelist()` and `rmqueue()`: static in `mm/page_alloc.c`; no
  caller outside that file can enter there.
- `alloc_pages_nolock_noprof()`: goes through
  `alloc_frozen_pages_nolock_noprof()` into `__alloc_frozen_pages_noprof()`
  with `ALLOC_NOLOCK`, not straight to `get_page_from_freelist()`.
- With `ALLOC_NOLOCK` still applied: `current_gfp_context()`,
  `prepare_alloc_pages()` (cpuset), the `__GFP_ACCOUNT` charge.
- With `ALLOC_NOLOCK` skipped: the memory policy, `should_fail_alloc_page()`,
  `alloc_flags_nofragment()`, `__alloc_pages_slowpath()`.

**Internal allocation flags**

- The flags are in `mm/page_alloc.h`. The trylock flag is `ALLOC_NOLOCK`; there
  is no ALLOC_TRYLOCK.
- There is no gfp_to_alloc_flags() or gfp_to_alloc_flags_cma() here.
  `alloc_flags_slowpath()`, `alloc_flags_nonblocking()` and `alloc_flags_cma()`
  in `mm/page_alloc.c` do those jobs.
- Entry point for caller flags: the fifth argument of
  `__alloc_frozen_pages_noprof()` and `__alloc_pages_noprof()`.
- Accepted there: only `ALLOC_NOLOCK` and `ALLOC_NO_CODETAG`. Any other bit:
  `WARN_ON()` and `NULL`.
- `ALLOC_DEFAULT`: 0; what every other caller passes.
- Caller flags are kept in `alloc_flags` of `struct alloc_context` and OR-ed
  into every slow-path recomputation, so they last the whole allocation.
- `ALLOC_NOLOCK`: passed only by `alloc_frozen_pages_nolock_noprof()`. Code
  outside mm/ selects it with `alloc_pages_nolock()`.
- `ALLOC_NO_CODETAG`: passed only by `__alloc_tag_add_early_pfn()` in
  `mm/alloc_tag.c`, which calls `clear_page_tag_ref()` before `__free_page()`.
  `alloc_tag_add_early_pfn()` tests it.

| Flag | Differs from the usual belief |
|---|---|
| `ALLOC_WMARK_LOW` | fast path only without `ALLOC_NOLOCK`; with it the fast path uses `ALLOC_WMARK_MIN` |
| `ALLOC_HIGHATOMIC` | needs `__GFP_HIGH`, order > 0, no `__GFP_DIRECT_RECLAIM`, no `__GFP_NOMEMALLOC`; set on the fast path too |
| `ALLOC_MIN_RESERVE` | `__GFP_HIGH`; or `rt_or_dl_task()` and `in_task()` when the request has `__GFP_DIRECT_RECLAIM`; or the `__GFP_NOFAIL` attempt at the `nopage` label |
| `ALLOC_NON_BLOCK` | not implied by `ALLOC_MIN_RESERVE`; only from `alloc_flags_nonblocking()` |
| `ALLOC_NOFRAGMENT` | also set whenever `defrag_mode` is on, by `alloc_flags_nofragment()` and `alloc_flags_slowpath()` |
| `ALLOC_KSWAPD` | fast path gets it from `alloc_flags_nofragment()`, so never with `ALLOC_NOLOCK` |
| `ALLOC_CPUSET` | forced on in `__alloc_pages_may_oom()` and the first try of `__alloc_pages_cpuset_fallback()` |

- `get_page_from_freelist()`: drops `ALLOC_NOFRAGMENT` and retries only when
  `defrag_mode` is off. With `defrag_mode`, `__alloc_pages_slowpath()` drops it.
- `__GFP_HIGH` and `__GFP_KSWAPD_RECLAIM`: tested explicitly; nothing asserts
  that their values equal `ALLOC_MIN_RESERVE` and `ALLOC_KSWAPD`.
- With `ALLOC_NOLOCK`, `__alloc_frozen_pages_noprof()` also: requires
  `pcp_allowed_order()`, returns `NULL` when `alloc_nolock_allowed()` is false,
  ORs in `gfp_nolock`, and has a `VM_WARN_ON_ONCE()` for any gfp bit other
  than `__GFP_ACCOUNT` and the `gfp_nolock` bits.

**Frozen page allocators**

- Buddy frozen allocators: declared in `mm/page_alloc.h`, not in
  `mm/internal.h`. `__alloc_frozen_pages_noprof()` takes five arguments.
- Nolock pair: `alloc_frozen_pages_nolock_noprof()` and
  `free_frozen_pages_nolock()`, same header.
- Frozen contiguous allocators exist and are public, in `include/linux/gfp.h`:
  `alloc_contig_frozen_range_noprof()`, `alloc_contig_frozen_pages_noprof()`,
  `free_contig_frozen_range()`.
- Frozen CMA: `cma_alloc_frozen()`, `cma_alloc_frozen_compound()`,
  `cma_release_frozen()` in `include/linux/cma.h`.

| Allocator | Count | Compound |
|---|---|---|
| `alloc_contig_range_noprof()`, `alloc_contig_pages_noprof()` | 1 on every page | never; `__GFP_COMP` is rejected with `WARN_ON()` |
| `alloc_contig_frozen_range_noprof()`, `alloc_contig_frozen_pages_noprof()` without `__GFP_COMP` | 0 on every page | no |
| the same with `__GFP_COMP` | 0 | one compound page |
| `cma_alloc()` | 1 on every page | no |
| `cma_alloc_frozen_compound()` | 0 | yes |

- Frozen range with `__GFP_COMP`: the range must be a power of two and match
  the isolated range exactly, else `-EINVAL`; the order may exceed
  `MAX_PAGE_ORDER` up to `MAX_FOLIO_ORDER`.
- `free_contig_range()`: warns and frees nothing when given a compound head.
- `free_contig_frozen_range()`: frees both kinds; a compound frozen page may
  also go straight to `free_frozen_pages()`.
- There is no folio_alloc_gigantic(); hugetlb uses
  `alloc_gigantic_frozen_folio()` in `mm/hugetlb.c`.

**Using frozen pages**

- `set_page_refcounted()`: stores with `set_page_count()`, a plain
  `atomic_set()`, with no ordering. `folio_ref_unfreeze()` uses
  `atomic_set_release()`.
- `set_page_refcounted()` checks (not a tail, count is zero): `VM_BUG_ON_PAGE()`
  only, so absent without `CONFIG_DEBUG_VM`.
- `put_page_testzero()` on a zero count: `VM_BUG_ON_PAGE()` only; without
  `CONFIG_DEBUG_VM` the count goes negative and the call returns false, so
  the caller does not free the page.
- `set_pages_refcounted()` in `mm/internal.h`: gives every page of a
  non-compound range a count of 1; used by `alloc_contig_range_noprof()`,
  `alloc_contig_pages_noprof()`, `cma_alloc()`.
- **Unsafe usage**: `free_frozen_pages()` on a page whose count is not zero.
  - Unsafe: `free_page_is_bad()` checks the count only when
    `check_pages_enabled` is on; otherwise the page reaches a free list still
    referenced.
  - Safe: drop the last reference yourself first, as `page_frag_free()` and
    `___free_pages()` do with `put_page_testzero()`.
  - Safe: page never left the frozen state, as in `__free_slab()` and
    `free_large_kmalloc()` in `mm/slub.c`.
- **Unsafe usage**: `free_frozen_pages()` on a compound page with an order
  other than `compound_order()`.
  - Safe: pass `compound_order()` or `folio_order()`, as `__folio_put()` does;
    `__free_pages_prepare()` asserts it with `VM_BUG_ON_PAGE()`.
- Frozen to refcounted, beyond the allocator wrappers, for example:
  `mark_allocated_noprof()` and `compaction_alloc_noprof()` in
  `mm/compaction.c` (after `post_alloc_hook()`), `split_page()` for the tails,
  `dequeue_hugetlb_folio_node_exact()` with `folio_ref_unfreeze()`.
- Refcounted to frozen, for example: `compaction_free()`
  (`folio_put_testzero()` then `free_pages_prepare()`), `cma_release()`,
  `__free_contig_range()`.
- Stays frozen for life: slab (`alloc_slab_page()`), large kmalloc
  (`___kmalloc_large_node()`).
- Hugetlb folios: not frozen for life. They are allocated frozen
  (`alloc_buddy_frozen_folio()`, `alloc_gigantic_frozen_folio()`), stay
  frozen while free in the pool, get a count of 1 from
  `folio_ref_unfreeze()` when handed out, for example on dequeue, and are at
  count zero again when `__update_and_free_hugetlb_folio()` frees them.

**Freeing pages**

- Chain: `__free_pages()` -> `___free_pages()` -> `__free_frozen_pages()` ->
  `__free_pages_prepare()` -> `free_frozen_page_commit()` (per-CPU list) or
  `free_one_page()` -> `split_large_buddy()` -> `__free_one_page()`.
- `__folio_put()`: in `mm/folio.c`; there is no mm/swap.c.
- There is no FPI_TRYLOCK and no free_unref_page_commit(); the names are
  `FPI_NOLOCK` and `free_frozen_page_commit()`.
- `free_pages_prepare()`: a wrapper for `__free_pages_prepare()` with
  `FPI_NONE`; `compaction_free()` calls it from outside `mm/page_alloc.c`.
- `FPI_PREPARED`: `__free_pages_prepare()` returns true at once; used by
  `free_prepared_contig_range()` after each order-0 page was prepared.
- `___free_pages()`, count not reaching zero on a non-compound page: frees the
  tail chunks through `__free_frozen_pages()`, so they can go to a per-CPU
  list.

| Entry point | Reference |
|---|---|
| `free_pages_nolock()` | drops one |
| `free_pages_bulk()`, `__free_contig_range()`, `free_contig_range()` | drop one on every order-0 page |
| `cma_release()` | drops one on every page |
| `free_frozen_pages_nolock()` | expects zero |
| `free_contig_frozen_range()`, `cma_release_frozen()` | expect zero |
| `free_reserved_pages()` | sets every count to zero itself |

- With `FPI_NOLOCK` and `can_spin_trylock()` false: the page goes on neither
  list; `add_page_to_zone_llist()` puts it on `zone->trylock_free_pages`.
- With `FPI_NOLOCK` and a failed pcp trylock: `free_one_page()` trylocks
  `zone->lock`, and on failure also uses `zone->trylock_free_pages`.
- With `FPI_NOLOCK`, `free_frozen_page_commit()`: queues the page and returns
  before the `pcp->high` check, so no drain to the buddy lists, and
  `pcp->count` may exceed `high`.
- `free_unref_folios()`: an order that fails `pcp_allowed_order()` goes to
  `free_one_page()` directly, not through `__free_pages_ok()`.
- Order-0 page with `PageHWPoison()`: `__free_pages_prepare()` returns false;
  the page reaches no list.

**Pages off the direct map**

- The page allocator does not restore a direct-map entry.
  `debug_pagealloc_map_pages()` in `post_alloc_hook()` maps only when
  debug_pagealloc is enabled.
- No TLB flush follows the restore: neither `secretmem_free_folio()` nor the
  `secretmem_fault()` error path calls `flush_tlb_kernel_range()` after
  `set_direct_map_default_noflush()`.
- `secretmem_free_folio()` ignores the return value of
  `set_direct_map_default_noflush()`.
- `set_direct_map_valid_noflush()`: a third form, taking a page count and a
  bool; `execmem_set_direct_map_valid()` in `mm/execmem.c` uses it.
- Without `CONFIG_ARCH_HAS_SET_DIRECT_MAP`: all three are stubs in
  `include/linux/set_memory.h` that return 0.
- **Unsafe usage**: dropping the last reference to a page whose direct-map
  entry is still invalid.
  - Unsafe: `__free_pages_prepare()` can write the page through the direct
    map: `kernel_poison_pages()` when page poisoning is enabled,
    `clear_highpages_kasan_tagged()` when init-on-free is enabled.
  - Safe: restore in `.free_folio`; `filemap_free_folio()` in `mm/filemap.c`
    calls it before `folio_put_refs()`.
  - Safe: restore, then `folio_put()`, as the `filemap_add_folio()` failure
    path of `secretmem_fault()` does.
  - Safe: `folio_put()` with no restore when
    `set_direct_map_invalid_noflush()` itself returned an error, as
    `secretmem_fault()` does.
  - Safe: `execmem_cache_clean()` calls `execmem_set_direct_map_valid()` with
    true before `vfree()`.

**Static keys near the allocator**

- `static_key_slow_inc()` and `static_key_slow_dec()`: take `cpus_read_lock()`
  on every call, whatever the count. Only `jump_label_mutex` is skipped when
  the count is already above the threshold.
- `static_key_enable()` on an enabled key: takes `cpus_read_lock()`, returns
  before `jump_label_lock()`.
- `static_key_fast_inc_not_disabled()`: takes no lock.
- `__static_key_slow_dec_deferred()`: no lock while the count stays above one;
  otherwise the delayed work takes `cpus_read_lock()`.
- `static_branch_enable_cpuslocked()` and `static_key_enable_cpuslocked()`:
  still take `jump_label_mutex` unless the key is already enabled; on x86 the
  patching in `arch/x86/kernel/jump_label.c` also takes `text_mutex`.
- `lockdep_assert_cpus_held()`: returns without checking while
  `system_state < SYSTEM_RUNNING`.
- Without `CONFIG_JUMP_LABEL`: every operation is a plain atomic in
  `include/linux/jump_label.h`, no lock; the `_cpuslocked` names are aliases.
- Without `CONFIG_HOTPLUG_CPU`: `cpus_read_lock()` is empty.
- `cpus_read_lock()`: calls `might_sleep()` and is tracked by lockdep as a
  non-recursive read (`percpu_down_read_internal()`).
- **Unsafe usage**: a static key enable, disable, inc or dec, in the plain or
  the `_cpuslocked` form, on a path that a page allocation or reclaim can
  reach.
  - Unsafe: `jump_label_module_notify()` holds `cpus_read_lock()` and
    `jump_label_mutex` across `kzalloc_obj()` with `GFP_KERNEL`; an operation
    reached from that allocation takes `jump_label_mutex` again.
  - Unsafe: allocator callers may be atomic; the operation sleeps.
  - Safe: test plain state, as `cond_accept_memory()` does with
    `list_empty()` on `zone->unaccepted_pages`.
  - Safe: defer to a work item, as `toggle_allocation_gate()` in
    `mm/kfence/core.c` and `net_enable_timestamp()` in `net/core/dev.c` do.
- **Potentially unsafe usage**: `static_branch_enable()` or another
  non-`_cpuslocked` form.
  - Unsafe: when the caller already holds `cpus_read_lock()`, for example
    under `mem_hotplug_begin()` or in a CPU hotplug callback.
  - Safe: caller holds no hotplug lock and can sleep, as `netstamp_clear()`.
  - Safe: caller holds `cpus_read_lock()` and uses the `_cpuslocked` form, as
    `lru_gen_change_state()` in `mm/vmscan.c` does, and as
    `cpuset_css_online()` does through `cpuset_inc()`.
- **Unsafe usage**: a non-`_cpuslocked` static key operation while holding
  `pcp_batch_high_lock`, that is between `zone_pcp_disable()` and
  `zone_pcp_enable()`.
  - Unsafe: `page_alloc_cpu_online()` takes `pcp_batch_high_lock` in
    `zone_pcp_update()` with `cpus_write_lock()` held by `_cpu_up()`.
  - Safe: the `_cpuslocked` form, with `cpus_read_lock()` taken before
    `zone_pcp_disable()`; `memory_block_offline()` takes it with
    `mem_hotplug_begin()` before `offline_pages()`.

## Free lists and pageblocks

**Per-CPU page lists**

- THP order: `pcp_allowed_order()` admits `HPAGE_PMD_ORDER` (through
  `is_pmd_order()`), not `pageblock_order`, and only under
  `CONFIG_TRANSPARENT_HUGEPAGE`.
- THP lists: `NR_PCP_THP` is 2 under `CONFIG_TRANSPARENT_HUGEPAGE`.
  `order_to_pindex()` gives movable its own list; unmovable and reclaimable
  share the other.
- `MIGRATE_HIGHATOMIC` and `MIGRATE_CMA` pages: freed onto the
  `MIGRATE_MOVABLE` per-CPU list by `__free_frozen_pages()` and
  `free_unref_folios()`. Of the migrate types, only `MIGRATE_ISOLATE`
  bypasses the lists, through `free_one_page()`.
- `rmqueue()`: tests only `pcp_allowed_order()` before `rmqueue_pcplist()`;
  it has no `ALLOC_CMA` test.
- Type on drain: `free_pcppages_bulk()` ignores which list a page sat on and
  re-reads `get_pfnblock_migratetype()` per page under `zone->lock`.
- `free_frozen_page_commit()` drain: frees `nr_pcp_free()` pages in chunks of
  `batch`, and drops and re-trylocks the list lock between chunks.
- `free_frozen_page_commit()` return value: false means the lock is no longer
  held (retry failed or task changed CPU).
- `ALLOC_HIGHATOMIC` on an empty list: `__rmqueue_pcplist()` returns NULL
  without refilling, so the request goes to `rmqueue_buddy()`.
- `zone_pcp_disable()`: sets `high_min` and `high_max` to 0 and `batch` to 1,
  then drains every online CPU. `nr_pcp_high()` then returns 0, so each
  `free_frozen_page_commit()` without `FPI_NOLOCK` drains.

**Locking a per-CPU list**

- There is no pcp_trylock_prepare(), pcp_trylock_finish() or
  pcp_spin_lock_maybe_irqsave() here. `pcp_spin_trylock(ptr)` takes one
  argument and no flags.

| Wrapper | `CONFIG_SMP` | `!CONFIG_SMP` |
|---|---|---|
| `pcp_spin_trylock()` | `pcpu_task_pin()`, `this_cpu_ptr()`, `spin_trylock()`; unpins and gives NULL on failure | always `NULL` |
| `pcp_spin_unlock()` | `spin_unlock()`, `pcpu_task_unpin()` | `BUG_ON(1)` |
| `pcp_spin_lock_nopin()` | `spin_lock(&(ptr)->lock)` only | same |
| `pcp_spin_unlock_nopin()` | `spin_unlock(&(ptr)->lock)` only | same |

- `pcpu_task_pin()`: `preempt_disable()` without `CONFIG_PREEMPT_RT`,
  `migrate_disable()` with it.
- Uniprocessor: no wrapper disables IRQs. Every allocation takes
  `rmqueue_buddy()` and every free takes `free_one_page()`, except that
  `__free_frozen_pages()` with `FPI_NOLOCK` and `can_spin_trylock()` false
  calls `add_page_to_zone_llist()` directly.
- Uniprocessor lists stay empty: the only code that adds a page,
  `free_frozen_page_commit()` and `rmqueue_bulk()` from
  `__rmqueue_pcplist()`, runs after a successful `pcp_spin_trylock()`.
- `pcp_spin_lock_nopin()` callers hold the pcp pointer of one given CPU,
  which may be a remote one: `__drain_all_pages()` calls
  `drain_pages_zone()` for each CPU in its mask from the calling CPU.
- Pairing: `pcp_spin_unlock()` also unpins, so it pairs only with
  `pcp_spin_trylock()`; `pcp_spin_unlock_nopin()` pairs only with
  `pcp_spin_lock_nopin()`.
- Lock order: `zone->lock` nests inside the pcp lock, taken irqsave, in
  `rmqueue_bulk()` and `free_pcppages_bulk()`.
- **Potentially unsafe usage**: taking the lock with
  `pcp_spin_lock_nopin()`.
  - Unsafe: from hard or soft IRQ context. `pcp_spin_trylock()` holders keep
    IRQs enabled, so the spin can interrupt the holder on the same CPU and
    never finish.
  - Safe: from task context, as `drain_pages_zone()` and `decay_pcp_high()`
    do; an IRQ that arrives meanwhile uses `pcp_spin_trylock()`, fails, and
    falls back to the buddy lists.
- **Unsafe usage**: calling `pcp_spin_unlock()` after
  `free_frozen_page_commit()` returned false.
  - Safe: test the return value and treat the lock as gone, as
    `__free_frozen_pages()` does; `free_unref_folios()` also resets its
    `pcp` and `locked_zone`.

**Pageblock flags**

- Isolation: the standalone bit `PB_migrate_isolate`, present only under
  `CONFIG_MEMORY_ISOLATION`. `PB_migrate_0` to `PB_migrate_2` keep the
  block's own type while it is isolated.
- `get_pfnblock_migratetype()` on an isolated block: returns
  `MIGRATE_ISOLATE`. Read the stored type with `__get_pfnblock_flags_mask()`
  and `PAGEBLOCK_MIGRATETYPE_MASK`, as `__move_freepages_block_isolate()`
  does.
- Names not in this tree: PB_migrate_end, PB_migrate_skip,
  PB_migratetype_bits, MIGRATETYPE_MASK, MIGRATETYPE_AND_ISO_MASK. The masks
  are `PAGEBLOCK_MIGRATETYPE_MASK` and `PAGEBLOCK_ISO_MASK`; the compaction
  bit is `PB_compact_skip`.
- Linkage: `set_pageblock_migratetype()`, `change_pageblock_range()`,
  `move_freepages_block()` and `__move_freepages_block()` are static in
  `mm/page_alloc.c`.
- Not static, for callers outside `mm/page_alloc.c`:
  `init_pageblock_migratetype()` (takes an `isolate` argument),
  `pageblock_isolate_and_move_free_pages()` and
  `pageblock_unisolate_and_move_free_pages()`.
- `set_pageblock_migratetype()` given `MIGRATE_ISOLATE`: returns without
  writing; only the warning depends on `CONFIG_DEBUG_VM`.
- `set_pageblock_migratetype()` on an isolated block: clears
  `PB_migrate_isolate`, because it writes with `PAGEBLOCK_ISO_MASK` in the
  mask. The warning is `VM_WARN_ONCE()`, so `CONFIG_DEBUG_VM` only.
- Page spanning several blocks: `change_pageblock_range()`. It assumes
  `start_order >= pageblock_order` and moves no free pages.
- `__move_freepages_block()`: moves the free pages only; the caller writes
  the type.
- `move_freepages_block()`: moves and writes the type; returns -1 and changes
  nothing when the block straddles a zone boundary.
- `pageblock_isolate_and_move_free_pages()`: when the block is part of a
  free page above `pageblock_order`, it splits that page with
  `split_large_buddy()` instead of moving list entries.
- **Unsafe usage**: writing a block's new type while its free pages are
  still on the old type's list.
  - Safe: move first, then write, as `move_freepages_block()` does;
    `move_to_free_list()` checks, with `VM_WARN_ONCE()`, that the block
    still has the old type.
  - Safe: for one page, delete it with the old type, write the type, add
    with the new type, as `try_to_claim_block()` does;
    `__del_page_from_free_list()` and `__add_to_free_list()` check each
    side with `VM_WARN_ONCE()`.
- **Potentially unsafe usage**: `change_pageblock_range()` with no move of
  free pages.
  - Unsafe: when the block holds other free pages; they stay on the old
    list.
  - Safe: when the page covers each block whole and is off the free lists:
    the allocated page in `reserve_highatomic_pageblock()`, or the buddy
    just deleted in `__free_one_page()`.

**Migrate type fallback**

- There is no __rmqueue_fallback() and no move_freepages_block_isolate()
  here. `__rmqueue()` calls `__rmqueue_claim()`, then `__rmqueue_steal()`.
- `find_suitable_fallback()`: returns `enum fallback_result`
  (`FALLBACK_FOUND`, `FALLBACK_EMPTY`, `FALLBACK_NOCLAIM`, in
  `mm/page_alloc.h`), not a type. The type comes back through `mt_out`,
  which may be NULL.
- `should_try_claim_block()`: receives the order of the candidate free page,
  not the order requested.
- `FALLBACK_NOCLAIM`: ends the downward scan in `__rmqueue_claim()`.
- Movable requests: a claim is tried only when the candidate page is at
  least `pageblock_order / 2` or `page_group_by_mobility_disabled` is set;
  smaller candidates are left to `__rmqueue_steal()`.
- `try_to_claim_block()` returning NULL (too few free or alike pages, or the
  block straddles a zone): `__rmqueue_claim()` tries the next lower order.
- `__rmqueue_steal()`: runs only after the whole claim scan found nothing,
  and only without `ALLOC_NOFRAGMENT`. In the `rmqueue_bulk()` loop, a
  `*mode` of `RMQUEUE_STEAL` makes later calls skip the scan.
- `ALLOC_NOFRAGMENT`: 0 without `CONFIG_ZONE_DMA32`, so there the raised
  `min_order` in `__rmqueue_claim()` and the steal skip never apply.
- Steal remainder: `page_del_and_expand()` gets `fallback_mt`, so the split
  remainder returns to the lists of the block's own type.
- Claim of a page >= `pageblock_order`: `del_page_from_free_list()` with
  `block_type`, then `change_pageblock_range()`, then `expand()` with
  `start_type`. A change must keep that order; see "Pageblock flags".
- Claim of a smaller page: `__move_freepages_block()`, then
  `set_pageblock_migratetype()`, then `__rmqueue_smallest()` on the new type,
  so the page returned need not be the candidate.

**Movable allocations**

- `gfp_migratetype()`: defined in `mm/page_alloc.h`, which undefines
  `GFP_MOVABLE_MASK` and `GFP_MOVABLE_SHIFT` right after it.
- Both bits set: `VM_WARN_ON()` (not once, `CONFIG_DEBUG_VM` only) runs
  before the `page_group_by_mobility_disabled` test, so it fires either way.
- Both bits set, value: 3, which a `BUILD_BUG_ON()` ties to
  `MIGRATE_HIGHATOMIC`; with `page_group_by_mobility_disabled` the result
  is `MIGRATE_UNMOVABLE`.
- Both bits set, value 3 afterwards: `prepare_alloc_pages()` stores the
  value untested. `order_to_pindex()` then returns the index of another
  list; for order 0 that is the order-1 `MIGRATE_UNMOVABLE` list.
- There is no gfp_to_alloc_flags_cma() here; `alloc_flags_cma()` in
  `mm/page_alloc.c` sets `ALLOC_CMA` for `MIGRATE_MOVABLE`, under
  `CONFIG_CMA`.
- Names not defined in this tree: MIGRATEPAGE_SUCCESS,
  __SetPageMovableOps(), __SetPageMovable(), __ClearPageMovable(),
  mm/balloon_compaction.c.
- Registration: `set_movable_ops()` in `mm/migrate.c`, one ops pointer per
  page type, with no locking against concurrent callers.
- `set_movable_ops()` types: only `PGTY_offline` and `PGTY_zsmalloc`; any
  other type gives -EINVAL. A new user must also extend `page_movable_ops()`
  and `page_has_movable_ops()`.
- `set_movable_ops()` results: -EBUSY when ops are already set, -ENOSYS
  without `CONFIG_MIGRATION`; NULL ops unregisters.
- Balloon drivers register nothing: `mm/balloon.c` registers `balloon_mops`
  under `CONFIG_BALLOON_MIGRATION`, and a driver supplies `migratepage` in
  `struct balloon_dev_info`.
- `balloon_page_alloc()`: uses `GFP_HIGHUSER_MOVABLE` only under
  `CONFIG_BALLOON_MIGRATION`, else `GFP_HIGHUSER`.
- Marking a page: `SetPageMovableOps()` plus the page type;
  `page_has_movable_ops()` needs both.
- `PG_movable_ops`: has no clear helper, and stays set until the page is
  freed; `migrate_page()` does not clear it.
- Flag aliases: `PG_movable_ops` is `PG_uptodate` and
  `PG_movable_ops_isolated` is `PG_reclaim`.
- `PG_movable_ops_isolated`: owned by the core. `isolate_movable_ops_page()`
  warns, under `CONFIG_DEBUG_VM`, if `isolate_page()` set it.
- `migrate_page()`: success is 0; only then does
  `migrate_movable_ops_page()` clear the isolated flag.
- `isolate_page()`: may be handed a page its owner already released, and
  must then return false, as `balloon_page_isolate()` and
  `zs_page_isolate()` do.
- After `set_movable_ops(NULL, type)`: `page_movable_ops()` returns NULL.
  Only `isolate_movable_ops_page()` checks for that;
  `putback_movable_ops_page()` and `migrate_movable_ops_page()` call
  through it.

## The slow path and failure

**Slow path steps**

- Fast path: in `__alloc_frozen_pages_noprof()` in `mm/page_alloc.c`;
  `__alloc_pages_noprof()` only wraps it and sets the refcount.
- Slow path flags: there is no gfp_to_alloc_flags() and no ALLOC_HARDER here;
  `alloc_flags_slowpath()` starts from `ALLOC_WMARK_MIN | ALLOC_CPUSET` and
  the result is ORed with `ac->alloc_flags`.
- Early compaction: there is no compaction block before the `retry` label;
  `compact_first`, while set, makes a pass of the loop skip
  `__alloc_pages_direct_reclaim()`.
- One pass from `retry`, in order:
  1. `wake_all_kswapds()` if `ALLOC_KSWAPD`.
  2. `get_page_from_freelist()` with the current `alloc_flags`.
  3. `__gfp_pfmemalloc_flags()`; with reserve flags, or without
     `ALLOC_CPUSET`, `ac->nodemask` is dropped and the first such pass jumps
     back to `retry`, so steps 1 and 2 repeat with the new flags and no
     nodemask.
  4. `goto nopage` without `__GFP_DIRECT_RECLAIM` (under `defrag_mode`, after
     one retry without `ALLOC_NOFRAGMENT`) or under `PF_MEMALLOC`.
  5. `__alloc_pages_direct_reclaim()`, unless `compact_first`.
  6. `__alloc_pages_direct_compact()` at `compact_priority`.
  7. With `compact_first`: clear it and `goto retry`, so the next pass does
     reclaim, then compaction.
  8. `__GFP_NORETRY` and costly-order exits, retry decisions,
     `__alloc_pages_may_oom()`.
- Reserves versus first compaction: the reserves attempt (step 3) comes before
  the first compaction, and a `PF_MEMALLOC` task or a request without direct
  reclaim never compacts.
- `compact_first` condition: `can_compact` and (`costly_order`, or
  `order > 0` with `ac->migratetype != MIGRATE_MOVABLE`); it does not call
  `gfp_pfmemalloc_allowed()`, so an OOM victim or `__GFP_MEMALLOC` request
  can compact first.
- `compact_first` pass failed, `__GFP_NORETRY` and `__GFP_THISNODE` both set:
  `goto nopage` with no direct reclaim, at any order; the code does not test
  `COMPACT_SKIPPED` or `COMPACT_DEFERRED` here.
- `compact_first` pass failed, `__GFP_NORETRY` alone: the next pass keeps
  `INIT_COMPACT_PRIORITY`; without `__GFP_NORETRY` it goes to
  `DEF_COMPACT_PRIORITY`.

**Requests that can fail**

- `ALLOC_NOLOCK` request (`alloc_frozen_pages_nolock_noprof()`): NULL after the
  single fast-path attempt; never enters the slow path.
- `order > MAX_PAGE_ORDER`: `alloc_order_allowed()` warns (not with
  `__GFP_NOWARN`) and `__alloc_frozen_pages_noprof()` returns NULL before the
  fast path, also with `__GFP_NOFAIL`.
- Non-costly order, direct reclaim, no modifier: retried without bound while
  `__alloc_pages_may_oom()` reports progress; it still returns NULL in the
  cases listed under "OOM killer exceptions".
- `__GFP_RETRY_MAYFAIL` at a costly order: has an effect in
  `__alloc_pages_slowpath()` only if `can_compact`, which needs
  `__GFP_DIRECT_RECLAIM`, `__GFP_IO` and `CONFIG_COMPACTION` (see
  `gfp_compaction_allowed()` in `include/linux/gfp.h`); otherwise the request
  fails after one pass as if the flag were absent.
- `__GFP_NORETRY` with `__GFP_RETRY_MAYFAIL`: `__GFP_NORETRY` is tested first
  and wins.
- `__GFP_NOFAIL` with `__GFP_NORETRY` or `__GFP_RETRY_MAYFAIL`: with
  `__GFP_DIRECT_RECLAIM` the request still loops without bound, because every
  `goto nopage` ends in the `nofail` branch.
- `__GFP_NOFAIL` and order: `mm/page_alloc.c` has no order test for
  `__GFP_NOFAIL` other than `alloc_order_allowed()`; an order above 1 gets no
  warning, and the "order > 1 is not supported" text in
  `include/linux/gfp_types.h` is not enforced by the page allocator.
- `__GFP_NOFAIL` at a costly order: loops through `nopage` and reaches
  `out_of_memory()` never; without `__GFP_RETRY_MAYFAIL` it exits to `nopage`
  before `__alloc_pages_may_oom()`, with it `__alloc_pages_may_oom()` skips.
- `__GFP_NOFAIL` warnings in `__alloc_pages_slowpath()`: exactly two
  `WARN_ON_ONCE()` at entry, for no `__GFP_DIRECT_RECLAIM` and for
  `PF_MEMALLOC`.
- `__GFP_NOFAIL` with `__GFP_DIRECT_RECLAIM` under `PF_MEMALLOC`: warns once,
  then loops between `retry` and `nopage` with no reclaim, trying only the
  freelist and the `ALLOC_MIN_RESERVE` fallback.
- `__GFP_NOFAIL` in `__alloc_pages_may_oom()`: gets the `ALLOC_NO_WATERMARKS`
  attempt on every call that reaches `out_of_memory()`, whatever it returns;
  `WARN_ON_ONCE_GFP()` fires only when `out_of_memory()` returned false.

**OOM killer exceptions**

- Skipped with `*did_some_progress = 0`, tested in this order after the
  `ALLOC_WMARK_HIGH` attempt: `PF_DUMPCORE`; order above
  `PAGE_ALLOC_COSTLY_ORDER`; `__GFP_RETRY_MAYFAIL` or `__GFP_THISNODE`;
  `ac->highest_zoneidx < ZONE_NORMAL`; `pm_suspended_storage()`.
- No `__GFP_FS`: `__alloc_pages_may_oom()` has no `__GFP_FS` test; it calls
  `out_of_memory()` in `mm/oom_kill.c`, which returns true without killing
  for a non-memcg request, so progress is 1 and the request loops.
- `__GFP_NOFAIL` in a skipped case: the skip tests jump to `out` before the
  `WARN_ON_ONCE_GFP()` branch, so the request gets progress 0 and no
  `ALLOC_NO_WATERMARKS` attempt; it loops through `nopage` with
  `ALLOC_MIN_RESERVE` only.
- Next step in `__alloc_pages_slowpath()`, in order:
  1. A page was returned: `got_pg`.
  2. `tsk_is_oom_victim(current)` with `ALLOC_OOM` in `alloc_flags` or
     `__GFP_NOMEMALLOC` in the mask: `goto nopage`, even with progress 1.
  3. Progress 1: `no_progress_loops = 0`, `goto retry`.
  4. Progress 0: falls into `nopage`.

**Slow path backward jumps**

| Jump | Bound |
|---|---|
| `retry` after dropping `ac->nodemask` or gaining reserves | once per call; `can_retry_reserves` |
| `retry` without direct reclaim, `defrag_mode`, `__GFP_KSWAPD_RECLAIM` | once per `restart`; clears `ALLOC_NOFRAGMENT` |
| `retry` after the `compact_first` pass | once per `restart`; clears `compact_first` |
| `retry` from `should_reclaim_retry()` | `no_progress_loops` over `MAX_RECLAIM_RETRIES`; reset on progress at a non-costly order |
| `retry` from `should_compact_retry()` | `compaction_retries`, `compact_priority`; see below |
| `retry` under `defrag_mode` after both declined | once per `restart`; clears `ALLOC_NOFRAGMENT` |
| `retry` after `__alloc_pages_may_oom()` progress | none |
| `retry` for `__GFP_NOFAIL` at `nopage` | none |
| `restart` from any of the three check sites | no counter |

- `ALLOC_NOFRAGMENT` without `CONFIG_ZONE_DMA32`: defined as 0 in
  `mm/page_alloc.h`, so neither `defrag_mode` jump is taken.
- `should_reclaim_retry()` past `MAX_RECLAIM_RETRIES`: still returns true if
  `unreserve_highatomic_pageblock()` with `force` released a block.
- `should_compact_retry()`: `compaction_retries` advances only on
  `COMPACT_SUCCESS`, with the limit `MAX_COMPACT_RETRIES` divided by 4 for a
  costly order.
- `should_compact_retry()` on `COMPACT_SKIPPED`: returns
  `compaction_zonelist_suitable()`, with no counter.
- `should_compact_retry()` priority floor: `MIN_COMPACT_COSTLY_PRIORITY` for
  a costly order, `MIN_COMPACT_PRIORITY` otherwise.
- `restart` from the nodemask branch of `check_retry_cpuset()`: at most once
  per call, since it sets `ac->nodemask` to NULL; the cookie branches need a
  new outside change after each `restart`.
- `restart` recomputes: both cookies, `compaction_retries`,
  `no_progress_loops`, `compact_result`, `compact_priority`, `compact_first`,
  `alloc_flags` from `alloc_flags_slowpath()`, and `ac->preferred_zoneref`.
- `restart` does not reset: `can_retry_reserves`, `alloc_start_time`, or an
  `ac->nodemask` already set to NULL.
- `retry` with reserve flags: `alloc_flags` is rebuilt from
  `alloc_flags_cma()`, the reserve flags, `ac->alloc_flags` and the
  `ALLOC_KSWAPD` bit only; `ALLOC_CPUSET`, `ALLOC_MIN_RESERVE` and
  `ALLOC_NOFRAGMENT` are lost until the next `restart`.
- `check_retry_cpuset()` detects two things, both only with
  `cpusets_enabled()`: `ac->nodemask` no longer intersecting the cpuset
  (`cpuset_nodemask_valid_mems_allowed()`), and a change of
  `current->mems_allowed_seq` since `read_mems_allowed_begin()`.
- `check_retry_zonelist()`: `read_seqretry()` on `zonelist_update_seq`, which
  `__build_all_zonelists()` writes; there is no zonelist_iter_retry() here.
- `check_retry_zonelist()` without `CONFIG_MEMORY_HOTREMOVE`: returns the
  cookie, which `zonelist_iter_begin()` set to 0, so it never restarts.

**Checks before a repeated retry**

- Three call sites, each `check_retry_cpuset() || check_retry_zonelist()`
  followed by `goto restart`:
  1. after the `__GFP_NORETRY` and costly-order exits, before
     `should_reclaim_retry()`;
  2. after the `defrag_mode` retry, before `__alloc_pages_may_oom()`;
  3. at the `nopage` label, before the `nofail` branch and `warn_alloc()`.

| Backward jump to `retry` | Sites passed before the jump |
|---|---|
| after dropping `ac->nodemask` or gaining reserves | none |
| without direct reclaim, under `defrag_mode` | none |
| after the `compact_first` pass | none |
| from `should_reclaim_retry()` | 1 |
| from `should_compact_retry()` | 1 |
| under `defrag_mode` after both declined | 1 |
| after `__alloc_pages_may_oom()` progress | 1 and 2 |
| for `__GFP_NOFAIL` | 3 |

- `goto fail` for `__GFP_NOFAIL` without direct reclaim: comes after site 3,
  so it too can restart instead of failing.
- **Potentially unsafe usage**: a `goto retry` placed above site 1.
  - Unsafe: when the jump can be taken more than once per `restart`; the loop
    then repeats without ever comparing the cpuset or zonelist cookie.
  - Safe: when a flag cleared before the jump limits it to one use, as
    `can_retry_reserves`, `compact_first` and the clearing of
    `ALLOC_NOFRAGMENT` do in `__alloc_pages_slowpath()`; the comment at
    site 1 states the requirement.

## Watermarks

**Watermark levels**

- `boost_watermark()` caller: only `try_to_claim_block()` in
  `mm/page_alloc.c`; there is no steal_suitable_fallback() in this tree.
- Trigger: a fallback claim from a free page smaller than `pageblock_order`.
  `try_to_claim_block()` returns before the boost for larger pages, and
  boosts before it knows whether the block will be claimed.
- `__rmqueue_steal()`: takes a single fallback page and never boosts.
- `boost_watermark()` returns `false` and leaves the boost alone when
  `watermark_boost_factor` is 0, when the zone has fewer than
  `4 * pageblock_nr_pages` managed pages, or when the cap computed from the
  stored `_watermark[WMARK_HIGH]` is 0.
- `boost_watermark()` at the cap: still returns `true`, so the flag below is
  set although the boost did not grow.
- `boost_watermark()` wakes nothing. `try_to_claim_block()` sets
  `ZONE_BOOSTED_WATERMARK` when it returned `true` and `ALLOC_KSWAPD` is set;
  `rmqueue()`, not `get_page_from_freelist()`, tests and clears the bit and
  calls `wakeup_kswapd()`.
- `wakeup_kswapd()`: wakes kswapd for a node that `pgdat_balanced()` accepts
  if `pgdat_watermark_boosted()` finds a boosted zone, unless
  `kswapd_test_hopeless()`.
- `zone->watermark_boost` has three writers: `boost_watermark()`,
  `balance_pgdat()` and `__setup_per_zone_wmarks()`.
- `balance_pgdat()` does not zero the boost: it subtracts the per-zone value
  it saved in `zone_boosts[]` on entry, so boosts added during the pass
  remain.
- `balance_pgdat()` subtracts at the end of every pass that began with a
  boost, also when boost reclaim was abandoned because the node was
  unbalanced or reclaim made no progress.
- Gap between levels in `__setup_per_zone_wmarks()`: the floor is a quarter of
  the zone's proportional share of `min_free_kbytes`, not of the stored min;
  the two differ for highmem and `ZONE_MOVABLE`, whose stored min is clamped.
- Direct reads of `_watermark[]` in `mm/page_alloc.c` are unboosted reads:
  the cap in `boost_watermark()`, the mark in `__isolate_free_page()`, and
  the retry in `zone_watermark_fast()`.

**The watermark test**

- Highatomic term: `__zone_watermark_unusable_free()` subtracts
  `z->nr_free_highatomic`, not `nr_reserved_highatomic`.
- Highatomic term is skipped when any bit of `ALLOC_RESERVES` is set, so also
  for `ALLOC_NON_BLOCK` alone.
- CMA term: `zone_page_state(z, NR_FREE_CMA_PAGES)` under `CONFIG_CMA` when
  `ALLOC_CMA` is clear; `struct zone` has no free-CMA field.
- `NR_UNACCEPTED`: not subtracted by the test. Unaccepted pages are counted in
  `NR_FREE_PAGES`; `cond_accept_memory()` subtracts them in its own
  calculation.
- There is no ALLOC_HIGH flag; `__GFP_HIGH` maps to `ALLOC_MIN_RESERVE`.
- Lowering steps, each applied to the already lowered value:

  | Flags set | Mark becomes about |
  |---|---|
  | `ALLOC_MIN_RESERVE` | 1/2 |
  | `ALLOC_MIN_RESERVE` and `ALLOC_NON_BLOCK` | 3/8 |
  | `ALLOC_OOM` | half of whatever the rows above left |
  | `ALLOC_NON_BLOCK` alone | unchanged |
  | `ALLOC_HIGHATOMIC` alone | unchanged |

- `ALLOC_NO_WATERMARKS`: `get_page_from_freelist()` still runs the test; the
  flag only overrides a failed result, after `cond_accept_memory()` and
  `_deferred_grow_zone()` have been tried.
- Without `CONFIG_MMU`, `ALLOC_OOM` is defined as `ALLOC_NO_WATERMARKS` in
  `mm/page_alloc.h`.
- Order above zero: a free area counts if any list below `MIGRATE_PCPTYPES`
  is non-empty, or `MIGRATE_CMA` with `ALLOC_CMA`, or `MIGRATE_HIGHATOMIC`
  with `ALLOC_HIGHATOMIC` or `ALLOC_OOM`.
- Order above zero: the request's own migratetype is not an input to the
  scan.

**The low-memory reserve**

- Empty upper zone `j`: its entry is not forced to 0; it repeats the entry
  for `j - 1`, because `setup_per_zone_lowmem_reserve()` divides a running
  sum.
- `lowmem_reserve[j]` is therefore non-decreasing in `j`;
  `calculate_totalreserve_pages()` relies on that and takes the first
  non-zero entry from the top.
- All entries of a zone are 0 when its ratio is 0 or the zone itself has no
  managed pages.
- The sum covers the zones above `i` on the same node only.
- Entries with `j <= i`, including index 0 of every zone, are never written.
- `highest_zoneidx` 0 gives a test with no reserve term; `__isolate_free_page()`
  and `mm/page_reporting.c` call `zone_watermark_ok()` that way.

**Per-CPU counter drift**

- There is no zone_watermark_ok_safe() in this tree. `pgdat_balanced()` in
  `mm/vmscan.c` open-codes the check and passes the count to
  `__zone_watermark_ok()`.
- `pgdat_balanced()` reads `NR_FREE_PAGES_BLOCKS` instead of `NR_FREE_PAGES`
  when `defrag_mode` is set and the order is non-zero, and compares it with
  the same `percpu_drift_mark`.
- Unconditional `zone_page_state_snapshot()` of `NR_FREE_PAGES`, with no look
  at `percpu_drift_mark`: `should_reclaim_retry()`, `allow_direct_reclaim()`
  and `compaction_zonelist_suitable()`.
- Cheap read: every caller of `zone_watermark_ok()` and
  `zone_watermark_fast()`, which includes reclaim-side tests such as
  `compaction_ready()`; `compaction_suitable()` also passes the cheap count,
  to `__zone_watermark_ok()`.
- `percpu_drift_mark` has one writer, `refresh_zone_stat_thresholds()`, with
  no else branch: when the drift fits in the low-min gap the field keeps its
  previous value.
- `set_pgdat_percpu_threshold()` skips zones whose `percpu_drift_mark` is 0,
  so kswapd's threshold switching in `kswapd_try_to_sleep()` only affects
  zones that have the mark set.
- `zone_page_state_snapshot()` is not exact: it sums the per-CPU deltas of
  online CPUs with no synchronisation.
- Without `CONFIG_SMP`: both reads are the same, and
  `refresh_zone_stat_thresholds()` is an empty stub in
  `include/linux/vmstat.h`, so `percpu_drift_mark` is never set.

**Watermarks early in boot**

- `CONFIG_DEFERRED_STRUCT_PAGE_INIT`: `page_alloc_init_late()` blocks until
  deferred init has finished, and `kernel_init_freeable()` calls it before
  `do_basic_setup()`, so `init_per_zone_wmark_min()` sees final zone sizes.
- Before `init_per_zone_wmark_min()` has run, `__zone_watermark_ok()` given a
  mark from an accessor returns true whenever the free count minus the
  unusable pages is above `lowmem_reserve[highest_zoneidx]`, plus the
  free-list scan for an order above zero.
- `lowmem_reserve[]` can be non-zero before `init_per_zone_wmark_min()`:
  `adjust_managed_page_count()` calls `setup_per_zone_lowmem_reserve()`, for
  example from `init_cma_reserved_pageblock()`.
- `cond_accept_memory()`: treats `promo_wmark_pages()` of 0 as "not
  initialised" and accepts one block with `try_to_accept_memory_one()`.
- **Unsafe usage**: computing a deficit from a watermark accessor in code
  that can run before `init_per_zone_wmark_min()`, without a test for 0; the
  deficit is never positive and the work is never done.
  - Safe: test the mark for 0 and take a fixed step, as
    `cond_accept_memory()` does.
  - Safe: test for 0 and do nothing, as `boost_watermark()` does.
  - Safe: a plain pass or fail test, as `zone_watermark_fast()` in
    `get_page_from_freelist()`; with a mark of 0 it passes while the usable
    free pages exceed `lowmem_reserve[highest_zoneidx]`.

## Any-context allocation

**Any-context page allocation**

- `alloc_frozen_pages_nolock_noprof()`: only maps `NUMA_NO_NODE` to
  `numa_node_id()` and calls the shared `__alloc_frozen_pages_noprof()` with
  `ALLOC_NOLOCK`; the nolock branches live in it and its callees.
- `gfp_nolock`: a `static const gfp_t` in `mm/page_alloc.c`, equal to
  `__GFP_NOWARN | __GFP_ZERO | __GFP_NOMEMALLOC | __GFP_COMP`; it is ORed
  into the caller's gfp.
- Accepted without a warning: `__GFP_ACCOUNT` and the four `gfp_nolock`
  bits.
- Any other caller bit: only trips `VM_WARN_ON_ONCE()`; the `ALLOC_NOLOCK`
  branch does not clear it and the allocation proceeds.
- Orders: `alloc_order_allowed()` returns `pcp_allowed_order(order)` for
  `ALLOC_NOLOCK`; any other order returns NULL with no warning.
- Order of the early tests: order first, then the gfp warning, then
  `alloc_nolock_allowed()`.
- `alloc_nolock_allowed()` fails when `can_spin_trylock()` in `mm/internal.h`
  is false or `deferred_pages_enabled()` is true.
- `can_spin_trylock()` is false in two cases: `CONFIG_PREEMPT_RT` in NMI or
  hardirq, and `!CONFIG_SMP` in NMI.
- `__alloc_frozen_pages_noprof()` makes no test of an arch primitive such as
  cmpxchg support.
- memcg charge failure: the page is freed with
  `__free_frozen_pages(page, order, FPI_NOLOCK)`, not `free_pages_nolock()`.

**Locks on the trylock-only path**

- `alloc_nolock_allowed()`: takes no argument and is called once, in
  `__alloc_frozen_pages_noprof()`; it is the entry gate, not what a helper
  calls.
- A helper that receives `alloc_flags` tests `alloc_flags & ALLOC_NOLOCK`
  itself; there is no ALLOC_TRYLOCK.
- A helper that sees only gfp tests `gfpflags_allow_spinning()`; for example
  `stack_depot_save_flags()` in `lib/stackdepot.c` and
  `add_stack_record_to_list()` in `mm/page_owner.c`, both reached from
  `post_alloc_hook()`.
- A reclaim bit passed by the caller is not cleared by the `ALLOC_NOLOCK`
  branch, so those gfp-only tests can then see a request that may spin.
- Helpers that take a lock with no test, for example, and what keeps them
  unreachable:

| Helper | Lock | What excludes it |
|---|---|---|
| `_deferred_grow_zone()` | `pgdat_resize_lock()` | `alloc_nolock_allowed()` fails while `deferred_pages_enabled()` |
| `reserve_highatomic_pageblock()` | `zone->lock` | needs `ALLOC_HIGHATOMIC` |
| `wakeup_kswapd()` in `rmqueue()` | waitqueue | needs `ALLOC_KSWAPD` |
| `cpuset_current_node_allowed()` | `callback_lock` | returns first for `__GFP_HARDWALL` |

- `ALLOC_HIGHATOMIC`: the fast path does compute it, as
  `alloc_flags_nonblocking(gfp, order) & ALLOC_HIGHATOMIC`; it stays clear
  because `alloc_flags_nonblocking()` returns 0 for `__GFP_NOMEMALLOC`, which
  `gfp_nolock` contains.
- gfp_to_alloc_flags() is not in this tree; `alloc_flags_slowpath()` does
  that job and is not reached with `ALLOC_NOLOCK`.
- `ALLOC_KSWAPD`: its only fast-path setter is `alloc_flags_nofragment()`,
  which `__alloc_frozen_pages_noprof()` skips for `ALLOC_NOLOCK`.
- `__GFP_HARDWALL`: `prepare_alloc_pages()` sets it in the gfp handed to
  `get_page_from_freelist()` whenever `cpusets_enabled()`.

**Any-context freeing**

- There is no FPI_TRYLOCK here; the flag is `FPI_NOLOCK` in
  `mm/page_alloc.c`.
- Three places pass `FPI_NOLOCK`: `free_pages_nolock()`,
  `free_frozen_pages_nolock()` (used by `__free_slab()` in `mm/slub.c`), and
  the charge-failure path of `__alloc_frozen_pages_noprof()`.
- `__free_pages()` passes `FPI_NONE`; it is not an any-context free.
- Page origin: `___free_pages()` and `__free_frozen_pages()` make no test of
  how the page was allocated, so pages from the ordinary allocator are
  accepted.
- `add_page_to_zone_llist()`: stores the order in `page->private`; struct
  page has no order field.
- `FPI_NOLOCK` with `can_spin_trylock()` false (also `!CONFIG_SMP` in NMI):
  the page goes to the llist with no lock tried.
- Draining `zone->trylock_free_pages`: done only by `free_one_page()` called
  without `FPI_NOLOCK`.
- Not drained by: any allocation path, `free_pcppages_bulk()`, or a
  `FPI_NOLOCK` free that got `zone->lock`.
- An ordinary free that lands on the per-CPU list therefore leaves the llist
  untouched, also when that list is later drained in bulk.

**Any-context kmalloc**

- Accepted gfp bits: `__GFP_ACCOUNT`, `__GFP_ZERO`, `__GFP_NOWARN`,
  `__GFP_NOMEMALLOC`; the last two are ORed in by
  `__kmalloc_nolock_noprof()`.
- There is no __GFP_NO_OBJ_EXT gfp bit here; `SLAB_ALLOC_NO_OBJ_EXT` in
  `mm/slab.h` is a slab alloc flag and callers of `kmalloc_nolock()` cannot
  pass it.
- Any other gfp bit: only trips `VM_WARN_ON_ONCE()`; the request is neither
  rejected nor stripped of the bit.
- No-spin mode is carried in `alloc_flags` of `struct slab_alloc_context`
  (`mm/slub.c`) as `SLAB_ALLOC_NOLOCK`, and tested with
  `alloc_flags_allow_spinning()`.
- `mm/slub.c` does not call `gfpflags_allow_spinning()`; an ordinary slab
  request whose gfp has no reclaim bit still has `SLAB_ALLOC_DEFAULT` and
  spins on slab locks.
- `kmalloc_flags()` in `mm/slab.h`: internal entry that takes `alloc_flags`;
  `__kmalloc_flags_noprof()` routes to `__kmalloc_nolock_noprof()` when
  `SLAB_ALLOC_NOLOCK` is set, as for obj_exts vectors and sheaves.
- Size 0: returns `ZERO_SIZE_PTR` before any context test.
- Returns NULL without trying, in this order:
  - `can_spin_trylock()` is false, which includes `!CONFIG_SMP` in NMI;
  - `size > KMALLOC_MAX_CACHE_SIZE`;
  - `!(s->flags & __CMPXCHG_DOUBLE) && !kmem_cache_debug(s)`.
- Bucket retry: taken once after any NULL from `___slab_alloc()`, from the
  next larger kmalloc bucket (`size = s->object_size + 1`);
  `mm/slub.c` does not call `local_lock_is_locked()`.
- There is no __slab_alloc_node() here; `__kmalloc_nolock_noprof()` calls
  `alloc_from_pcs()` and then `___slab_alloc()` directly.

**Pairing any-context allocation and free**

- Valid after `kmalloc_nolock()`: `kfree_nolock()`, `kfree_rcu_nolock()`
  (`include/linux/rcupdate.h`), `kfree()`, `kfree_rcu()`.
- `kfree()` and `kfree_rcu()` only where spinning is allowed.
- What lets `kfree()` and `kfree_rcu()` run without the matching alloc hooks:
  `delete_object_full()` and `paint_ptr()` in `mm/kmemleak.c` return silently
  for an unknown object, and `kfence_free()` returns false for a non-KFENCE
  address.
- In-tree frees with a function other than `kfree_nolock()`, for example:
  - `free_slab_obj_exts()` in `mm/slub.c` calls `kfree()` when `allow_spin`,
    on a vector that `alloc_slab_obj_exts()` may have got in no-spin mode;
  - `bpf_selem_free()` and `bpf_selem_free_trace_rcu()` in
    `kernel/bpf/bpf_local_storage.c` use `kfree_rcu()` and `kfree()` on
    objects from `bpf_map_kmalloc_nolock()`.
- `free_slab_obj_exts()` picks by the `allow_spin` of the free; nothing
  records how the vector was allocated.
- **Unsafe usage**: `kfree_nolock()` on an object that did not come from a
  `SLAB_ALLOC_NOLOCK` allocation.
  - Unsafe: an object from `kmalloc()` or `kmem_cache_alloc()` may be
    registered with kmemleak or belong to KFENCE; `kfree_nolock()` calls
    neither `kmemleak_free_recursive()` nor `kfence_free()`.
  - Unsafe: a large kmalloc object; `virt_to_slab()` is NULL, so
    `kfree_nolock()` warns once and returns without freeing.
  - Safe: the same flag chose the allocation and the free, as in
    `__kfree_rcu_sheaf()`, where `to_alloc_flags(free_flags)` allocates the
    sheaf and `__free_empty_sheaf()` frees it by `free_flags`.
  - Safe: the vector of a slab discarded by `free_new_slab_nolock()`; that
    slab was allocated by the same no-spin request.
- `kfree_nolock()` never tries `n->list_lock`; it calls `defer_free()` when
  `can_free_to_pcs()` is false or `free_to_pcs()` fails.
- There is no free_deferred_objects() here; `deferred_percpu_work_fn()` in
  `mm/slub.c` drains the per-CPU `deferred_percpu_work` llists from
  `irq_work`.

**kmemleak registration**

- `slab_post_alloc_hook()`: calls `kmemleak_alloc_recursive()` only when
  `alloc_flags_allow_spinning(ac->alloc_flags)`; the test is on the slab
  alloc flags, not on gfp.
- Unregistered therefore: `kmalloc_nolock()` objects and internal
  `kmalloc_flags()` requests made with `SLAB_ALLOC_NOLOCK`.
- There is no __GFP_NOLEAKTRACE here; the other slab-side test is
  `SLAB_NOLEAKTRACE` on the cache, in `kmemleak_alloc_recursive()`.
- On an object that was never registered:

| Function | Lookup | Result | Locks taken |
|---|---|---|---|
| `kmemleak_free()` | `find_and_remove_object()` | silent return | `kmemleak_lock` |
| `kmemleak_not_leak()` | `paint_ptr()` | silent return | `rcu_read_lock()`, `kmemleak_lock` |
| `kmemleak_ignore()` | `paint_ptr()` | silent return | `rcu_read_lock()`, `kmemleak_lock` |
| `kmemleak_no_scan()` | `object_no_scan()` | `kmemleak_warn()` | `rcu_read_lock()`, `kmemleak_lock` |

- `delete_object_full()`: has no warning for an unknown object in any
  configuration.
- `kmemleak_lock`: one raw spinlock, taken on these paths with
  `raw_spin_lock_irqsave()`; there is no read side and no trylock.
- **Potentially unsafe usage**: a kmemleak call on a pointer from a no-spin
  allocation.
  - Unsafe: from a context that may not spin; the lookup spins on
    `kmemleak_lock` even though the object is unknown.
  - Unsafe: `kmemleak_no_scan()`; it prints a warning and a stack dump for
    the unknown object.
  - Safe: `kmemleak_not_leak()` behind `if (allow_spin)`, as in
    `alloc_slab_obj_exts()`.
  - Safe: `kmemleak_free()` and `kmemleak_ignore()` where spinning is
    allowed, as `kfree()` and `kvfree_call_rcu()` do; both return silently.

**Slab retry without spinning**

- `___slab_alloc()` here has one retry label, `new_objects`, and no CPU
  slab; there is no retry_load_slab or redo label and no
  defer_deactivate_slab() in `mm/slub.c`.
- Of the cache's own locks, `___slab_alloc()` tries only `n->list_lock`, in
  `get_from_partial_node()`, `alloc_from_new_slab()` and
  `alloc_single_from_new_slab()`; there is no get_partial_node() here.
- Per-CPU sheaf lock: tried by `alloc_from_pcs()` with `local_trylock()`
  before `___slab_alloc()` is called; nothing checks
  `local_lock_is_locked()` first.
- `local_trylock()` without `CONFIG_PREEMPT_RT`: fails only when this CPU
  already holds the lock, so the failure lasts for the whole call.
- `local_trylock()` with `CONFIG_PREEMPT_RT`: always fails in NMI and
  hardirq.
- Failed `n->list_lock` trylock on a fresh slab: `free_new_slab_nolock()`
  frees the slab pages directly through `free_frozen_pages_nolock()`; the
  slab is not queued for `irq_work`.
- `get_from_any_partial()`: without `allow_spin` it does not call
  `read_mems_allowed_begin()`, and its `do`/`while` loop runs once.
- **Potentially unsafe usage**: jumping back to allocate another slab after
  `alloc_from_new_slab()` or `alloc_single_from_new_slab()` returned too
  little.
  - Unsafe: when `allow_spin` is false; the `n->list_lock` trylock can fail
    on every pass, and each pass allocates and discards a slab.
  - Safe: behind `if (allow_spin)`, as the second `goto new_objects` in
    `___slab_alloc()`.
  - Safe: when the call passes `allow_spin` true, as the `goto new_slab` in
    `refill_objects()`; `alloc_from_new_slab()` then spins on `n->list_lock`
    and never discards the slab.

## The slab allocator

**Layers of the slab allocator**

- `s->cpu_sheaves`: allocated for every cache in `do_kmem_cache_create()`;
  the fast paths make no NULL test.
- Cache without a per-CPU layer: `s->sheaf_capacity == 0`, tested by
  `cache_has_sheaves()` in `mm/slab.h`.
- `bootstrap_sheaf` in `init_percpu_sheaves()`: one static empty sheaf that
  `pcs->main` of every CPU points at when the capacity is 0; its `size` 0
  equals the capacity, so `alloc_from_pcs()` and `free_to_pcs()` both fall
  into the replace helpers, which test `cache_has_sheaves()` and back off.
- Capacity 0: see `calculate_sheaf_capacity()`. It is 0 under
  `CONFIG_SLUB_TINY`, with any `SLAB_DEBUG_FLAGS` bit, with `SLAB_NO_SHEAVES`
  (the two boot caches in `kmem_cache_init()`) and with `SLAB_NOLEAKTRACE`.
- kmalloc caches: capacity 0 until `bootstrap_kmalloc_sheaves()` runs.
- Per-node pointers: `s->per_node[nid].barn` and `s->per_node[nid].node`,
  `struct kmem_cache_per_node_ptrs` in `mm/slab.h`.
- `struct kmem_cache_node` has no barn member, and `struct kmem_cache` has no
  node array of its own.
- `slab_barn_nodes` (online nodes) decides where a barn exists; `slab_nodes`
  (nodes with memory) decides where a `struct kmem_cache_node` exists. An
  online node that never had memory has a barn, for a cache with sheaves,
  and no `struct kmem_cache_node`.
- `get_barn()`: uses `numa_node_id()`, while slab lists use `numa_mem_id()`.
  It can return NULL, and every caller tests for that.
- `struct slab_sheaf`: `capacity` and `pfmemalloc` share a union with
  `barn_list` and `rcu_head`; they are valid only while a caller of
  `kmem_cache_prefill_sheaf()` holds the sheaf. Elsewhere the capacity is
  `s->sheaf_capacity`. `node` is set only for a full `rcu_free` sheaf.

**Slab allocation path**

- `slab_alloc_node()`: calls `alloc_from_pcs()` without testing
  `cache_has_sheaves()`, then `___slab_alloc()` directly. There is no
  __slab_alloc_node() or __slab_alloc() here.
- Partial-list getters: `get_from_partial()`, `get_from_partial_node()` and
  `get_from_any_partial()`. There is no get_partial(), get_partial_node() or
  get_any_partial().
- `___slab_alloc()`: returns one object. A new slab goes through
  `alloc_from_new_slab()`, or `alloc_single_from_new_slab()` for debug caches
  and `CONFIG_SLUB_TINY`, which put the rest of the slab on the node list.
- Sheaf refill chain: `refill_sheaf()`, `refill_objects()`,
  `__refill_objects_node()` (`get_partial_node_bulk()` and
  `get_freelist_nofreeze()`), `__refill_objects_any()`, then `new_slab()` and
  `alloc_from_new_slab()`. There is no __refill_objects().
- `refill_objects()`: always fills from `numa_mem_id()` first; it takes no
  node argument, so sheaf refill never honours a node request.
  `kmem_cache_alloc_bulk_noprof()` has no node argument.
- `apply_strict_numa_policy()`: runs in `slab_alloc_node()` and
  `__kmalloc_nolock_noprof()`, before `alloc_from_pcs()`. It only changes
  `NUMA_NO_NODE`.
- `___slab_alloc()` with a node and no `__GFP_THISNODE`: first pass uses
  `trynode_flags`, the caller's flags reduced to `GFP_NOWAIT`,
  `__GFP_NOMEMALLOC` and `__GFP_ACCOUNT` bits plus `__GFP_NOWARN` and
  `__GFP_THISNODE`, for both the partial list and the new slab. The second
  pass uses the caller's flags. `node` is never rewritten to `NUMA_NO_NODE`.
- `pfmemalloc_match()`: called in `get_from_partial_node()` and
  `get_partial_node_bulk()`, not in `___slab_alloc()`. A slab that
  `___slab_alloc()` has just allocated is not tested.
- `alloc_from_pcs()`: makes no reserve test. Sheaves are kept free of reserve
  objects elsewhere: `__pcs_replace_empty_main()` refills with
  `__GFP_NOMEMALLOC`, and `can_free_to_pcs()` rejects them on free.

**Slab free path**

- `kfree()`: `virt_to_page()` then `page_slab()`; NULL means
  `free_large_kmalloc()`. There is no folio_slab() in this tree.
- `kmem_cache_free()`: there is no cache_from_obj() or virt_to_cache(). The
  check is open-coded. Under `CONFIG_SLAB_FREELIST_HARDENED` or
  `SLAB_CONSISTENCY_CHECKS`, a NULL slab or `slab->slab_cache != s` calls
  `warn_free_bad_obj()` and returns: the object is leaked, not freed to its
  real cache.
- `kmem_cache_free()` without those options: trusts the `s` it was passed.
- `slab_free()`: hooks, then `can_free_to_pcs()` and `free_to_pcs()`, else
  `__slab_free()`. There is no do_slab_free(), and `slab_free()` does not
  test `cache_has_sheaves()`.
- `can_free_to_pcs()`: holds both bypass tests, remote node and
  `slab_test_pfmemalloc()`.
- `can_free_to_pcs()` without `CONFIG_HAVE_MEMORYLESS_NODES`: compares with
  `numa_node_id()`, and accepts a remote object when the CPU's node lacks
  `N_NORMAL_MEMORY`. Sheaves can hold remote objects, so `alloc_from_pcs()`
  rechecks the node of the object it pops when a node was requested.
- `__pcs_replace_full_main()` when the barn returns `-E2BIG` and `allow_spin`
  is true: flushes the spare, not main, with `sheaf_flush_unused()` and
  reuses it as the empty sheaf. Main is flushed, by
  `sheaf_try_flush_main()`, only when `alloc_empty_sheaf()` fails.
- `__pcs_replace_full_main()` returning NULL: `slab_free()` frees that one
  object with `__slab_free()`.
- Sheaf flush: `sheaf_flush_unused()` and `__sheaf_flush_main_batch()` use
  `__kmem_cache_free_bulk()`, which runs no free hooks; see
  "Allocation and free hooks".
- `kmem_cache_free_bulk()` with `s == NULL`: never uses sheaves; it takes the
  `build_detached_freelist()` path.

**The slab descriptor**

- `page_slab()` in `mm/slab.h`: takes `compound_head()` first, then tests
  `page_type >> 24` against `PGTY_slab`. It returns NULL for anything else,
  large kmalloc pages (`PGTY_large_kmalloc`) included.
- Page type: set with `__SetPageSlab()` in `alloc_slab_page()`, on the head
  page only, and cleared with `__ClearPageSlab()` in `__free_slab()`.
  `mm/slub.c` does not call `__folio_set_slab()` or `folio_test_slab()`.
- `PageSlab()` on a tail page of a slab: false. Code that holds an arbitrary
  address uses `virt_to_slab()`.
- `enum slab_flags` in `mm/slub.c`: names the bits of `slab->flags` that slab
  code uses; it plays no part in identifying a slab.
- `SLAB_MATCH()`: `slab_cache` is matched against `compound_info`, the word
  after `flags` in `struct page`; `struct page` has no field named
  `compound_head`. No `SLAB_MATCH()` line covers `__page_type`.
- Without `CONFIG_MEMCG` and with `CONFIG_SLAB_OBJ_EXT`: `obj_exts` is matched
  against `_unused_slab_obj_exts`.
- A new field must leave alone: bit 0 of the `compound_info` word, the
  `page_type` word, `_refcount`, and `memcg_data`.
- `page->mapping`: overlaid by `slab_list.prev` and by the function pointer
  of `rcu_head`. `__free_slab()` sets `page->mapping = NULL` because
  `page_expected_state()` in `mm/page_alloc.c` rejects anything else.
- `SL_pfmemalloc` is `PG_active`, which is in `PAGE_FLAGS_CHECK_AT_FREE`;
  `__free_slab()` clears it with `__slab_clear_pfmemalloc()`.
- pfmemalloc mark: `page_is_pfmemalloc()` reads `page->lru.next`, the word
  that becomes `slab->slab_cache`. `alloc_slab_page()` copies it to
  `SL_pfmemalloc` before `allocate_slab()` writes `slab_cache`.
- `allocate_slab()` sets: `counters = 0`, `objects`, `obj_exts_needs_objcg`
  (64-bit), `slab_cache`, and `obj_exts` through `init_slab_obj_exts()`,
  `alloc_slab_obj_exts_early()` and `account_slab()`.
- `slab->counters = 0`: the only place where `frozen`, `inuse` and the
  64-bit bits `obj_exts_in_object` and `obj_exts_needs_objcg` of a new slab
  are cleared.
- `allocate_slab()` does not write `freelist`, run constructors, add the slab
  to a list or call `inc_slabs_node()`. There is no shuffle_freelist().
- Freelist of a new slab: built by the caller with `init_slab_obj_iter()`,
  `next_slab_obj()` and `build_slab_freelist()`, as `alloc_from_new_slab()`
  does. The caller hands out the objects it wants first, sets `inuse`, and
  links only the rest.
- `frozen`: set only by `alloc_debug_processing()`, to retire a slab that
  failed a consistency check.

**Slab locks**

- Order: as in the comment at the top of `mm/slub.c`: `cpu_hotplug_lock`,
  `slab_mutex`, `cpu_sheaves->lock`, `barn->lock`, `list_lock`,
  `slab_lock()`, `object_map_lock`. There is no cpu_slab lock.
- `flush_lock`: a mutex in `mm/slub.c` that the comment omits; taken inside
  `cpu_hotplug_lock` and `slab_mutex`, see `flush_all_rcu_sheaves()`.

| Lock | Kind | Only tried |
|---|---|---|
| `cpu_sheaves->lock` | `local_trylock_t` | in every alloc and free path |
| `barn->lock` | `spinlock_t`, irqsave | when `allow_spin` is false |
| `list_lock` | `spinlock_t`, irqsave | when `allow_spin` is false |
| `slab_lock()` | bit spinlock on `SL_locked` | never |
| `object_map_lock` | `spinlock_t` | never |

- `cpu_sheaves->lock`: also taken with `local_lock()`, in flush and prefill
  code; search `mm/slub.c` for `local_lock(&s->cpu_sheaves->lock)`. Those
  sites must not run in a context that can interrupt a holder.
- `allow_spin`: comes from `alloc_flags_allow_spinning()` or
  `free_flags_allow_spinning()` in `mm/slab.h`, that is `SLAB_ALLOC_NOLOCK`
  or `SLAB_FREE_NOLOCK`. `mm/slub.c` does not call
  `gfpflags_allow_spinning()`.
- `allow_spin` false does not prove a nolock context:
  `__refill_objects_any()` passes false to `__refill_objects_node()` from
  normal context, to skip a contended remote `list_lock`.
- Functions with no trylock form, for example: `__slab_free()`,
  `free_to_partial_list()`, `barn_put_empty_sheaf()`,
  `barn_put_full_sheaf()`, `barn_get_full_or_empty_sheaf()`. A nolock path
  must not reach them; `kfree_nolock()` uses `defer_free()` instead of
  `__slab_free()`.
- `slab_lock()`: one caller, `__update_freelist_slow()`, reached when the
  cache lacks `__CMPXCHG_DOUBLE`. Debug caches change the freelist under
  `list_lock` and do not take `slab_lock()`.
- `slab_update_freelist()`: wraps the slow path in `local_irq_save()` on
  every configuration. `__slab_update_freelist()` expects the caller to have
  IRQs off, and asserts it only without `CONFIG_PREEMPT_RT`.
- `CONFIG_PREEMPT_RT`: `kvfree_call_rcu()` skips `kfree_rcu_sheaf()`;
  `__kfree_rcu_sheaf()` has a `VM_WARN_ON_ONCE()` for being called there
  with spinning allowed.

**Allocation and free hooks**

- `slab_pre_alloc_hook()`: `might_alloc()` and `should_failslab()` only; no
  memcg work.
- `slab_free_hook()`: does not uncharge and does not drop the allocation
  tag. `memcg_slab_free_hook()` and `alloc_tagging_slab_free_hook()` are
  called beside it, for example in `slab_free()` and `free_to_pcs_bulk()`.
- `maybe_wipe_obj_freeptr()`: not part of `slab_post_alloc_hook()`. Each path
  that takes an object off a freelist calls it first, as `slab_alloc_node()`
  and `__refill_objects_node()` do.
- `slab_alloc_node()`: ignores the return value of `slab_post_alloc_hook()`;
  it relies on the memcg hook having set the object pointer to NULL.
- `memcg_alloc_abort_single()`: calls `alloc_tagging_slab_free_hook()`, then
  `slab_free_hook()`, then `__slab_free()` if the hook allows. It does not
  call `memcg_slab_free_hook()` and does not use the sheaves.
- Objects in a `main`, `spare` or barn sheaf: have already passed the free
  hooks and not yet the allocation hooks. A path that pops one must call
  `slab_post_alloc_hook()`, as `kmem_cache_alloc_from_sheaf_noprof()` does.
- Objects in an `rcu_free` sheaf: have passed no free hook yet;
  `__rcu_free_sheaf_prepare()` runs all three after the grace period, with
  `after_rcu_delay` true.
- `__kmalloc_nolock_noprof()`: skips `slab_pre_alloc_hook()` and
  `kfence_alloc()`.
- `kfree_nolock()`: does not call `slab_free_hook()`; it calls
  `memcg_slab_free_hook()`, `alloc_tagging_slab_free_hook()`,
  `kmsan_slab_free()`, `kasan_slab_pre_free()` and `kasan_slab_free()`
  without quarantine itself. It is only for objects from `kmalloc_nolock()`.
- `kmem_cache_alloc_bulk_noprof()`: frees with `__kmem_cache_free_bulk()`
  when allocation fails before the hooks, and the memcg hook frees with
  `kmem_cache_free_bulk()` when the charge of more than one object fails
  after them.
- **Potentially unsafe usage**: freeing with `__slab_free()` or
  `__kmem_cache_free_bulk()`, which run no hooks.
  - Unsafe: for an object that has passed `slab_post_alloc_hook()` and has
    not passed `slab_free_hook()` and the two hooks beside it; KASAN,
    kmemleak, the tag and the charge stay in the allocated state.
  - Safe: for an object taken from a `main`, `spare` or barn sheaf, as
    `sheaf_flush_unused()` does; `slab_free()` runs the hooks before
    `free_to_pcs()`.
  - Safe: for an object that never reached `slab_post_alloc_hook()`, as the
    error path of `__kmem_cache_alloc_bulk()` does.
  - Safe: when the caller first ran the free hooks that still apply:
    `memcg_alloc_abort_single()` (the charge failed, so none to drop) and
    `slab_free_after_rcu_debug()` (the free that deferred the object, for
    example `slab_free()`, already dropped the charge and the tag).
- **Unsafe usage**: freeing an object after `slab_free_hook()` returned
  false.
  - Safe: drop the object from the batch, as `free_to_pcs_bulk()` and
    `slab_free_freelist_hook()` do; KFENCE, the KASAN quarantine or
    `CONFIG_SLUB_RCU_DEBUG` now owns it.

**Per-object extensions**

- `struct slabobj_ext`: holds one union of `_objcg` and `_ctref`, not two
  members. An object's extension is one or two consecutive elements, objcg
  first; `slab_obj_ext_size()` gives the size.
- Access: `slab_obj_ext()` in `mm/slab.h` for the element, then
  `slab_obj_ext_objcg()`, `slab_obj_ext_set_objcg()` or
  `slab_obj_ext_codetag_ref()`, all inside `get_slab_obj_exts()` and
  `put_slab_obj_exts()`. Indexing the vector by object index is wrong: the
  stride is `slab_obj_ext_size()` or `s->size`.
- `slab->obj_exts_needs_objcg` (64-bit): fixes the layout per slab; set in
  `allocate_slab()` from `SLAB_MAY_ACCOUNT`.

| Place | Set up by | Condition |
|---|---|---|
| separate kmalloc memory | `alloc_slab_obj_exts()` | no in-slab vector |
| slab space after the last object | `alloc_slab_obj_exts_early()` | `obj_exts_fit_within_slab_leftover()` |
| padding of each object | `alloc_slab_obj_exts_early()` | cache has `SLAB_OBJ_EXT_IN_OBJ`, 64-bit only |

- In-object placement: marked per slab by `obj_exts_in_object`, not by the
  cache flag; test with `obj_exts_in_object()` in `mm/slab.h`.
- `alloc_slab_obj_exts_early()`: does nothing unless `need_slab_obj_exts()`
  is true when the slab is created.
- Low bits: only bit 0 is used. With a pointer it is `MEMCG_DATA_OBJEXTS`;
  alone it is `OBJEXTS_ALLOC_FAIL`. There is no OBJEXTS_NOSPIN_ALLOC;
  `free_slab_obj_exts()` picks `kfree()` or `kfree_nolock()` from its
  `allow_spin` argument.
- Without `CONFIG_MEMCG`: a valid vector pointer has no flag bit set.
- `OBJEXTS_ALLOC_FAIL`: written only under
  `CONFIG_MEM_ALLOC_PROFILING_DEBUG`. It does not stop retries:
  `slab_obj_exts()` returns 0 for it, and the next allocation tries again.
- `free_slab_obj_exts()`: sets `slab->obj_exts = 0` in every case; it does
  not free a vector for which `obj_exts_in_slab()` is true.
- Bad-page check on a non-zero field: `page_expected_state()` in
  `mm/page_alloc.c` tests `page->memcg_data`, only under `CONFIG_MEMCG`.

**Allocation of the extension vector**

- `alloc_slab_obj_exts()`: allocates `slab_obj_ext_size(slab) *
  slab->objects` bytes with `kmalloc_flags()` and `__GFP_ZERO`. It does not
  call `kcalloc_node()`.
- `SLAB_ALLOC_NO_OBJ_EXT`: set by `alloc_slab_obj_exts()` only when
  `is_kmalloc_normal(s)`; it makes `kmalloc_slab()` pick the cache type
  `KMALLOC_NO_OBJ_EXT`.
- `KMALLOC_NO_OBJ_EXT` caches: created in `new_kmalloc_cache()` in
  `mm/slab_common.c` with `SLAB_NO_OBJ_EXT`, so their slabs never get a
  vector. They alias `KMALLOC_NORMAL` when `need_kmalloc_no_objext()` is
  false.
- Vector of any other cache: comes from a normal kmalloc cache, because
  `OBJCGS_CLEAR_MASK` strips the bits that select another type. That slab's
  own vector then comes from `KMALLOC_NO_OBJ_EXT`, where the chain ends.
- `CONFIG_DEBUG_VM`: `alloc_slab_obj_exts()` warns if the vector came from
  any other kind of cache.
- No size adjustment keeps the vector out of its own cache; there is no
  obj_exts_alloc_size().
- There is no mark_objexts_empty(). `mark_obj_codetag_empty()` is called only
  from `__free_empty_sheaf()`, for sheaves of kmalloc caches.
- `SLAB_ALLOC_NEW_SLAB`: passed by `account_slab()`; it lets
  `alloc_slab_obj_exts()` assign the field without `cmpxchg()`.

**Free pointers**

- Default `s->offset`: `ALIGN_DOWN(s->object_size / 2, sizeof(void *))`, not
  0; see `calculate_sizes()`.
- `SLAB_RED_ZONE`: moves the pointer after the object only when
  `s->object_size < sizeof(void *)` or `slub_debug_orig_size()` is true.
- `freeptr_offset`: allowed for a cache with `SLAB_TYPESAFE_BY_RCU` or with a
  constructor; `create_cache()` in `mm/slab_common.c` rejects it otherwise.
- There is no get_freepointer_safe() and no freelist_corrupted() in this
  tree.
- `mm/Makefile`: sets `KASAN_SANITIZE_slub.o := n`, so compiler-inserted
  KASAN checks do not cover accesses made in `mm/slub.c`.
- `kasan_reset_tag()`: still needed in slab code wherever an object address
  feeds arithmetic or a comparison, for example the hardened hash,
  `__obj_to_index()` and `check_valid_pointer()`.
- Pointers held in a freelist or a sheaf: still carry an old tag, for a
  freed object that of the previous allocation; `kasan_slab_alloc()` assigns
  the tag in `slab_post_alloc_hook()`, a new one unless the cache has a
  constructor or `SLAB_TYPESAFE_BY_RCU`.
- `metadata_access_enable()` and `metadata_access_disable()` in
  `mm/slab.h`: `check_bytes_and_report()` wraps `memchr_inv()`, a helper
  outside `mm/slub.c`, in them, on top of `kasan_reset_tag()`. Under
  `CONFIG_KASAN_HW_TAGS` `kasan_disable_current()` is an empty inline, so
  there only `kasan_reset_tag()` counts.
- **Potentially unsafe usage**: reading or writing `object + s->offset`
  without `get_freepointer()` or `set_freepointer()`.
  - Unsafe: while the object is linked on a slab freelist or a detached
    freelist; under `CONFIG_SLAB_FREELIST_HARDENED` the next
    `get_freepointer()` decodes the raw value to a wrong address.
  - Safe: zeroing the slot of an object that is leaving the free state, as
    `maybe_wipe_obj_freeptr()` does.
  - Safe: using the slot as a list node while the object is on no freelist,
    as `defer_free()` does; `deferred_percpu_work_fn()` rewrites it with
    `set_freepointer()` before `__slab_free()`.
- **Unsafe usage**: `set_freepointer()` with `fp` equal to `object`; it is a
  `BUG_ON()` under `CONFIG_SLAB_FREELIST_HARDENED`.
  - Safe: link an object only to a different object or NULL, as
    `build_slab_freelist()` does.
- **Unsafe usage**: `memset()` or a read of a free object through the pointer
  as stored, under `CONFIG_KASAN_HW_TAGS`; the hardware checks the stale
  pointer tag against memory that `kasan_slab_free()` has poisoned.
  - Safe: apply `kasan_reset_tag()` first, as `get_freepointer()` and
    `init_object()` do.

**Type-safe-by-RCU caches**

- There is no __sk_nulls_lookup() in this tree; `__inet_lookup_established()`
  in `net/ipv4/inet_hashtables.c` is a lookup of this form.
- Ordering: the identity check must come after the reference is taken. The
  comment at the flag names `refcount_inc_not_zero_acquire()`,
  `refcount_add_not_zero_acquire()` and `refcount_set_release()` in
  `include/linux/refcount.h` as the helpers with the needed fences.
- Writer side: initialise the whole object before the refcount;
  `refcount_set_release()` gives the store ordering, as
  `vma_mark_attached()` in `include/linux/mmap_lock.h` uses.
- `freeptr_offset` in `struct kmem_cache_args`: puts the free pointer inside
  the object, so the field under it can be overwritten while the object is
  free. It must not overlay a field a reader uses to detect reuse;
  `create_cache()` in `mm/slab_common.c` does not check what it overlays.
- **Potentially unsafe usage**: taking a lock inside the object before taking
  a reference.
  - Unsafe: when the lock is initialised after each allocation; the reader
    can take a lock that the new owner is initialising.
  - Safe: when a constructor initialises the lock and no allocation path
    reinitialises it, as with `sighand_ctor()` in `kernel/fork.c` and
    `anon_vma_ctor()` in `mm/rmap.c`; then recheck identity under the lock,
    as `lock_task_sighand()` does.

## kmalloc memory

**kmalloc caches**

- Partition names: there is no KMALLOC_RANDOM_START, KMALLOC_RANDOM_END or
  RANDOM_KMALLOC_CACHES_NR here. The normal caches are split under
  `CONFIG_KMALLOC_PARTITION_CACHES` into `KMALLOC_PARTITION_START` to
  `KMALLOC_PARTITION_END` (`KMALLOC_PARTITION_CACHES_NR` + 1 = 16 rows). Row 0
  is `KMALLOC_NORMAL`, named "kmalloc-<size>"; the other 15 are named
  "kmalloc-part-NN-<size>".
- `RANDOM_KMALLOC_CACHES`: only a transitional symbol in `mm/Kconfig` that sets
  the default of `KMALLOC_PARTITION_CACHES`; no C code tests it.
- Partition key: a `kmalloc_token_t`, built by `__kmalloc_token()` where the
  `kmalloc()` macro expands, not `_RET_IP_` inside the allocator.

  | Mode | Token | Row chosen by `kmalloc_type()` |
  |---|---|---|
  | `CONFIG_KMALLOC_PARTITION_RANDOM` | `_CODE_LOCATION_` | `hash_64()` of token XOR `random_kmalloc_seed`, 4 bits |
  | `CONFIG_KMALLOC_PARTITION_TYPED` | `__builtin_infer_alloc_token()` of the call's arguments | the token itself; `Makefile` bounds it with `-falloc-token-max=16` |

- Token plumbing: the token is an extra parameter of the out-of-line
  allocators that pick a cache, for example `__kmalloc_noprof()`, hidden by
  `DECL_TOKEN_PARAMS()` and `PASS_TOKEN_PARAMS()` in `include/linux/slab.h`
  (`DECL_KMALLOC_PARAMS()` and `PASS_KMALLOC_PARAMS()` where a bucket is passed
  too); a new wrapper must pass it on, as `_kmalloc_array_noprof()` does.
- `KMALLOC_NO_OBJ_EXT` (`CONFIG_SLAB_OBJ_EXT`, "kmalloc-no-objext-<size>"): a
  row that no GFP bit selects; `kmalloc_slab()` in `mm/slab.h` forces it when
  `alloc_flags` has `SLAB_ALLOC_NO_OBJ_EXT`, after `kmalloc_type()` ran.
- Large path: there is no __kmalloc_large_node() here; `___kmalloc_large_node()`
  in `mm/slub.c` does the work. It does not call `alloc_pages_node()`; it uses
  `alloc_frozen_pages_noprof()` or `__alloc_frozen_pages_noprof()` and then
  `__SetPageLargeKmalloc()`.
- `kfree()`: does not call `virt_to_folio()`; it uses `virt_to_page()` and
  `page_slab()`, which tests `PGTY_slab` on the compound head. NULL means a
  large allocation.
- `free_large_kmalloc()`: if `PageLargeKmalloc()` is false it warns once,
  calls `dump_page()` and returns without freeing.

**kmalloc alignment**

- Non-power-of-two size: aligned to at least the largest power-of-two divisor
  of the size, not only to `ARCH_KMALLOC_MINALIGN` (96 gives 32, 192 gives 64).
- `create_boot_cache()`: one expression, `max(align, 1U << (ffs(size) - 1))`,
  applied only when `flags` has `SLAB_KMALLOC`. KMALLOC_MAX_ALIGN is not in
  this tree.
- `SLAB_KMALLOC`: among the callers of `create_boot_cache()` only
  `create_kmalloc_cache()` passes it, so the enforcement covers the
  `kmalloc_caches` rows.
- `kmem_buckets_create()` caches: made by `kmem_cache_create_usercopy()` with
  align 0 and without `SLAB_KMALLOC`; they never pass through
  `create_boot_cache()`, so `calculate_alignment()` gives them only
  `arch_slab_minalign()` rounded up to `sizeof(void *)`, unless the caller
  passes `SLAB_HWCACHE_ALIGN`.
- `new_kmalloc_cache()`: when `__kmalloc_minalign()` exceeds
  `ARCH_KMALLOC_MINALIGN`, it rounds the cache size up to a multiple of that
  value and points the smaller index at the larger cache.

**Pages behind kmalloc memory**

- Slab page reference count: zero. `alloc_slab_page()` in `mm/slub.c` takes
  frozen pages (for example `alloc_frozen_pages()`), and `__free_slab()`
  returns them with `free_frozen_pages()`, or with
  `free_frozen_pages_nolock()` when `allow_spin` is false.
- Large kmalloc page reference count: also zero; `___kmalloc_large_node()`
  uses `alloc_frozen_pages_noprof()` or `__alloc_frozen_pages_noprof()`. The
  page type is `PGTY_large_kmalloc`.
- `sendpage_ok()`: false for slab memory and for large kmalloc memory, because
  `page_count()` is 0 in both.
- `sendpage_ok()` on a tail page: `PageSlab()` tests only the page given and
  the slab type is set on the head; the `page_count()` test, which goes
  through `page_folio()`, is what rejects it.
- `get_page()` on a slab or large-kmalloc folio: `WARN_ON_ONCE()` and return,
  no reference is taken (`include/linux/mm.h`).
- `put_page()` on a slab or large-kmalloc folio: returns silently, nothing is
  dropped.
- `folio_get()` called directly: no such filter; it hits `VM_BUG_ON_FOLIO()`
  on the zero count, under `CONFIG_DEBUG_VM` only.
- `try_get_page()`: warns once and returns false when the count is 0 or less.
- **Unsafe usage**: giving the `struct page` of a kmalloc buffer to code that
  holds the memory by page reference (`get_page()`, `folio_get()`,
  `MSG_SPLICE_PAGES`). `get_page()` takes no reference and `kfree()` does not
  test the page count, so `kfree()` releases the memory while that code still
  uses it.
  - Safe: test `sendpages_ok()` or `sendpage_ok()` first and clear
    `MSG_SPLICE_PAGES` so the data is copied, as `nvme_tcp_try_send_data()` in
    `drivers/nvme/host/tcp.c` does. `skb_splice_from_iter()` enforces it with
    `WARN_ON_ONCE()` and `-EIO`.
  - Safe: `sg_set_buf()` on a linear-map buffer that is not freed until the
    I/O is complete. It stores page, offset and length and takes no reference;
    `CONFIG_DEBUG_SG` checks the address with `virt_addr_valid()`.

**Zone bits passed to kmalloc**

- `KMALLOC_DMA` cache names: "dma-kmalloc-<size>", see `KMALLOC_DMA_NAME()` in
  `mm/slab_common.c`.
- `kmalloc_fix_flags()`: defined in `mm/slab_common.c`, not `mm/slub.c`.
- Warning form: `pr_warn()` followed by `dump_stack()`, printed on every hit;
  it is not once-only, and it is compiled out only without `CONFIG_PRINTK`.
- Large path (`___kmalloc_large_node()`): after `kmalloc_fix_flags()` it only
  adds `__GFP_COMP`, so `__GFP_DMA` and `__GFP_MOVABLE` reach the page
  allocator unchanged.
- Preferred node without `__GFP_THISNODE`: the first attempt in
  `___slab_alloc()` masks the flags to
  `GFP_NOWAIT | __GFP_NOMEMALLOC | __GFP_ACCOUNT` before `new_slab()`, so the
  bad bits are gone and no warning is printed if that attempt succeeds.

**Zeroing in krealloc**

- Capacity `ks`: `__do_krealloc()` does not call `ksize()`. `ks` is
  `s->object_size` for a slab object, `page_size()` for a large kmalloc and
  `kfence_ksize()` for a KFENCE object.
- In-place conditions: `new_size <= ks`, the pointer satisfies `align`, and
  not (`__GFP_THISNODE` with a `nid` that is neither `NUMA_NO_NODE` nor the
  page's node). Otherwise it allocates anew.
- Requested size tracking, for a slab object: only when
  `slub_debug_orig_size()` is true, that is `SLAB_STORE_USER` debugging active
  on a `SLAB_KMALLOC` cache. `CONFIG_KASAN` or `CONFIG_SLUB_DEBUG` alone do not
  store it, and `SLAB_RED_ZONE` is not required.
- Settings consulted on the in-place path: `want_init_on_alloc()` only;
  `want_init_on_free()` is not tested, on a shrink or on a grow.
- Grow with the size not tracked: when `want_init_on_alloc()` is true it
  zeroes `[new_size, ks)` only; the bytes between the old and new size are not
  touched.

**kvmalloc fallback**

- `kmalloc_gfp_adjust()`, for `size > PAGE_SIZE` only: adds `__GFP_NOWARN`,
  clears `__GFP_DIRECT_RECLAIM` unless `__GFP_RETRY_MAYFAIL` is set, clears
  `__GFP_NOFAIL`.
- `kmalloc_gfp_adjust()` does not add `__GFP_NORETRY` and does not test
  `PAGE_ALLOC_COSTLY_ORDER`.
- Masks that skip the fallback: none. `__kvmalloc_node_noprof()` has no early
  return for non-blocking masks, nor any test of `__GFP_FS` or `__GFP_IO`.
- `gfpflags_allow_blocking()` in `__kvmalloc_node_noprof()`: only decides
  whether `VM_ALLOW_HUGE_VMAP` is passed to `__vmalloc_node_range_noprof()`.
- `GFP_ATOMIC` or `GFP_NOWAIT` with `size > PAGE_SIZE`: can return vmalloc
  memory.
- Fallback skipped only when: kmalloc succeeded, `size <= PAGE_SIZE`, or
  `size > INT_MAX`.
- `__GFP_NORETRY`: the kerneldoc of `kvmalloc_node()` calls it unsupported, but
  no code in `__kvmalloc_node_noprof()` tests for it.

**Contexts for kvfree**

- `kvfree_atomic()`: defined in `mm/slub.c`. It calls `vfree_atomic()` for a
  vmalloc address and `kfree()` otherwise.
- `kvfree_atomic()` contexts: any context except NMI, including task context
  with a spinlock held; `vfree_atomic()` has `BUG_ON(in_nmi())` and only
  queues the free to a work item.
- `kvfree()` contexts: preemptible task context, or interrupt context other
  than NMI. It is not limited to process context: `vfree()` hands off to
  `vfree_atomic()` when `in_interrupt()` is true.
- `in_interrupt()`: also true in task context with BH disabled, see
  `irq_count()` in `include/linux/preempt.h`.
- Memory from `kvmalloc()` with `GFP_ATOMIC` or `GFP_NOWAIT`: may be vmalloc
  memory in this tree (see "kvmalloc fallback"), so the allocation context
  does not show that `kfree()` semantics apply.
- **Potentially unsafe usage**: `kvfree()` in atomic context.
  - Unsafe: in task context with preemption off, IRQs off or a spinlock
    held, where `in_interrupt()` is false and the pointer may be a vmalloc
    address; `vfree()` reaches `might_sleep()`.
  - Safe: where `in_interrupt()` is true and not NMI; `vfree()` defers to
    `vfree_atomic()`. For example `bucket_table_free_rcu()` in
    `lib/rhashtable.c`, an RCU callback.
  - Safe: `kvfree_atomic()` instead, as `bucket_table_free_atomic()` in
    `lib/rhashtable.c` does.

## Mempools and vmalloc

**Mempool guarantees**

- `mempool_alloc_from_pool()` and `mempool_adjust_gfp()`: both exist in
  `mm/mempool.c`; the wait on `pool->wait` is inside
  `mempool_alloc_from_pool()`, not in `mempool_alloc_noprof()`.
- `bio_alloc_bioset()` in `block/bio.c`: does not clear
  `__GFP_DIRECT_RECLAIM` based on `current->bio_list`.
  - Mask without `__GFP_DIRECT_RECLAIM`: returns NULL when the slab attempt
    fails, before any `mempool_alloc()`.
  - Mask with it, when the slab attempt fails: calls
    `punt_bios_to_rescuer()`, then `mempool_alloc()` with the caller's
    unchanged mask, and uses the result with no NULL check.
- `mempool_alloc_bulk_noprof()`: the way to take several elements from one
  pool.
  - Takes no mask; uses `GFP_KERNEL` internally and always returns 0 with all
    `count` elements filled.
  - Takes from the reserve only when the reserve holds every element still
    missing; otherwise it takes none and retries, waiting on `pool->wait`
    from the second pass on.
  - `count > pool->min_nr`: `VM_WARN_ON_ONCE()`, which compiles to nothing
    without `CONFIG_DEBUG_VM`.
  - A caller that needs no-IO wraps the call in `memalloc_noio_save()`, as
    `blk_crypto_alloc_enc_bio()` does.
- `mempool_alloc_noreserve()` in `include/linux/mempool.h`: calls
  `pool->alloc` directly, never touches the reserve and never waits on
  `pool->wait`, so it can return NULL also with a mask that has
  `__GFP_DIRECT_RECLAIM`, and needs a NULL check.

**vmalloc and GFP masks**

- Scope location: `__vmalloc_area_node()` in `mm/vmalloc.c`, around the static
  `__vmap_pages_range()`; `__vmalloc_node_range_noprof()` applies none itself.
- `vmap_pages_range()` (not static, declared in `include/linux/vmalloc.h`):
  applies no scope.
- `memalloc_apply_gfp_scope()` and `memalloc_restore_scope()`: defined in
  `mm/vmalloc.c`; the first matching row wins:

| Mask | Scope |
|---|---|
| lacks `__GFP_DIRECT_RECLAIM`, or has `__GFP_NORETRY` or `__GFP_RETRY_MAYFAIL` | `memalloc_noreclaim_save()` |
| has `__GFP_IO`, lacks `__GFP_FS` | `memalloc_nofs_save()` |
| lacks both `__GFP_IO` and `__GFP_FS` | `memalloc_noio_save()` |
| anything else | none; returns 0 |

- `GFP_NOFS | __GFP_NORETRY`: gets only the `memalloc_noreclaim_save()` scope,
  because that row is tested first.
- KASAN shadow page tables: `__kasan_populate_vmalloc_do()` in
  `mm/kasan/shadow.c` uses the same two helpers around
  `apply_to_page_range()`.
- `vmalloc_fix_flags()`: clears every bit outside `GFP_VMALLOC_SUPPORTED` and
  does one `WARN_ONCE()`; the allocation goes on.
- `vmalloc_fix_flags()` callers: `__vmalloc_noprof()` and
  `vmalloc_huge_node_noprof()` only.
- Unfiltered entry points: `__vmalloc_node_noprof()`,
  `__vmalloc_node_range_noprof()`, `__kvmalloc_node_noprof()` and
  `vrealloc_node_align_noprof()` pass the mask on as given.
- `GFP_VMALLOC_SUPPORTED`: includes `__GFP_RETRY_MAYFAIL` and
  `__GFP_SKIP_KASAN`; `__GFP_NOWARN` and `__GFP_ACCOUNT` are in it through
  `GFP_NOWAIT` and `GFP_KERNEL_ACCOUNT`.
- Zone bits and `__GFP_HIGHMEM`: outside `GFP_VMALLOC_SUPPORTED`, so the two
  filtered entry points strip them; `vmalloc_32_noprof()` passes
  `GFP_VMALLOC32` through the unfiltered `__vmalloc_node_noprof()`.
- `__GFP_SKIP_KASAN` from the caller, under hardware tag-based KASAN:
  `__vmalloc_node_range_noprof()` skips `kasan_unpoison_vmalloc()` and does not
  add `__GFP_SKIP_KASAN | __GFP_SKIP_ZERO` or change `prot`.
- `__GFP_NOFAIL` with a mask that lacks `__GFP_DIRECT_RECLAIM`:
  `__vmalloc_area_node()` sets `nofail = false`, so the mapping step is not
  retried.

**Zeroing in vrealloc**

- Shrink in place: zeroes `[p + size, p + old_size)` when
  `want_init_on_free() || want_init_on_alloc(flags)`; either one is enough.
- Grow in place: zeroes nothing, whatever `flags` holds, `__GFP_ZERO`
  included.
- Grown bytes are zero only if the first allocation and every earlier shrink
  of that area ran with zeroing in effect.
- In-place grow bound: `size <= vm->nr_pages << PAGE_SHIFT`, not
  `get_vm_area_size()`; `alloced_size` only feeds the mismatch `WARN()`.
- Shrink across a page boundary: unmaps and frees the tail pages and lowers
  `vm->nr_pages`, after the `memset()`, when all of these hold:
  - `vm_area_page_order(vm)` is 0
  - `vm->flags` has neither `VM_FLUSH_RESET_PERMS` nor `VM_USERMAP`
  - `gfp_has_io_fs(flags)` is true
  - the new page count is below `vm->nr_pages`
- After such a shrink: a grow past the remaining pages goes to a new
  allocation through `__vmalloc_node_noprof()`; only growing the area is
  still a TODO.

**KASAN in vrealloc**

- `kasan_poison()`: does `WARN_ON()` and returns without poisoning when the
  address or the size is not a multiple of `KASAN_GRANULE_SIZE`; it rounds
  nothing.
- `__kasan_poison_vmalloc()` in `mm/kasan/shadow.c`: rounds the size up, then
  calls `kasan_poison()`; the start must still be aligned.
- `__kasan_vrealloc()`: in `mm/kasan/common.c`, under `CONFIG_KASAN_VMALLOC`;
  without it `kasan_vrealloc()` is an empty stub in `include/linux/kasan.h`.
- `__kasan_vrealloc()`: has no alignment test and no early return; equal sizes
  do nothing.
- Shrink, in order:
  - `kasan_poison_last_granule(addr, new_size)` marks the partly used granule
    at the new end.
  - Both sizes are rounded up to `KASAN_GRANULE_SIZE`.
  - If the rounded sizes still differ, `__kasan_poison_vmalloc()` poisons
    from the rounded new end to the rounded old end.
- Shrink never unpoisons, and leaves bytes below the new end accessible.
- Grow: rounds `old_size` down, then `__kasan_unpoison_vmalloc()` from there
  to `new_size`, with `KASAN_VMALLOC_PROT_NORMAL | KASAN_VMALLOC_VM_ALLOC |
  KASAN_VMALLOC_KEEP_TAG`; it does not start from `addr`.
- `addr`: `__kasan_vrealloc()` does not align it; the rounded offsets are
  granule aligned only if `addr` is.
- Outside `CONFIG_KASAN_GENERIC`: `kasan_poison_last_granule()` is an empty
  stub in `mm/kasan/kasan.h`, so a shrink that stays inside one granule
  changes nothing.
- Hardware tag-based KASAN: `__kasan_poison_vmalloc()` in
  `mm/kasan/hw_tags.c` is empty, so a shrink poisons nothing.

## Boot-time allocation

**Memblock range parameters**

- `memmap_init_reserved_range()`: `static void __init` in `mm/memblock.c`,
  takes `(phys_addr_t start, phys_addr_t end, int nid)`; `end` is exclusive.
- `memmap_init_reserved_range()` has one caller,
  `memmap_init_reserved_pages()`, which computes
  `end = start + region->size` from the base/size pair in
  `struct memblock_region`.
- There is no reserve_bootmem_region() in this tree.
- `memblock_free()`: takes `(void *ptr, size_t size)`, a virtual address;
  `memblock_phys_free()` takes the physical `base, size`.
- Second parameter name decides the convention: a first parameter named
  `start` is paired with a size in, for example, `reserved_mem_add()` and
  `memblock_double_array()` (`new_area_start`, `new_area_size`).
- Rounding of start/end helpers in `mm/memblock.c` differs:
  `memmap_init_reserved_range()` rounds outward (`PFN_DOWN(start)`,
  `PFN_UP(end)`); `__free_memory_core()` and `__free_reserved_area()` round
  inward (`PFN_UP(start)`, `PFN_DOWN(end)`).
- A start/end pair handed to a base/size function is written `end - start`;
  see `free_memmap()` and `free_reserved_area()` in `mm/memblock.c`.
- **Potentially unsafe usage**: passing a value that looks like an end
  address as the `size` of a base/size function.
  - Unsafe: when `base` is not 0 and the value is a real end address, not
    the all-ones value; the region covers `[base, base + end)`.
  - Safe: the all-ones value (`PHYS_ADDR_MAX`, `-1`, `ULLONG_MAX`) with any
    `base`, to mean "up to the top", as `memblock_clear_hotplug(0, -1)` in
    `free_low_memory_core_early()` and
    `memblock_remove(1ULL << PHYS_MASK_SHIFT, ULLONG_MAX)` in
    `arm64_memblock_init()` do; `memblock_cap_size()` clamps the size to
    `PHYS_ADDR_MAX - base` in `memblock_add_range()` and
    `memblock_isolate_range()`.

**Memblock lifetime**

- `__init_memblock` and `__initdata_memblock` in
  `include/linux/memblock.h`: `__meminit` and `__meminitdata` without
  `CONFIG_ARCH_KEEP_MEMBLOCK`, empty with it.
- `__meminit` in `include/linux/init.h` is empty under
  `CONFIG_MEMORY_HOTPLUG`, so code marked `__init_memblock` and the static
  arrays are discarded only when both `CONFIG_ARCH_KEEP_MEMBLOCK` and
  `CONFIG_MEMORY_HOTPLUG` are off.
- `memblock_discard()` (without `CONFIG_ARCH_KEEP_MEMBLOCK`): frees resized
  arrays but leaves `memblock.memory.regions` and
  `memblock.reserved.regions` pointing at them, and sets `memblock_memory`
  to NULL; the data is stale afterwards even when `CONFIG_MEMORY_HOTPLUG`
  keeps the section.
- `physmem` and `memblock_physmem_init_regions` in `mm/memblock.c` carry no
  `__initdata_memblock`; they survive in every configuration that has
  `CONFIG_HAVE_MEMBLOCK_PHYS_MAP`.
- Allocation failure: `memblock_alloc_try_nid()` and
  `memblock_alloc_range_nid()` only return NULL or 0; the only message
  `memblock_alloc_range_nid()` itself prints on failure is
  `pr_warn_ratelimited()` when mirrored memory runs out and the search is
  retried.
- There is no memblock_free_late() in this tree; `memblock_phys_free()`
  (and `memblock_free()`, which wraps it) does that job.
- `memblock_phys_free()` once `slab_is_available()`: hands the pages to the
  buddy allocator through `__free_reserved_area()`; `memblock_discard()`
  relies on this.
- `memblock.reserved` after a late free: `memblock_phys_free()` and
  `free_reserved_area()` remove the range only with
  `CONFIG_ARCH_KEEP_MEMBLOCK`.
- `memblock_free()` and `memblock_phys_free()` are `__init_memblock`;
  `free_reserved_area()` has no section annotation, so it is usable from
  non-init code in every configuration.
- **Potentially unsafe usage**: `memblock_free()` or `memblock_phys_free()`
  after `memblock_free_all()`.
  - Unsafe: before `slab_is_available()` is true; only `memblock.reserved`
    is edited and the pages never reach the buddy allocator.
  - Unsafe: with `CONFIG_DEFERRED_STRUCT_PAGE_INIT`, before
    `page_alloc_init_late()` disables `deferred_pages`;
    `__free_reserved_area()` WARNs and frees nothing. The same holds for
    `free_reserved_area()`.
  - Safe: after `page_alloc_init_late()` has disabled `deferred_pages`, as
    `memblock_discard()` does.
- **Potentially unsafe usage**: `kfree()` or `free_pages()` on memory
  obtained from memblock.
  - Unsafe: when memblock served the allocation; the pages are
    `PageReserved` and need what `free_reserved_pages()` in
    `mm/page_alloc.c` does (clear reserved, zero the count,
    `adjust_managed_page_count()`).
  - Safe: `kfree()` when the allocation was made after
    `slab_is_available()` and so came from the slab; `memblock_discard()`
    chooses between `kfree()` and `memblock_free()` with
    `memblock_memory_in_slab` and `memblock_reserved_in_slab`, which
    `memblock_double_array()` records.

**Memblock availability window**

- `memblock_free_all()`: declared in `mm/mm_init.h`, called only by
  `mm_core_init()` in `mm/mm_init.c`, directly; `mem_init()` and
  `kmem_cache_init()` follow it. No arch code calls it.
- `WARN_ON_ONCE(slab_is_available())` and the `kzalloc_node(size,
  GFP_NOWAIT, nid)` fallback are in `memblock_alloc_range_nid()`, not
  `memblock_alloc_internal()`; `memblock_phys_alloc_range()` and
  `memblock_phys_alloc_try_nid()` get the fallback too and return
  `virt_to_phys()` of slab memory.
- The fallback ignores `align`, `start` and `end`.
- `memblock_alloc_hugetlb()`: does not call `memblock_alloc_range_nid()`,
  so it gets neither the warning nor the slab fallback.
- Unwarned gap: from `memblock_free_all()` until `create_kmalloc_caches()`
  sets `slab_state = UP` inside `kmem_cache_init()`; it covers `mem_init()`.
- Full region array before `memblock_allow_resize()`:
  `memblock_double_array()` panics with "cannot resize"; nothing overflows.

**mm globals early in boot**

- `free_area_init()`: static in `mm/mm_init.c`, takes no arguments, called
  only from `mm_core_init_early()`, which `start_kernel()` calls
  immediately after `setup_arch()`.
- Arch code does not call `free_area_init()`; it supplies zone limits
  through `arch_zone_limits_init()`.
- Everything in `setup_arch()` runs before the zone fields and
  `arch_zone_lowest_possible_pfn[]` are set.
- `parse_early_param()`: the call in `start_kernel()` comes after
  `mm_core_init_early()`; it runs the handlers only once, so it does nothing
  when `setup_arch()` already called it, as for example
  `arch/x86/kernel/setup.c` does.
- `high_memory`: `set_high_memory()`, last step of `free_area_init()`, sets
  it only when it is still NULL.
- `high_memory` on arches that assign it in `setup_arch()` is valid from
  that assignment, for example `initmem_init()` in
  `arch/x86/mm/init_32.c`; search `arch/` for `high_memory =`.
- `node_states` in `mm/page_alloc.c` has a static initialiser:
  `N_POSSIBLE` all nodes, `N_ONLINE` node 0; without `CONFIG_NUMA` also
  node 0 in `N_NORMAL_MEMORY`, `N_HIGH_MEMORY`, `N_MEMORY` and `N_CPU`.
- With `MAX_NUMNODES == 1`: `node_state()` returns `node == 0` and
  `node_set_state()` is empty (`include/linux/nodemask.h`); the masks are
  "not yet valid" only on NUMA builds.
- `N_MEMORY`: the lasting setter at boot is the `for_each_node()` loop in
  `free_area_init()`, for nodes with `node_present_pages`.
- `early_calculate_totalpages()` also sets `N_MEMORY`, but
  `find_zone_movable_pfns_for_nodes()` restores the saved mask before it
  returns.
- `N_CPU`: not set by `free_area_init()`; `init_cpu_node_state()` and
  `vmstat_cpu_online()` in `mm/vmstat.c` set it, under `CONFIG_SMP`.
- `memblock_end_of_DRAM()`: returns an exclusive end and reads
  `memblock.memory.regions[cnt - 1]`; call it only after the arch has added
  memory.

## Cgroup charging and statistics

**Opting in to cgroup charging**

- `memcg_slab_post_alloc_hook()` in `mm/slub.c`: charges when `__GFP_ACCOUNT`
  or `SLAB_ACCOUNT` is set; either one alone is enough.
- There is no memcg_slab_pre_alloc_hook() here; `slab_pre_alloc_hook()` does
  no memcg work.
- `SLAB_MAY_ACCOUNT`: not an opt-in. It marks caches whose slabs reserve an
  objcg slot per object; see `cache_needs_objcg()` in `mm/slab.h`.
- `SLAB_MAY_ACCOUNT` is added by `__kmem_cache_create_args()` and
  `new_kmalloc_cache()` unless `mem_cgroup_kmem_disabled()`; for example the
  `KMALLOC_NORMAL` and `KMALLOC_NO_OBJ_EXT` kmalloc caches lack it when
  `CONFIG_SLUB_TINY` is off.
- `new_slab()`: keeps only `GFP_RECLAIM_MASK | GFP_CONSTRAINT_MASK`, so
  `__GFP_ACCOUNT` never reaches the page allocator for a slab page.
- Page allocator: the charge is in `__alloc_frozen_pages_noprof()` in
  `mm/page_alloc.c`; on failure the page goes to `__free_frozen_pages()` and
  NULL is returned.
- `alloc_slab_obj_exts()` failure in `__memcg_slab_post_alloc_hook()`: the
  object is returned to the caller uncharged; the allocation does not fail.
- `__GFP_NOFAIL` is stripped from the vector allocation (`OBJCGS_CLEAR_MASK`
  in `mm/slub.c`), so a `__GFP_NOFAIL | __GFP_ACCOUNT` object can also come
  back uncharged.
- KFENCE object on a slab with no vector: skipped, returned uncharged.
- `try_charge_memcg()` in `mm/memcontrol.c`: forces the charge over the limit
  for `__GFP_NOFAIL`, for `__GFP_HIGH` (so `GFP_ATOMIC | __GFP_ACCOUNT`), and
  for a `PF_MEMALLOC` task; none of these returns `-ENOMEM`.

**Choosing the cgroup**

- `current_obj_cgroup()` in `mm/memcontrol.c`: returns the root memcg's objcg,
  not NULL, for a root-cgroup task, a kernel thread, a task without `mm`, and
  non-task context without `int_active_memcg`.
- Charge skipped: callers test `!objcg || obj_cgroup_is_root(objcg)`; see
  `__memcg_slab_post_alloc_hook()`, `__memcg_kmem_charge_page()` and
  `pcpu_memcg_pre_alloc_hook()`; a NULL test alone does not mean "not
  charged".
- NULL return: only for `in_nmi()` when `CONFIG_MEMCG_NMI_UNSAFE` is set.
- The objcg is per node: `memcg->nodeinfo[nid]->objcg` with `numa_node_id()`;
  the field is in `struct mem_cgroup_per_node`, `struct mem_cgroup` has none.
- Override walk: goes up `parent_mem_cgroup()` until a per-node `objcg` is
  non-NULL, and ends at the root objcg.
- Offlined override memcg: `__memcg_reparent_objcgs()` cleared its `objcg`, so
  the charge lands on the nearest ancestor that still has one.
- Task's own cgroup on the kmem path: `mem_cgroup_from_task(current)` in
  `current_objcg_update()`, which does not read `mm->owner`;
  `get_mem_cgroup_from_mm()` does.
- `get_mem_cgroup_from_current()`: does not read the override.
- `get_mem_cgroup_from_mm()`: reads the override only when `mm` is NULL.
- `set_active_memcg(NULL)`: ends the override, so in task context the
  allocation is charged to the current task again.
- `set_active_memcg(root_mem_cgroup)`: suppresses the charge, as
  `filemap_add_folio()` in `mm/filemap.c` does for kernel files.
- **Potentially unsafe usage**: calling `set_active_memcg()` on a memcg
  without taking a reference in the same function.
  - Unsafe: when nothing else keeps the memcg alive until the old value is
    restored; `current_obj_cgroup()` dereferences it with no RCU lock and no
    reference, and `get_mem_cgroup_from_mm()` uses `css_get()`, not
    `css_tryget()`.
  - Safe: the memcg is pinned by an object the caller holds, as
    `fanotify_alloc_event()` uses `group->memcg`, taken in group creation and
    dropped in `fsnotify_final_destroy_group()`.
  - Safe: the memcg is `root_mem_cgroup`, which is never freed (its css has
    `CSS_NO_REF`), as in `filemap_add_folio()`.

**Node and cgroup statistics**

- NULL memcg in `lruvec_stat_mod_folio()` and `mod_lruvec_kmem_state()`: an
  explicit test calls `mod_node_page_state()`; no lruvec is involved.
- `mem_cgroup_lruvec()` with a NULL memcg: returns the root memcg's lruvec;
  `mod_lruvec_state()` on it updates the root memcg's counters as well as the
  node. It returns `pgdat->__lruvec` only when `mem_cgroup_disabled()`.
- "No cgroup" means `memcg_data` is 0 (or the object's slot holds no objcg).
- Folio charged by a root-cgroup task: `charge_memcg()` commits the root
  objcg, so `folio_memcg()` is `root_mem_cgroup` and the root memcg's counters
  are updated too.
- Kernel page or slab object allocated by a root-cgroup task:
  `__memcg_kmem_charge_page()` and `__memcg_slab_post_alloc_hook()` store no
  objcg, so the helpers update the node only.
- `mod_lruvec_kmem_state()`: finds the memcg with `mem_cgroup_from_virt()` in
  `mm/memcontrol.c`; there is no mem_cgroup_from_slab_obj() here.
- `mem_cgroup_from_virt()` on a non-slab address: uses
  `folio_memcg_check()` on the page's folio.
- `folio_memcg()`: goes through the folio's objcg; after
  `__memcg_reparent_objcgs()` the update lands on the parent memcg.
- Per-object slab statistics: `__account_obj_stock()` → `mod_objcg_mlstate()`,
  memcg side only; there is no mod_objcg_state() or
  obj_cgroup_charge_account() here.

**Statistics across a late charge**

- `kmem_cache_charge()`: calls `memcg_slab_post_charge()`, which calls
  `__memcg_slab_post_alloc_hook()` directly; neither `__GFP_ACCOUNT` nor
  `SLAB_ACCOUNT` is tested, and there is no virt_to_cache() here.
- Skipped cache: `memcg_slab_post_charge()` returns true without charging when
  `!cache_needs_objcg(s)`, that is, the cache lacks `SLAB_MAY_ACCOUNT`.
- Returns true with no charge and no statistics change also when the objcg is
  the root objcg, and when `alloc_slab_obj_exts()` fails.
- Slab object, memcg side: `__account_obj_stock()` adds `obj_full_size()` to
  the memcg's `cache_vmstat_idx()` counter; there is no mod_objcg_state()
  here.
- Slab object, node side: not touched by the late charge or by the per-object
  free; only `account_slab()` and `unaccount_slab()` change it.
- Large kmalloc is handled first, tested with `PageLargeKmalloc()`:
  - already charged (`PageMemcgKmem()`): returns true;
  - charges with `__memcg_kmem_charge_page()`;
  - then `mod_node_page_state()` subtracts the size from
    `NR_SLAB_UNRECLAIMABLE_B` and `mod_lruvec_page_state()` adds it back, so
    the node is net zero and the memcg gains the size.
- Large kmalloc under a root objcg: `__memcg_kmem_charge_page()` returns 0
  without setting `memcg_data`; both updates hit the node only, net zero.
- Large kmalloc free: `free_large_kmalloc()` subtracts with
  `mod_lruvec_page_state()` before the page is uncharged in
  `__free_pages_prepare()`, so for a charged page node and memcg are both
  decremented.
- Caller in this tree: `__sk_charge()` in `net/core/sock.c`, which adds
  `__GFP_NOFAIL`.

## NUMA nodes and memory policy

**Policy-aware and node-specific allocation**

- There is no __alloc_pages_node() here; node-taking forms in
  `include/linux/gfp.h` are, for example, `alloc_pages_node()` and
  `__folio_alloc_node()`.
- `alloc_pages_node_noprof()` and `__folio_alloc_node_noprof()`: no
  `VM_BUG_ON()` or other range check on `nid`.
- `__alloc_pages()` and `__alloc_frozen_pages()`: declared in
  `mm/page_alloc.h`, not `include/linux/gfp.h`, and take a fifth argument
  `alloc_flags` (`ALLOC_DEFAULT` for ordinary callers).
- `alloc_pages_mpol()`: `static` in `mm/mempolicy.c`; the explicit-policy
  entry point is `folio_alloc_mpol()`.
- `alloc_pages()` and `folio_alloc()`: skip the task policy and use
  `default_policy` when `in_interrupt()` or when gfp has `__GFP_THISNODE`; see
  `alloc_frozen_pages_noprof()` in `mm/mempolicy.c`.
- `alloc_pages_bulk_mempolicy()`: task policy, same two exceptions.
- `alloc_pages_bulk()`: no policy, prefers `numa_mem_id()`.
- `vma_alloc_folio()`: uses the task policy when the VMA has none
  (`get_vma_policy()`).
- `vma_alloc_folio()` versus `folio_alloc()` at PMD order with
  `CONFIG_TRANSPARENT_HUGEPAGE`: for a policy that is neither interleave nor
  `MPOL_PREFERRED_MANY` and that allows the preferred node,
  `alloc_pages_mpol()` first tries that node with
  `__GFP_THISNODE | __GFP_NORETRY`, and returns NULL with no fallback if gfp
  lacks `__GFP_DIRECT_RECLAIM`; `folio_alloc()` passes `NO_INTERLEAVE_INDEX`
  and never does this.
- `NUMA_NO_NODE` handling, none of these apply a policy:

| Entry point | `nid == NUMA_NO_NODE` |
|---|---|
| `alloc_pages_node()`, `alloc_pages_bulk_node()` | becomes `numa_mem_id()` |
| `alloc_pages_nolock()` | becomes `numa_node_id()` |
| `__folio_alloc_node()`, `__folio_alloc()`, `__alloc_pages()`, `__alloc_frozen_pages()` | not mapped; with `CONFIG_NUMA`, `node_zonelist()` indexes `node_data[]` with it |

- `___kmalloc_large_node()`, and `alloc_slab_page()` in `mm/slub.c` when
  `allow_spin` is true: `NUMA_NO_NODE` goes to `alloc_frozen_pages_noprof()`
  (task policy), any other node to `__alloc_frozen_pages_noprof()` with a NULL
  nodemask; neither calls `alloc_pages()` or `__alloc_pages()`.
- Slab objects with `NUMA_NO_NODE`: `apply_strict_numa_policy()` substitutes
  `mempolicy_slab_node()` only when the static key `strict_numa` is on (boot
  parameter `slab_strict_numa`).
- `alloc_from_pcs()`: has no policy test of its own; in its object refill,
  `refill_objects()`, only `__refill_objects_any()` calls
  `mempolicy_slab_node()`, to pick the zonelist it walks.
- `warn_if_node_offline()`: only prints; the allocation proceeds.
- **Unsafe usage**: passing a nid that can be `NUMA_NO_NODE` to
  `__folio_alloc_node()`, `__folio_alloc()`, `__alloc_pages()` or
  `__alloc_frozen_pages()`; with `CONFIG_NUMA`, `node_zonelist()` indexes
  `node_data[]` with it and makes no test.
  - Safe: map it first, as `iommu_alloc_pages_node_sz()` does with
    `numa_mem_id()` and `alloc_migration_target()` does with
    `folio_nid(src)`.
  - Safe: `alloc_pages_node()`, which maps it itself.
- **Unsafe usage**: replacing a refcounted allocator with a frozen one, or the
  reverse, and leaving the free side unchanged; `put_page_testzero()` has a
  `VM_BUG_ON_PAGE()` on a zero refcount.
  - Safe: frozen allocation freed with `free_frozen_pages()`, as
    `___kmalloc_large_node()` and `free_large_kmalloc()` pair up.

**Node ids from outside**

- `do_pages_move()`: returns `-ENODEV` both for
  `node < 0 || node >= MAX_NUMNODES` and for `!node_state(node, N_MEMORY)`;
  it returns `-EINVAL` for neither and does not call `node_online()`.
- `do_pages_move()` cpuset test: `-EACCES` when the node is not in
  `cpuset_mems_allowed()` of the target task, which `find_mm_struct()`
  fetched; it is not `current->mems_allowed`.
- `node_state()`, `node_online()`, `node_possible()`: `test_bit()` on
  `node_states[]` with no bounds check, so the range test must come first.
- `numa_valid_node()` in `include/linux/numa.h`: the range test
  `nid >= 0 && nid < MAX_NUMNODES`; it rejects `NUMA_NO_NODE`.
- `MAX_NUMNODES` bounds `node_data[]` and `node_states[]`; an array allocated
  with `nr_node_ids` entries needs `nid < nr_node_ids`, as `compact_store()`
  in `mm/compaction.c` tests before `node_online()`.
- `numa_node_store()` in `drivers/pci/pci-sysfs.c`: accepts `NUMA_NO_NODE`,
  otherwise requires range and `node_online()`.
- Possible but offline node: `NODE_DATA()` is non-NULL on every architecture
  once `free_area_init()` in `mm/mm_init.c` has run; it calls
  `alloc_offline_node_data()` for each possible node whose entry is NULL.
- Possible but offline node, zonelists: `__build_all_zonelists()` builds them
  for every possible node; `ZONELIST_FALLBACK` holds the `N_MEMORY` nodes,
  `ZONELIST_NOFALLBACK` is empty.
- Node that is not possible: its `node_data[]` entry can be NULL, and
  `node_zonelist()` makes no NULL test.
- Without `CONFIG_NUMA`: `NODE_DATA()` returns `&contig_page_data` for any
  nid.
- `of_node_to_nid()` in `drivers/of/of_numa.c`: tests only
  `nid < MAX_NUMNODES && node_possible(nid)`, so the result can be offline.
- `numa_map_to_online_node()`: a macro in `include/linux/numa.h` for
  `numa_nearest_node(node, N_ONLINE)`; it passes `NUMA_NO_NODE` through, does
  no range check, and without `CONFIG_NUMA` returns `NUMA_NO_NODE` for every
  input.

**Iterating over nodes**

- There is no for_each_possible_node() here; `for_each_node()` iterates
  `N_POSSIBLE`.
- SLUB: `kmem_cache_init()` fills `slab_nodes` with
  `for_each_node_state(node, N_MEMORY)`, not `N_NORMAL_MEMORY`.
- Array indexed by any nid: iterate `for_each_node()` and choose the
  allocation node separately, as `hugetlb_cgroup_css_alloc()` does with
  `node_state(node, N_NORMAL_MEMORY) ? node : NUMA_NO_NODE`.
- Raw loop to `nr_node_ids`: can visit ids that are not possible, so each
  entry needs a test; `for_each_kmem_cache_node()` in `mm/slub.c` tests the
  pointer.
- `struct kmem_cache`: `per_node[]` is declared with `MAX_NUMNODES` entries
  but `kmem_cache_init()` sizes the cache for `nr_node_ids` entries, so
  indexing up to `MAX_NUMNODES` overruns the object.
- With `MAX_NUMNODES == 1`: `nr_node_ids` and `nr_online_nodes` are the
  macros `1U`, and `node_state()` is `node == 0`.
- `nr_node_ids`: `MAX_NUMNODES` until `setup_nr_node_ids()` runs, from
  `free_area_init()` or earlier from architecture NUMA setup, for example
  `setup_node_to_cpumask_map()` in `mm/arch_numa.c`.
- `N_POSSIBLE`: narrowed by architecture code during `setup_arch()`, for
  example `numa_register_meminfo()` in `mm/numa_memblks.c`.
- `N_MEMORY` and `N_NORMAL_MEMORY`: first set in `free_area_init()`, called
  from `mm_core_init_early()` right after `setup_arch()`.
- `N_CPU`: first set in `init_cpu_node_state()`, called from
  `init_mm_internals()`, long after the allocators are up.
- Before `free_area_init()`, with `CONFIG_NUMA`: `NODE_DATA()` of a node the
  architecture did not set up is NULL.
- Hotplug tracking: `register_node_notifier()` in `drivers/base/node.c` and
  the `hotplug_node_notifier()` macro in `include/linux/node.h`; both are
  stubs returning 0 unless `CONFIG_MEMORY_HOTPLUG` and `CONFIG_NUMA` are set.

**Memoryless nodes**

- `CONFIG_HAVE_MEMORYLESS_NODES`: defined only in `arch/powerpc/Kconfig`; on
  every other architecture `numa_mem_id()` is `numa_node_id()` and
  `cpu_to_mem()` is `cpu_to_node()`, so both can return a memoryless node.
- `get_node()`: returns `s->per_node[node].node`.
- `slab_nodes`: filled from `N_MEMORY`, not `N_NORMAL_MEMORY`, in
  `kmem_cache_init()`, and extended by `slab_mem_going_online_callback()` on
  `NODE_ADDING_FIRST_MEMORY`.
- `slab_nodes` bits are never cleared, so a node that lost its memory keeps a
  non-NULL `struct kmem_cache_node`.
- `get_from_partial_node()`: takes the `struct kmem_cache_node *`, not a nid,
  and returns NULL on `!n || !n->nr_partial`; `get_partial_node_bulk()` has
  the same test.
- `get_from_partial()`: maps `NUMA_NO_NODE` to `numa_mem_id()` and passes
  `get_node()` of that straight in, relying on the NULL test above.
- `___slab_alloc()`: does not rewrite a requested node that lacks a
  `struct kmem_cache_node`; it tries the node with `__GFP_THISNODE` added,
  then retries with the caller's flags, which lets the page allocator fall
  back.
- Caller's `__GFP_THISNODE` with a requested memoryless node:
  `get_from_partial()` returns NULL without trying other nodes, and
  `new_slab()` keeps the flag (`GFP_CONSTRAINT_MASK`).
- **Potentially unsafe usage**: dereferencing the result of `get_node()` with
  no NULL test.
  - Unsafe: when the nid comes from `numa_node_id()`, from a caller's node
    argument, or from `numa_mem_id()` on an architecture without
    `CONFIG_HAVE_MEMORYLESS_NODES`; the pointer is NULL for a node that never
    had memory.
  - Safe: when the nid is `slab_nid()` of an allocated slab, as in
    `inc_slabs_node()`; `slab_mem_going_online_callback()` installs the
    structure before the node's memory can be allocated.
  - Safe: after a NULL test, as `get_from_partial_node()` does.

## Model gaps

### Other mistakes models make

- Models take __GFP_NO_OBJ_EXT to stop recursion inside slab. There is no
  such gfp bit here; for a sheaf of a kmalloc cache `__alloc_empty_sheaf()` in
  `mm/slub.c` passes the slab alloc flag `SLAB_ALLOC_NO_RECURSE` (`mm/slab.h`)
  through `kmalloc_flags()`.
- Models take every allocation call to carry an explicit GFP argument.
  `kmalloc_obj()`, `kzalloc_obj()`, `kvmalloc_obj()`, `kvzalloc_obj()` and
  their array and flex forms in `include/linux/slab.h` use `default_gfp()`
  (`include/linux/gfp.h`), which gives `GFP_KERNEL` when the argument is left
  out.
- Models take the zonelist walk to use the first zone that passes its
  watermark. With more than one online node, `get_page_from_freelist()` first
  skips nodes whose kswapd is not asleep on `kswapd_wait`, and retries
  without the skip only if that pass found nothing.
