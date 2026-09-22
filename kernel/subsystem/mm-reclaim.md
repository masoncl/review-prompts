# MM Reclaim, Swap, and Migration

## Writeback Tags

Incorrect tag handling causes data loss (dirty pages skipped during sync) or
writeback livelock (sync never completes because new dirty pages keep appearing).
Review any code that starts writeback or implements `->writepages`.

Page cache tags defined as `PAGECACHE_TAG_*` in `include/linux/fs.h`:

| Tag | XA Mark | Purpose |
|-----|---------|---------|
| PAGECACHE_TAG_DIRTY | XA_MARK_0 | Folio has dirty data needing writeback |
| PAGECACHE_TAG_WRITEBACK | XA_MARK_1 | Folio is currently under IO |
| PAGECACHE_TAG_TOWRITE | XA_MARK_2 | Folio tagged for current writeback pass |

**Tag lifecycle:**
1. `folio_mark_dirty()` calls `mapping->a_ops->dirty_folio`.
   `filemap_dirty_folio()` and `block_dirty_folio()` set PAGECACHE_TAG_DIRTY
   through `__folio_mark_dirty()`; `noop_dirty_folio()` sets no tag
2. `tag_pages_for_writeback()` in `mm/page-writeback.c` copies DIRTY to TOWRITE
   for data-integrity syncs, preventing livelocks from new dirty pages
3. `folio_start_writeback()` (macro for `__folio_start_writeback(folio, false)`,
   defined in `include/linux/page-flags.h`):
   - Sets PAGECACHE_TAG_WRITEBACK
   - Clears PAGECACHE_TAG_DIRTY if the folio's dirty flag is not set
   - Clears PAGECACHE_TAG_TOWRITE (because `keep_write` is false)
4. To preserve PAGECACHE_TAG_TOWRITE, call `__folio_start_writeback(folio, true)`

**Tag selection** (see `wbc_to_tag()` in `include/linux/writeback.h`):
- `wbc_to_tag()` returns PAGECACHE_TAG_TOWRITE for `WB_SYNC_ALL` or
  `tagged_writepages` mode, PAGECACHE_TAG_DIRTY otherwise
- Data-integrity syncs (`WB_SYNC_ALL`) iterate TOWRITE so pages dirtied after
  the sync starts are not included

## Cgroup Writeback Domain Abstraction

Code receiving a `dirty_throttle_control *dtc` must use `dtc_dom(dtc)` for the
domain, not `global_wb_domain` directly. `balance_dirty_pages()` in
`mm/page-writeback.c` selects between global (`gdtc`) and memcg (`mdtc`)
domains based on `pos_ratio`; hardcoding global values produces wrong
throttling when the memcg domain is selected.

**REPORT as bugs**: `global_wb_domain` field access in functions/traces that
receive a `dtc` parameter, except code that intentionally uses the global
value: the rt/dl task boost in `domain_dirty_limits()`, which adds
`global_wb_domain.dirty_limit / 32` for both domains, and the
`global_dirty_state` tracepoint, which is only emitted for the global dtc.
Tracepoints cannot call the static `dtc_dom()`; they should use fields already
computed in the dtc (e.g. `dtc->limit`).

## Swap Cache Residency

A folio enters the swap cache via `folio_alloc_swap()` during reclaim and
remains until explicitly removed. `folio_free_swap()` in `mm/swapfile.c`
removes it only when `folio_swapcache_freeable(folio)` (swapcache, not under
writeback, storage not suspended) AND `!folio_maybe_swapped(folio)` (no slot
covered by the folio has a swap count above zero). `folio_maybe_swapped()` may
return true spuriously if a count is dropped concurrently, so
`folio_free_swap()` errs toward keeping the cache.

**Large folio swapin conflicts:** `swap_cache_alloc_folio()` in
`mm/swap_state.c` checks the range with `__swap_cache_add_check()`. It returns
`-ENOENT` when the target slot is no longer swapped out (abort), `-EEXIST`
when the target slot already has a folio (callers that want the folio, such as
`swapin_sync()` and `swap_cache_read_folio()`, look the cache up again), and
gets `-EBUSY` when another slot of a large range is cached, freed, or differs
in zero-flag or memcg. It handles `-EBUSY` / `-ENOMEM` itself by stepping down
through the remaining `orders`. A caller that passes a single large order must
retry at order 0 (see `shmem_swap_alloc_folio()` in `mm/shmem.c`); callers
that pass `BIT(0)` cannot see `-EBUSY`. Retrying the same order on `-EBUSY`
can loop forever, because readahead or concurrent swapin can keep order-0
entries in the cache.

**Swap entry reuse (ABA problem):** swap entries are recycled -- the same
`swp_entry_t` can be reassigned to a different folio. `pte_same()` on swap
PTEs only confirms the entry value, not folio identity. After locking a folio
from `swap_cache_get_folio()` on a swap entry, verify
`folio_test_swapcache(folio)` and `folio->swap.val` still match. After
acquiring the PTE lock when an earlier lookup returned NULL, check
`swap_cache_has_folio(entry)` again. See `move_swap_pte()` in
`mm/userfaultfd.c`.

## Swap Device Lifetime

Accessing a `struct swap_info_struct` without stabilising the device allows
`swapoff` to free its cluster info, swap tables and other sub-structures
concurrently, causing use-after-free (the `struct swap_info_struct` itself is
never freed). `swapoff()` calls `percpu_ref_kill()` on `si->users` followed by
`synchronize_rcu()` before freeing structures.

- `get_swap_device(entry)` in `mm/swapfile.c` validates the entry and takes a
  `percpu_ref` on `si->users`. Returns NULL if the device is being swapped off.
  Must be paired with `put_swap_device(si)` (in `include/linux/swap.h`)
- `__swap_entry_to_info(entry)` in `mm/swap.h` returns the
  `struct swap_info_struct` pointer WITHOUT taking a reference -- only safe
  when the device is already stabilised: the caller holds a
  `get_swap_device()` reference, holds the lock of a folio that is in the swap
  cache for that entry, holds a lock protecting a reference to the entry (e.g.
  the PTL), or is in an RCU read-side section (see the comment above
  `swap_cache_has_folio()` in `mm/swap.h`; the RCU case is in the comment above
  `get_swap_device()` in `mm/swapfile.c`). The locked swap-cache folio case is
  the most common in-tree use. The path that would free the device needs none
  of these: swapoff's own `try_to_unuse()` runs before `percpu_ref_kill()`, and
  hibernation pins the device with `SWP_HIBERNATION`
- `swap_cache_alloc_folio()` in `mm/swap_state.c` uses
  `__swap_entry_to_cluster()` internally without pinning the device. Callers
  must protect the device with a reference or one of the locks above. All
  current callers hold a device reference, except the swapoff path
  (`try_to_unuse()` → `swapin_readahead()`), which needs none
- **Cross-device readahead hazard**: readahead code that iterates page table
  entries (VMA readahead) may encounter swap entries from different devices than
  the target. The caller typically holds a device reference only for the target
  entry's device. Each entry from a different device must be separately pinned
  with `get_swap_device()` or skipped on failure (see `swap_vma_readahead()` in
  `mm/swap_state.c`)

## Dual Reclaim Paths: Classic LRU vs MGLRU

`mm/vmscan.c` has two parallel reclaim implementations that must maintain
identical vmstat, memcg event, and tracepoint coverage. MGLRU is runtime-
selectable, so bugs only manifest when the other path is active.

- Classic: `shrink_inactive_list()` / `shrink_active_list()`
- MGLRU: `evict_folios()` / `scan_folios()`

Both call `shrink_folio_list()` but each has its own post-reclaim stat
updates. When modifying vmstat counters, memcg events, or tracepoints in
one function, verify the corresponding change in the other. The pairing
depends on the counter: steal, demote and rotate accounting and
`mm_vmscan_lru_shrink_inactive` pair `shrink_inactive_list()` with
`evict_folios()` (both call the shared `handle_reclaim_writeback()` for the
writeback-stall part); the per-reclaimer scan counters (`PGSCAN_KSWAPD`,
`PGSCAN_DIRECT`, `PGSCAN_KHUGEPAGED`, `PGSCAN_PROACTIVE`), `PGSCAN_ANON` /
`PGSCAN_FILE`, `PGSCAN_SKIP` and `mm_vmscan_lru_isolate` pair
`shrink_inactive_list()` / `isolate_lru_folios()` with `scan_folios()`;
`PGREFILL` pairs `shrink_active_list()` with `scan_folios()`.

## MGLRU Generation and Tier Bit Consistency

When a folio moves to a new generation, its tier bits (`LRU_REFS_FLAGS`,
defined as `LRU_REFS_MASK | BIT(PG_referenced)` in `include/linux/mmzone.h`)
must be cleared so tier tracking starts fresh. Stale tier bits inflate access
counts and distort eviction. Paths that move a folio that stays on the LRU to
another generation must also clear `LRU_REFS_FLAGS` via
`old_flags & ~(LRU_GEN_MASK | LRU_REFS_FLAGS)`. This is done in
`folio_update_gen()` and `folio_inc_gen()` in `mm/vmscan.c`.
`lru_gen_add_folio()` and `lru_gen_del_folio()` in
`include/linux/mm_inline.h` put a folio on and take it off the LRU; they
rewrite `LRU_GEN_MASK` (add also clears `BIT(PG_active)`) and deliberately
preserve the refs bits. That is correct and must not be reported.

**Review any code that moves a folio between generations** to verify it also
handles `LRU_REFS_FLAGS`.

## Shmem Folio Cache Residency

Confusing `folio_test_swapbacked()` with `folio_test_swapcache()` causes
xarray or swap table corruption, incorrect VM statistics accounting, and wrong
branching in migration and reclaim paths, because shmem folios can be in
two different cache states that require different handling.

**The three folio cache states for shmem:**

| State | `swapbacked` | `swapcache` | `folio->mapping` | where the entries live |
|-------|-------------|-------------|-------------------|-----------------|
| Shmem in page cache | true | false | shmem inode `struct address_space` | `mapping->i_pages` (single multi-order entry) |
| Shmem in swap cache | true | true | NULL | swap table of the entry's cluster (`ci->table`, N slots, under `ci->lock`) |
| Anonymous in swap cache | true | true | `struct anon_vma` (with `FOLIO_MAPPING_ANON` flag); NULL for a folio just read into the swap cache that has no rmap yet | swap table of the entry's cluster (`ci->table`, N slots, under `ci->lock`) |

A shmem folio is in either the page cache or the swap cache, never both once
the folio is unlocked. The transitions in `shmem_writeout()` and
`shmem_swapin_folio()` hold the folio lock while it is briefly in both. Once
moved to swap cache, `folio->mapping` is set to NULL and the folio is no longer
associated with the shmem inode mapping.

**`folio_test_swapbacked()` vs `folio_test_swapcache()`:**
- `folio_test_swapbacked()` tests `PG_swapbacked`: true for shmem folios (both
  page-cache-resident and swap-cache-resident) and for anonymous folios except
  lazyfree (`MADV_FREE`) ones, which are anon with `PG_swapbacked` cleared
  (`folio_test_lazyfree()`). It indicates the folio *can use* swap as backing
  storage
- `folio_test_swapcache()` tests both `PG_swapbacked` AND `PG_swapcache`:
  true only when the folio is *currently in* the swap cache
- Using `folio_test_swapbacked()` as a proxy for "is in swap cache" is
  wrong because it also matches shmem folios that are in the page cache

**Storage models:**
- **Page cache** (`mapping->i_pages`): stores a single multi-order xarray
  entry for a large folio. Operations use `xas_store()` once
- **Swap cache**: not an xarray. It is the per-cluster swap table (see
  `mm/swap_table.h` and `Documentation/mm/swap-table.rst`), one slot per
  subpage, modified under the cluster lock through the `swap_cache_*()` /
  `__swap_cache_*()` helpers. `swap_space` in `mm/swap_state.c` (what
  `swap_address_space()` and `folio_mapping()` return for a swap-cache folio)
  is a dummy `struct address_space` with nothing in `i_pages`; it only supplies
  `a_ops` for `shrink_folio_list()`, `folio_mark_dirty()` and migration

Code that branches between page-cache xarray operations and swap-cache
swap-table operations must use `folio_test_swapcache()`, not
`folio_test_swapbacked()`. See `__folio_migrate_mapping()` in
`mm/migrate.c` which uses `folio_test_swapcache()` to select the
swap-cache-specific replacement path (`__swap_cache_replace_folio()`).

## Memcg Charge Lifecycle

Every `mem_cgroup_charge()` must have a corresponding `mem_cgroup_uncharge()`
on the free path. On migration, charge transfers via `mem_cgroup_migrate()` --
the old folio is NOT uncharged separately. `folio_unqueue_deferred_split()`
must precede uncharging to avoid accessing freed memcg data.

**Memcg lookup safety:**
- `folio_memcg()` returns NULL for uncharged folios. `memcg_data` holds an
  objcg; when a memcg goes offline `memcg_reparent_objcgs()` redirects its
  objcgs to the parent, node by node, and the LRU lists are spliced across
  under the same locks. `folio_memcg()` can therefore return a dying memcg
  only in the window before that node is reparented. A pointer read under RCU
  in that window may, by the time it is used, belong to a memcg whose private
  ID was already released, which is why swap accounting resolves it through
  `mem_cgroup_private_id_get_online()`
- Operations that charge/record/uncharge must all use the same memcg, the one
  resolved by `mem_cgroup_private_id_get_online()`, whose private ID is still
  live. Refactorings replacing an explicit memcg parameter with
  `folio_memcg()` introduce a mismatch (counter targets online ancestor,
  recorded ID is the offline memcg), causing permanent counter leaks when
  cgroups are deleted under pressure
- `mem_cgroup_from_private_id()` returns an RCU-protected pointer valid only
  under `rcu_read_lock()`. Use `mem_cgroup_tryget()` before `rcu_read_unlock()`
  to extend lifetime. `get_mem_cgroup_from_*()` functions acquire a reference
  internally

**Per-CPU stock drain:** charges are batched in per-CPU stocks that cache
a memcg pointer. Each cached entry holds a reference that pins the memcg
— search near the per-CPU charge-caching code to find the acquire that
pins the pointer when it is cached and the release that drops it when the
stock is drained. Destroying a memcg drains those stocks to flush charges
and drop the reference — without the drain the cached pointer simply keeps
the memcg alive until a later drain, deferring its freeing; the reference
makes this a delayed free, not a use-after-free. Cgroup removal itself
proceeds, the object just lingers until drained.

## Folio Migration and Sleeping Constraints

`folio_mc_copy()` in `mm/util.c` calls `cond_resched()` between pages -- safe
for order-0 (loop exits before resched) but sleeps for large folios. This
makes `filemap_migrate_folio()` / `migrate_folio()` / `__migrate_folio()`
sleeping operations for large folios.

**REPORT as bugs**: `migrate_folio` callbacks (in
`struct address_space_operations`) that hold a spinlock while calling these
functions. Use non-blocking state flags instead (e.g., `BH_Migrate` in
`__buffer_migrate_folio()` in `mm/migrate.c`).

## Folio Isolation for Migration

Not every folio that qualifies for migration is added to the isolation list:
device-coherent folios skip it, `folio_isolate_lru()` can fail, etc.
`collect_longterm_unpinnable_folios()` in `mm/gup.c` returns a count of all
unpinnable folios, not just those listed.

**REPORT as bugs**: using `list_empty()` on a migration list as proxy for
"no qualifying items" when the collection has early-continue paths. Use an
explicit count instead.

## Quick Checks

- **Bounded iteration under LRU locks**: skipping LRU entries without
  advancing the termination counter creates unbounded spinlock-held scans.
  Skip paths must either advance the counter or have an independent bound
  (e.g., `SWAP_CLUSTER_MAX_SKIPPED`). Applies to any spinlock-held list
  filtering loop
- **Migration lock scope across unmap and remap phases**: if `TTU_RMAP_LOCKED`
  is passed to `try_to_migrate()`, `i_mmap_rwsem` must stay held until
  `remove_migration_ptes()`, which takes the same flag. Dropping between phases
  creates ABBA deadlock (`folio_lock` → `i_mmap_rwsem` vs reverse). Anon vs
  file-backed use different locks — fixes for one may break the other. See
  `unmap_and_move_hugetlb_folio()` in `mm/migrate.c`
- **kswapd order-dropping and watermark checks**: `kswapd_shrink_node()`
  drops `sc->order` to 0 after reclaiming `compact_gap(order)` pages. Watermark
  checks in `pgdat_balanced()`/`balance_pgdat()` that use stricter high-order
  metrics must check `order != 0`, not a static mode flag. Ignoring the
  dynamic order drop causes massive overreclaim
- **`folio_putback_lru()` requires valid memcg**: after
  `mem_cgroup_migrate()` clears the source folio's `memcg_data`,
  `folio_putback_lru()` triggers a memcg assert. Use plain `folio_put()`
  for the source folio. See `migrate_folio_done()`, called from
  `migrate_folio_move()` in `mm/migrate.c`
- **Swap allocator local lock scope**: the allocator part of
  `folio_alloc_swap()` (`swap_alloc_fast()` / `swap_alloc_slow()` and
  everything they call) runs under `local_lock(&percpu_swap_cluster.lock)`.
  Nothing reachable there may sleep without dropping it first (see
  `swap_cluster_populate()`). Code after the `local_unlock()` in
  `folio_alloc_swap()` may sleep (`swap_sync_discard()`). A sleeping call under
  the local lock is usually silent unless it really blocks;
  `CONFIG_DEBUG_ATOMIC_SLEEP` or `CONFIG_PROVE_LOCKING` catch it on every call
- **Zone skip criteria consistency in vmscan**: zone-skip logic must be
  consistent across `balance_pgdat()`, `pgdat_balanced()`,
  `allow_direct_reclaim()`, and `skip_throttle_noprogress()`. If one counts a
  zone another skips, `kswapd_failures` escape hatch may never fire, causing
  infinite loops in `throttle_direct_reclaim()`
- **Counter-gated tracking list removal**: list membership gated by a
  resource counter (e.g., `shmem_swaplist` requires `info->swapped > 0`).
  Error paths must check the counter before `list_del_init()` — the object
  may already be on the list from a prior operation. Unconditional removal
  causes iterators to loop forever unable to find remaining resources
- **List iteration with lock drop**: `list_for_each_entry_safe()` is not safe
  when the lock is dropped mid-iteration. Concurrent `list_del_init()` makes
  the element self-referential → infinite loop. After reacquiring, check
  `list_empty()` and restart from head. See `shmem_unuse()` in `mm/shmem.c`
