# MM Reclaim, Swap, and Migration

## Main structures

### Objects and how they relate

- Reclaim writeback: `pageout()` in `mm/vmscan.c` writes only shmem folios
  (`shmem_writeout()`) and anon swap-cache folios (`swap_writeout()`).
- Dirty file-LRU folio in `shrink_folio_list()`: gets `folio_set_reclaim()` and
  goes to `activate_locked`; reclaim never writes it. `mm/vmscan.c` makes no
  `writepages` call.
- `struct mem_cgroup_per_node`: holds the lruvec and one `objcg` per memcg per
  node.
- Memcg offline: `mem_cgroup_css_offline()` calls `memcg_reparent_objcgs()`,
  which splices the child's LRU lists into the parent's lruvec
  (`lru_reparent_memcg()` or `lru_gen_reparent_memcg()`) and repoints the
  objcgs to the parent, per node, under both `lru_lock`s.
- Folio and lruvec: a folio is on at most one lruvec. It is on none while
  isolated or while it sits in the per-CPU `lru_add` batch of
  `struct cpu_fbatches`; the other batches there do not take a folio off its
  list.
- Unevictable folio: counted in its lruvec but not linked on a list; see
  `lruvec_add_folio()` in `include/linux/mm_inline.h`.
- `struct lruvec`: holds `lists` and, with `CONFIG_LRU_GEN`, `lrugen`. Which
  one takes a folio is chosen at run time, per lruvec, by `lrugen->enabled`,
  not by `CONFIG_LRU_GEN` alone.
- `struct lru_gen_memcg` (`memcg_lru` in `struct pglist_data`): per-node list
  of the memcgs' `struct lru_gen_folio`. MGLRU root reclaim picks memcgs from
  it in `shrink_many()`, which does not call `mem_cgroup_iter()`;
  `shrink_node_memcgs()` does.
- MGLRU names: `struct lru_gen_folio`, `struct lru_gen_mm_state`,
  `struct lru_gen_mm_walk`, `struct lru_gen_memcg` are in
  `include/linux/mmzone.h`; `struct lru_gen_mm_list` is in
  `include/linux/mm_types.h`.
- Swap cache: is the set of PFN words in the swap tables, not an xarray.
  `swap_space` in `mm/swap_state.c` is a single placeholder
  `struct address_space` that `folio_mapping()` returns for swap-cache folios.
- `swap_cache_get_folio()`: lockless lookup that returns the folio unlocked; a
  caller that maps the folio or reads `folio->swap` must first lock it and
  recheck that it still serves the entry, normally with
  `folio_matches_swap_entry()`.
- `folio_dup_swap()`: called under the folio lock, for example from
  `ttu_anon_swapbacked_folio()` in `mm/rmap.c`; it warns
  (`VM_WARN_ON_FOLIO()`) when the folio is not locked or not in the swap
  cache.
- Slot data: is in one of four places: the swap cache folio, zswap, the device,
  or nowhere when the slot is zero-filled.
- `softleaf_t`: the name for a non-present page table entry value; today an
  alias of `swp_entry_t`. `softleaf_type()` in `include/linux/leafops.h` tells
  swap, migration, device, hwpoison and marker entries apart.
- Entry helpers: there is no is_migration_entry(), non_swap_entry() or
  pte_to_swp_entry() here; `softleaf_is_migration()`, `softleaf_is_swap()` and
  `softleaf_from_pte()` do those jobs.
- `migrate_pages()`: a function in `mm/migrate.c`; there is no struct of that
  name.
- `struct memory_tier`: private to `mm/memory-tiers.c`. `mm/vmscan.c` calls
  only `next_demotion_node()` and `node_get_allowed_targets()` from it.

## Where to look

**Core files**

| Job | File in this tree | Not where expected |
|---|---|---|
| LRU batching, activation, `lru_add_drain()`, `release_pages()` | `mm/folio.c` | There is no mm/swap.c. |
| Multi-generation LRU | `mm/vmscan.c` | `lru_gen_eviction()` and `lru_gen_refault()` are in `mm/workingset.c`; `lru_gen_inc_refs()` and `lru_gen_clear_refs()` are in `mm/folio.c`. |
| Shrinkers | `mm/shrinker.c` | `shrink_slab()` is defined here; `mm/vmscan.c` calls it and, of the slab code, defines only `drop_slab()` and `drop_slab_node()`. |
| Swap slot allocator | `mm/swapfile.c` | No mm/swap_slots.c, no include/linux/swap_slots.h. `struct swap_info_struct` has no swap_map member; the per-slot count is in the swap table entry, see `__swp_tb_get_count()` in `mm/swap_table.h`. |
| Swap cache | `mm/swap_state.c` | One `swap_space` for all devices. |
| Swap table (stores the swap cache) | `mm/swap_table.h` | Header only, no mm/swap_table.c. One table per cluster: `table` in `struct swap_cluster_info`, `mm/swap.h`. Allocated and freed by `swap_cluster_alloc_table()` and `swap_cluster_free_table()` in `mm/swapfile.c`. |
| Swap I/O | `mm/page_io.c` | Back ends are `struct swap_ops` in `include/linux/swap_ops.h`: `swap_bdev_ops` is the default on every device; a filesystem installs its own with `swap_fs_activate()`. There is no swap_rw address-space operation. |
| zswap | `mm/zswap.c` | Calls `zs_malloc()` in `mm/zsmalloc.c` directly; no zpool layer exists, neither mm/zpool.c nor include/linux/zpool.h. |
| Memory cgroup charge code | `mm/memcontrol.c` | cgroup v1 code is in `mm/memcontrol-v1.c` under `CONFIG_MEMCG_V1`. |
| Memory cgroup owner of a swap slot | `mm/swap_table.h` | No mm/swap_cgroup.c, no include/linux/swap_cgroup.h. The id is in `struct swap_memcg_table`, written by `__swap_cgroup_set()` from `__mem_cgroup_try_charge_swap()` in `mm/memcontrol.c`. |

## Shrinking a folio list

**Exit paths and step order**

- `keep`: its `VM_BUG_ON_FOLIO()` fires on `folio_test_lru()` or
  `folio_test_unevictable()`; the `folio_test_active()` assertions are after
  the hwpoison check and at `activate_locked`.
- `activate_locked`: `folio_set_active()`, `stat->nr_activate[]` and
  `PGACTIVATE` happen only when `folio_test_mlocked()` is false; an mlocked
  folio goes back unactivated.
- `activate_locked`: a swap-cache folio gets `folio_free_swap()` when
  `mem_cgroup_swap_full()` or `folio_test_mlocked()`; otherwise it stays in
  the swap cache.
- `activate_locked_split`: only sets `nr_pages` to 1 and subtracts the rest
  from `sc->nr_scanned`; it does not split and counts no fallback.
- `activate_locked_split` is reached only from a failed `folio_alloc_swap()`
  on a folio that is not large; a failed `split_folio_to_list()` goes to
  `activate_locked` with the folio still large.
- `shrink_folio_list()` has no lazyfree label and no `walk_done` label; a
  lazyfree folio is handled inline: `folio_ref_freeze(folio, 1)` fails to
  `keep_locked`, succeeds to the unlock before `free_it`.
- `free_it` has a third producer: a folio with buffers and no mapping, after
  `filemap_release_folio()`, is unlocked and `folio_put_testzero()` jumps
  there.
- Failed `folio_put_testzero()` in that branch: adds `nr_pages` to
  `nr_reclaimed` and does `continue` with the folio on no list; the holder of
  the other reference frees it.
- hwpoisoned large folio: `keep_locked`; only a small one takes the
  `unmap_poisoned_folio()`, `folio_put()`, `continue` exit.
- Folios that `demote_folio_list()` could not move: spliced back onto
  `folio_list` and the loop reruns from `folio_trylock()` with
  `do_demote_pass` false; with `sc->proactive` there is no rerun and they are
  returned to the caller.
- Swap step before unmap: `ttu_anon_folio()` in `mm/rmap.c` warns and fails
  the unmap of an anon folio whose `folio_test_swapbacked()` and
  `folio_test_swapcache()` differ.
- `keep_locked` and `keep` undo no earlier step: after a split the tails are
  already on `folio_list`; after `folio_alloc_swap()` the folio stays in the
  swap cache, dirty, on `keep_locked` (as the `may_enter_fs()` failure does).

**Page table reference check**

- `enum folio_references` in `mm/vmscan.c` has three values:
  `FOLIOREF_RECLAIM`, `FOLIOREF_KEEP`, `FOLIOREF_ACTIVATE`; there is no
  FOLIOREF_RECLAIM_CLEAN.
- No reference, classic LRU: `FOLIOREF_RECLAIM` whether or not
  `PG_referenced` was set; the flag is cleared by
  `folio_test_clear_referenced()`.
- `folio_referenced()` fills a `vma_flags_t`; the tests are
  `vma_flags_test()` on `VMA_LOCKED_BIT` and, in `is_exec_file_folio()`, on
  `VMA_EXEC_BIT`.
- Return value of `folio_referenced()`: counts VMAs that referenced the
  folio, not PTEs; "more than once" means more than one VMA.
- Classic LRU, swap-backed anon folio, one reference, `PG_referenced` clear:
  `FOLIOREF_KEEP`, same as a non-exec file folio.
- Return of -1 has two causes: rmap lock contention (`rwc.contended`), or
  `folio_referenced_one()` found a non-shared swap-backed anon folio mapped
  by an exiting or OOM-reaped mm. Both give `FOLIOREF_KEEP`.
- `VMA_LOCKED_BIT` is tested before the -1 test, so it wins.
- Zero can hide references: `invalid_folio_referenced_vma()` skips VMAs
  without `vma_has_recency()` and, under cgroup reclaim, VMAs of an mm
  outside `sc->target_mem_cgroup`.
- MGLRU branch: taken when `lru_gen_enabled() && !lru_gen_switching()`;
  while switching, the classic rules apply.
- MGLRU, any reference: the count is ignored and `lru_gen_set_refs()`
  decides:

| Folio flags on entry | Result |
|---|---|
| neither `PG_referenced` nor `PG_workingset`, exec file folio | sets `PG_workingset`, `FOLIOREF_ACTIVATE` |
| neither flag, any other folio | sets `PG_referenced`, `FOLIOREF_KEEP` |
| either flag set | `FOLIOREF_ACTIVATE` |

**Dirty folios in reclaim**

- `struct address_space_operations` has no writepage member; `pageout()`
  calls `shmem_writeout()` or `swap_writeout()` directly.
- There is no writeout() or is_page_cache_freeable() helper; the refcount
  test, `folio_set_reclaim()` and its clearing are inline in `pageout()`.
- Dirty file-LRU folio: the `NR_VMSCAN_IMMEDIATE`, `folio_set_reclaim()`,
  `activate_locked` branch is unconditional; there is no kswapd test and no
  PGDAT_DIRTY flag.
- Flusher wakeup: in `handle_reclaim_writeback()`, called from
  `shrink_inactive_list()` and from `evict_folios()`.
- `swap_writeout()` returns 0 with no I/O and no writeback when
  `folio_free_swap()` succeeds, the folio is zero-filled, or `zswap_store()`
  takes it; `pageout()` then clears `PG_reclaim`.
- After the zero-filled and `zswap_store()` cases the folio is clean and can
  be freed in the same pass; after `folio_free_swap()` it is dirty and goes
  to `keep`.
- `swap_writeout()` returns `AOP_WRITEPAGE_ACTIVATE`, folio redirtied and
  still locked, when `zswap_store()` failed and
  `mem_cgroup_zswap_writeback_enabled()` is false.
- `shmem_writeout()` returns `AOP_WRITEPAGE_ACTIVATE`, folio redirtied and
  locked, at its `redirty` label: for example `SHMEM_F_LOCKED`, `noswap`, no
  swap pages, or a failed split.
- `shmem_writeout()` success: the folio has moved from the page cache to the
  swap cache, so `folio_mapping()` changes across `pageout()`.

**Folios under writeback**

- `writeback_throttling_sane()`: true for global reclaim
  (`sc->target_mem_cgroup` NULL); for cgroup reclaim, true only on cgroup v2
  built with `CONFIG_CGROUP_WRITEBACK`; always true without `CONFIG_MEMCG`.
- Case 2 has four alternatives: `writeback_throttling_sane()`,
  `!folio_test_reclaim()`, `!may_enter_fs()`, or a non-NULL mapping with
  `mapping_writeback_may_deadlock_on_reclaim()`
  (`AS_WRITEBACK_MAY_DEADLOCK_ON_RECLAIM`).
- Case 2 does not test `current_is_kswapd()`; only case 1 does.
- Wait (case 3) needs all of: cgroup reclaim without sane throttling,
  `PG_reclaim` already set, `may_enter_fs()` true, mapping not flagged.
- `may_enter_fs()` false prevents the wait; it never causes it.
- `may_enter_fs()`: there is no SWP_FS_OPS; with only `__GFP_IO` a swap-cache
  folio passes unless the device's `ops->flags` has
  `SWAP_OPS_F_REQUIRE_NOFS`. It makes no `PG_private` test.
- `stat->nr_immediate`: summed into `sc->nr.immediate` by
  `handle_reclaim_writeback()`; the stall is
  `reclaim_throttle(pgdat, VMSCAN_THROTTLE_WRITEBACK)` in `shrink_node()`,
  for kswapd only.
- `PGDAT_WRITEBACK`: set by kswapd in `shrink_node()` when
  `sc->nr.writeback` is non-zero and equals `sc->nr.taken`.

**Anonymous folios to swap**

- Checks before allocation: `sc->gfp_mask & __GFP_IO` and
  `folio_maybe_dma_pinned()`, both to `keep_locked`; this block does not test
  `sc->may_swap` or `total_swap_pages`.
- Lazyfree folios: kept out of this block by its `folio_test_swapbacked()`
  entry test; it does not call `folio_test_lazyfree()`.
- Large folio split test: there is no can_split_folio(); the code compares
  `folio_expected_ref_count(folio)` with `folio_ref_count(folio) - 1` and
  goes to `activate_locked` on a mismatch.
- `folio_alloc_swap()` in `mm/swapfile.c` takes only the folio; there is no
  add_to_swap().
- `folio_alloc_swap()` on a large folio without `CONFIG_THP_SWAP`: returns
  `-EAGAIN` at once, so every large folio takes the split fallback.
- `folio_alloc_swap()` success: the folio is in the swap cache, which holds
  one reference per page; the slots have swap count zero.
- `folio_mark_dirty()` after success: needed because a `MADV_FREE` folio can
  have clean PTEs while `PG_swapbacked` is set; unmap would leave it clean,
  the dirty test would skip `pageout()`, and `__remove_mapping()` would free
  it unwritten.

**Detaching from the mapping**

- Page-cache folio: `spin_lock(&mapping->host->i_lock)`, then
  `xa_lock_irq(&mapping->i_pages)`.
- Swap-cache folio: only the swap cluster lock, through
  `swap_cluster_get_and_lock_irq()` in `mm/swap.h`; no `i_lock`, no
  `i_pages` lock.
- IRQ-off form of the cluster lock: `__memcg1_swapout()` runs under it and
  relies on interrupts being disabled.
- Freeze count: `1 + folio_nr_pages(folio)` for both kinds of folio.
- `i_lock` is held for `inode_lru_list_add()`; there is no inode_add_lru().

**Reference count at removal**

- Swap-cache path, in order under the cluster lock: `workingset_eviction()`,
  `__memcg1_swapout()`, `__swap_cache_del_folio()`, unlock; there is no
  put_swap_folio() and no __delete_from_swap_cache().
- `workingset_eviction()` must precede `__memcg1_swapout()`, which clears
  `folio->memcg_data` under `do_memsw_account()`; `lru_gen_eviction()` reads
  `folio_memcg()`.
- Swap slot without a shadow: not cleared; `__swap_cache_do_del_folio()`
  stores `shadow_to_swp_tb(NULL, flags)`, an empty shadow-format entry that
  keeps the old entry's flags field (`__swp_tb_get_flags()`: swap count and
  inline zero flag).
- Large swap-cache folio: every one of its slots gets the same shadow value.
- Slots whose swap count is zero: reset to NULL by
  `__swap_cluster_free_entries()` in the same call.
- Page-cache slot without a shadow: the folio's whole index range is set to
  NULL by one `xas_store()` in `page_cache_delete()`.
- `mapping->a_ops->free_folio()`: page-cache path only.

**Shadow entries**

- `pack_shadow()` takes a `file` argument; a file shadow keeps
  `BITS_PER_LONG - EVICTION_SHIFT` counter bits, an anon shadow
  `SWAP_COUNT_SHIFT` fewer (`EVICTION_SHIFT_ANON`, `EVICTION_MASK_ANON`).
- Reason for the anon limit: the swap table entry keeps the swap count and,
  when `SWAP_TABLE_HAS_ZEROFLAG`, the zero flag in its top
  `SWP_TB_FLAGS_BITS`; `shadow_to_swp_tb()` in `mm/swap_table.h` has a
  `VM_WARN_ON_ONCE()` for a shadow with bits there.
- `bucket_order` is an array indexed by `WORKINGSET_ANON` and
  `WORKINGSET_FILE`; `workingset_init()` sets each from its own bit count.
- A new field in the shadow must be added to `EVICTION_SHIFT`; the
  `BUILD_BUG_ON()` in `lru_gen_eviction()` checks that `LRU_GEN_WIDTH` plus
  `LRU_REFS_WIDTH` still fit in the bits left by the larger of the two
  shifts.
- Memcg id packed: `mem_cgroup_private_id()`, looked up again with
  `mem_cgroup_from_private_id()`.
- `lru_gen_eviction()` token: `min_seq` shifted by `LRU_REFS_WIDTH`, or-ed
  with `max(refs - 1, 0)`; it is not shifted by `bucket_order` and does not
  call `workingset_age_nonresident()`.
- Swapped-out folio: the shadow is in the per-cluster swap table
  (`table` in `struct swap_cluster_info`), one entry per slot; read with
  `swap_cache_get_shadow()`.
- `shadow_nodes` list and its shrinker: cover page-cache xarray nodes only;
  swap table shadows are not on it.

**Refault decision**

- There is no lru_note_cost_refault() in this tree; `workingset_refault()`
  does not charge refault cost.
- Classic LRU, not recent: only `WORKINGSET_REFAULT_BASE + file` is counted;
  the workingset bit of the shadow is ignored.
- Classic LRU, recent: `folio_set_active()`, `workingset_age_nonresident()`
  on the refaulting folio's lruvec, `WORKINGSET_ACTIVATE_BASE + file`.
- `folio_set_workingset()` and `WORKINGSET_RESTORE_BASE + file`: only when
  recent and the shadow's workingset bit is set.
- Workingset size in `workingset_test_recent()`, file folio:
  `NR_ACTIVE_FILE`, plus `NR_ACTIVE_ANON` and `NR_INACTIVE_ANON` when
  `mem_cgroup_get_nr_swap_pages()` is above 0.
- Workingset size, anon folio: `NR_ACTIVE_FILE` and `NR_INACTIVE_FILE`, plus
  `NR_ACTIVE_ANON` when swap is available.
- Unpacked counter: shifted left by `bucket_order[file]`; the distance is
  masked with `EVICTION_MASK` or `EVICTION_MASK_ANON` by type.
- `lru_gen_refault()`: counts nothing and changes nothing when the shadow's
  lruvec is not `folio_lruvec(folio)`.
- `lru_gen_refault()`, recent means the shadow's sequence is within
  `MAX_NR_GENS` of `max_seq`; it never calls `folio_set_active()`.
- `lru_gen_refault()`, recent with workingset bit: `folio_set_workingset()`
  and `WORKINGSET_RESTORE_BASE`; `WORKINGSET_ACTIVATE_BASE` only if
  `lru_gen_in_fault()`.
- `lru_gen_refault()`, recent without workingset bit: restores the stored
  refs into the folio flags under `LRU_REFS_MASK`.
- Call sites: two, `filemap_add_folio()` (skipped with `__GFP_WRITE`) and
  `__swap_cache_alloc()` in `mm/swap_state.c`; both run before
  `folio_add_lru()`.

## LRU lists and counters

**LRU isolation**

- `folio_isolate_lru()` order: `folio_test_clear_lru()`, then `folio_get()`,
  then `folio_lruvec_lock_irq()`, `lruvec_del_folio()`,
  `lruvec_unlock_irq()`. The reference is taken only after the flag is won,
  and before the lock.
- `folio_isolate_lru()` return: `bool`, `false` only when `PG_lru` was
  already clear. It returns no error code.
- `isolate_lru_folios()` tests, in order: `folio_zonenum()` against
  `sc->reclaim_idx`, `folio_test_lru()`, `!sc->may_unmap && folio_mapped()`,
  `folio_try_get()`, `folio_test_clear_lru()`.
- `isolate_lru_folios()` has no test of unevictable, dirty, writeback or CMA
  and takes no isolation mode; there is no __isolate_lru_folio_prepare() and
  no skip_cma() in this tree.
- Zone test in `isolate_lru_folios()`: rejects only while fewer than
  `SWAP_CLUSTER_MAX_SKIPPED` folios have been skipped in this call; after
  that a folio above `sc->reclaim_idx` runs the remaining tests and can be
  isolated.
- Rejected folios in `isolate_lru_folios()`: none stays in place. Every
  visited folio gets `list_move()`: to `dst`, to `folios_skipped` (zone), or
  to the head of `src` (all other rejections).
- `isolate_lru_folios()` does not call `lruvec_del_folio()`; LRU sizes are
  fixed once after the loop by `update_lru_sizes()`.
- `folio_put()` after a lost `folio_test_clear_lru()` in
  `isolate_lru_folios()`: no assertion accompanies it.
- Flags on a classic list: only `PG_lru` changes in both functions.
- Flags on an MGLRU list: `folio_isolate_lru()` reaches
  `lru_gen_del_folio()` in `include/linux/mm_inline.h` with
  `reclaiming == false`, which clears the `LRU_GEN_MASK` bits and sets
  `PG_active` when the folio was in one of the two youngest generations.
- `isolate_folio()` (MGLRU): does not clear `PG_reclaim`; it clears the
  `LRU_REFS_MASK` bits when `PG_referenced` is clear, and passes
  `reclaiming == true`, so `PG_active` is not set.

**Isolation limit**

- Comparison in `too_many_isolated()` in `mm/vmscan.c`: true when
  `isolated > inactive`; `inactive` is shifted right by 3 first when
  `gfp_has_io_fs(sc->gfp_mask)`. There is no halving.
- `writeback_throttling_sane()` false means no limit: that is reclaim with
  `sc->target_mem_cgroup` set on cgroup v1, or on any hierarchy without
  `CONFIG_CGROUP_WRITEBACK`. Global direct reclaim, and cgroup v2 memcg
  reclaim with `CONFIG_CGROUP_WRITEBACK`, are limited.
- Fatal signal after the stall in `shrink_inactive_list()`: returns
  `SWAP_CLUSTER_MAX`. The return of 0 is for a second trip round the loop.
- `wake_throttle_isolated()`: called only from the two `too_many_isolated()`
  functions (`mm/vmscan.c`, `mm/compaction.c`), when the comparison there is
  false. Putback wakes nobody; a sleeper otherwise waits out the `HZ/50`
  timeout.
- Task that `reclaim_throttle()` does not put to sleep (see "Exempt tasks"
  under "Reclaim throttling"): goes straight to the second check in
  `shrink_inactive_list()`, which returns 0 if `too_many_isolated()` is still
  true.
- `NR_ISOLATED_ANON` and `NR_ISOLATED_FILE`: node-wide, and raised by
  isolators that `too_many_isolated()` in `mm/vmscan.c` never blocks, for
  example `shrink_active_list()`, kswapd in `shrink_inactive_list()`, and
  `isolate_migratepages_block()`.
- MGLRU: `evict_folios()` neither calls `too_many_isolated()` nor changes
  `NR_ISOLATED_ANON` or `NR_ISOLATED_FILE`, so folios it holds are invisible
  to both `too_many_isolated()` functions.

**Scans under the LRU lock**

- **Potentially unsafe usage**: setting a filtered folio aside without adding
  it to the loop bound.
  - Unsafe: when no second counter caps the folios set aside; the lock is
    held with interrupts off for as long as the filter keeps rejecting.
  - Safe: `isolate_lru_folios()`: zone-ineligible folios do not add to
    `scan`, but `max_nr_skipped` counts them, in folios not pages, and at
    `SWAP_CLUSTER_MAX_SKIPPED` (`include/linux/swap.h`) the zone test stops
    applying, so each later folio adds to `scan`.
  - Safe: `scan_folios()`: `remaining` starts at `nr_to_scan` and drops by
    one per folio visited, whether sorted, isolated or skipped; it asserts
    `nr_to_scan <= MAX_LRU_BATCH`, and also stops a zone when `isolated` or
    `skipped_zone` reaches `MIN_LRU_BATCH`.
- `scan` and `total_scan` in `isolate_lru_folios()`: `scan` bounds the loop
  and excludes zone-skipped pages; `total_scan` includes them and is what
  `*nr_scanned` returns.
- **Unsafe usage**: leaving a visited folio at the tail of the list being
  scanned; each iteration takes the tail again with `lru_to_folio()`.
  - Safe: `list_move()` every visited folio, accepted or not, as
    `isolate_lru_folios()` does at its `move` label.
- **Potentially unsafe usage**: processing a whole LRU list under the lock.
  - Unsafe: when the list length is the only bound on one lock hold.
  - Safe: stop after `MAX_LRU_BATCH` folios, unlock, `cond_resched()`, lock
    again, as `lru_gen_change_state()` does around `fill_evictable()` and
    `drain_evictable()`.
- **Potentially unsafe usage**: `folio_put()` while holding the LRU lock.
  - Unsafe: when `PG_lru` may be set and the reference may be the last;
    `__page_cache_release()` in `mm/folio.c` then takes the lruvec lock.
  - Safe: drop the lock first, as `isolate_migratepages_block()` does at
    `isolate_fail_put`.
  - Safe: after `folio_test_clear_lru()` returned false, as in
    `isolate_lru_folios()`: `__page_cache_release()` takes the lock only
    when `folio_test_lru()` is true.

**Reclaim counters**

- Scan, steal, demote, refill and rotate counters: all are
  `enum node_stat_item` in `include/linux/mmzone.h`, none is an
  `enum vm_event_item`. This covers `PGSCAN_KSWAPD` and `PGSTEAL_KSWAPD` with
  their per-reclaimer siblings, `PGDEMOTE_KSWAPD` with its siblings,
  `PGSCAN_ANON`, `PGSCAN_FILE`, `PGSTEAL_ANON`, `PGSTEAL_FILE`, `PGREFILL`,
  `PGROTATE_ANON` and `PGROTATE_FILE`.
- Helper: `mod_lruvec_state()`, in `mm/memcontrol.c` under `CONFIG_MEMCG`,
  one call per counter; it updates the node, the memcg and the lruvec.
  `count_vm_events()` and `count_memcg_events()` take `enum vm_event_item`
  and do not apply.
- `cgroup_reclaim(sc)`: does not guard any of these updates; memcg-limit
  reclaim counts in the node totals too.
- `mod_node_page_state()` alone on one of these items: updates the node and
  loses the memcg and lruvec share.
- `memcg_node_stat_items[]` in `mm/memcontrol.c`: an item missing from it
  makes `__mod_memcg_lruvec_state()` hit `WARN_ONCE()` and skip the memcg
  and lruvec update.
- `PGROTATE_ANON`, `PGROTATE_FILE`: pages scanned but not reclaimed, plus
  pages `shrink_active_list()` keeps active; `prepare_scan_control()` reads
  them with `lruvec_page_state_monotonic()` to build `lruvec->cost[]`.
- `PGROTATED`: a separate vm event, counted with `__count_vm_events()` in
  `lru_move_tail()` and one other site in `mm/folio.c`, with no memcg copy.
  There is no mm/swap.c in this tree.
- Still vm events in reclaim: `PGSCAN_SKIP` (`__count_zid_vm_events()`),
  `PGACTIVATE` (`count_vm_events()` plus `count_memcg_folio_events()` in
  `shrink_folio_list()`), `PGDEACTIVATE` (`count_vm_events()` plus
  `count_memcg_events()` in `shrink_active_list()`),
  `PGSCAN_DIRECT_THROTTLE`.
- __count_memcg_events(): not in this tree; use `count_memcg_events()`.
- `reclaimer_offset()`: the result is added to a `enum node_stat_item` base;
  `CHECK_RECLAIMER_OFFSET()` holds the `BUILD_BUG_ON()` layout checks.

**Classic and MGLRU accounting**

| Item | `shrink_inactive_list()` | `evict_folios()` |
|---|---|---|
| `NR_ISOLATED_ANON + file` | `+nr_taken` under the lock, `-nr_taken` after putback | not touched |
| `PGSCAN_KSWAPD + reclaimer_offset(sc)`, `PGSCAN_ANON` or `PGSCAN_FILE` | `nr_scanned`: every page looked at, zone-skipped included | in `scan_folios()`, `isolated` only |
| `PGREFILL` | not here; `shrink_active_list()` adds `nr_scanned` | in `scan_folios()`, pages moved by `sort_folio()` |
| `PGSCAN_SKIP` | in `isolate_lru_folios()`: pages skipped for their zone | in `scan_folios()`: pages for which `isolate_folio()` failed |
| `sc->nr_reclaimed` | added by `shrink_lruvec()` from the return value | added in `evict_folios()`, each pass |
| `sc->nr` tallies, flusher wakeup | `handle_reclaim_writeback(nr_taken, ...)` | `handle_reclaim_writeback(isolated, ...)`, first pass only |
| Putback | `move_folios_to_lru()`, lock not held | `move_folios_to_lru()`, lock not held |
| `PGDEMOTE_KSWAPD + reclaimer_offset(sc)` | `stat.nr_demoted` | `stat.nr_demoted`, each pass |
| `PGSTEAL_KSWAPD + reclaimer_offset(sc)`, `PGSTEAL_ANON` or `PGSTEAL_FILE` | `nr_reclaimed` | `reclaimed`, each pass |
| `PGROTATE_ANON + file` | `nr_scanned - nr_reclaimed`, if positive | `nr_isolated - total_reclaimed`, if positive, once after the last pass |

- Helper for every `PG` row except `PGSCAN_SKIP`: `mod_lruvec_state()`,
  with no `cgroup_reclaim(sc)` test, in both functions.
- `handle_reclaim_writeback()`: fills `sc->nr.dirty`, `sc->nr.congested`,
  `sc->nr.writeback`, `sc->nr.immediate`, `sc->nr.taken` for both paths, and
  wakes the flushers when `stat->nr_unqueued_dirty == nr_taken`.
  `struct scan_control` has no unqueued_dirty or file_taken member in `nr`.
- lru_note_cost(): not in this tree. The rotation share of reclaim cost
  comes from `PGROTATE_ANON` and `PGROTATE_FILE`, which both paths update;
  `prepare_scan_control()` consumes them and returns early under MGLRU
  unless `lru_gen_switching()`.
- `move_folios_to_lru()`: takes only the list, locks each folio's lruvec
  itself, and its caller must not hold a lruvec lock.
- Freeing: neither function uncharges or frees after `shrink_folio_list()`;
  `shrink_folio_list()` and `move_folios_to_lru()` call
  `mem_cgroup_uncharge_folios()` and `free_unref_folios()` themselves. There
  is no mem_cgroup_uncharge_list() in this tree.

## Scan balance, throttling and kswapd

**Anon and file balance**

- Cost inputs: there is no lru_note_cost() or lru_note_cost_refault() in this
  tree, and `struct lruvec` has no `anon_cost` or `file_cost` field.
- `lruvec->cost[]` (`struct lru_cost` in `include/linux/mmzone.h`): holds the
  costs, under `lruvec->cost_lock`.
- `prepare_scan_control()`: the only place that updates and decays
  `lruvec->cost[]`, for the target lruvec; it copies the result to
  `sc->anon_cost` and `sc->file_cost`.
- Cost sources: deltas of `PGROTATE_ANON + f`, `WORKINGSET_RESTORE_BASE + f`
  and, for anon only, `NR_VMSCAN_WRITE`; IO events weigh `SWAP_CLUSTER_MAX`
  times a rotation.
- Order of tests in `get_scan_count()`: `SWAPPINESS_ANON_ONLY` comes first,
  before `sc->may_swap` and `can_reclaim_anon_pages()`.
- `SWAPPINESS_ANON_ONLY` when `can_reclaim_anon_pages()` is false: every entry
  of `nr[]` is zeroed and the function returns; file is not scanned as a
  fallback.
- `SWAPPINESS_ANON_ONLY`: `MAX_SWAPPINESS + 1` in `mm/internal.h`.
- Swappiness `MAX_SWAPPINESS` (200): has no test of its own and is not
  `SCAN_ANON`; under `SCAN_FRACT` its file weight is 0.
- Swappiness 0: the zero test gives `SCAN_FILE` only when
  `cgroup_reclaim(sc)`; global reclaim falls through, and gets `SCAN_FRACT`
  with an anon weight of 0 unless `sc->file_is_tiny` or `sc->cache_trim_mode`
  is set.
- `SCAN_EQUAL`: needs `sc->priority == 0`, the most aggressive pass, and
  non-zero swappiness.
- `can_reclaim_anon_pages()`: tests `get_nr_swap_pages()` or
  `mem_cgroup_get_nr_swap_pages()`, then `can_demote()`; it does not read
  `total_swap_pages`.
- `calculate_pressure_balance()`: holds the `SCAN_FRACT` weights.
- MGLRU, when `lru_gen_enabled()` and not `lru_gen_switching()`:
  `prepare_scan_control()` returns before it sets anything; `shrink_lruvec()`
  returns before it calls `get_scan_count()` when `!root_reclaim(sc)`, and
  root reclaim returns from `shrink_node()` after `lru_gen_shrink_node()`.

**Memory cgroup protection**

- `apply_proportional_protection()` in `mm/vmscan.c`: does the scan scaling;
  `get_scan_count()` and MGLRU's `get_nr_to_scan()` both call it.
- There is no mem_cgroup_size() here; `mem_cgroup_protection()` returns the
  usage through its fifth argument, next to `min` and `low`.
- Formula: `scan -= scan * protection / (usage + 1)`, with
  `usage = max(usage, protection)`.
- Protection used: `low` only if `!sc->memcg_low_reclaim && low > min`, which
  also sets `sc->memcg_low_skipped`; otherwise `min`, on the first pass too.
- `SWAP_CLUSTER_MAX` floor: applied to the scaled size before
  `>> sc->priority`, and only when `min` or `low` is non-zero.
- Low override: `do_try_to_free_pages()` is the only place that sets
  `sc->memcg_low_reclaim`.
- `balance_pgdat()` and `__node_reclaim()`: reach `shrink_node()` without that
  retry, so on the classic LRU kswapd and node reclaim always skip a memcg
  that is below low in `shrink_node_memcgs()`.
- Retry order in `do_try_to_free_pages()`: it returns first if anything was
  reclaimed or `sc->compaction_ready` is set; then it retries with
  `sc->memcg_full_walk`, then with `sc->force_deactivate` if
  `sc->skipped_deactivate`, and only then with `sc->memcg_low_reclaim` if
  `sc->memcg_low_skipped`.
- MGLRU root reclaim, when not `lru_gen_switching()`: `shrink_node()` calls
  `lru_gen_shrink_node()` and does not reach `shrink_node_memcgs()`.
- `shrink_one()`: tests `mem_cgroup_below_min()` and `mem_cgroup_below_low()`
  but does not call `mem_cgroup_calculate_protection()`.
- `lru_gen_age_node()`: the only caller of
  `mem_cgroup_calculate_protection()` for MGLRU root reclaim; kswapd runs it.
- `shrink_one()` on a memcg below low: its test does not read
  `sc->memcg_low_reclaim`; it returns `MEMCG_LRU_TAIL` while its lruvec is not
  at `MEMCG_LRU_TAIL`, and calls `try_to_shrink_lruvec()` when its lruvec is
  already at `MEMCG_LRU_TAIL`; for an online memcg `get_nr_to_scan()` still
  scales the target with `apply_proportional_protection()`.

**Reclaim throttling**

- Exempt tasks: `reclaim_throttle()` only calls `cond_resched()` for a task
  with `PF_KTHREAD` or `PF_USER_WORKER` that is not kswapd, whatever the reason.
- kswapd: is throttled, for `VMSCAN_THROTTLE_WRITEBACK`, from `shrink_node()`.
- Fatal signal: `reclaim_throttle()` makes no signal test and sleeps in
  `TASK_UNINTERRUPTIBLE`; only the two `VMSCAN_THROTTLE_ISOLATED` callers test
  `fatal_signal_pending()` after it returns.
- `PF_LOCAL_THROTTLE`: `current_may_throttle()` is tested at the
  `VMSCAN_THROTTLE_CONGESTED` site in `shrink_node()` only.

| Reason | Timeout | Early wake |
|---|---|---|
| `VMSCAN_THROTTLE_WRITEBACK` | `HZ/10` | `__acct_reclaim_writeback()` |
| `VMSCAN_THROTTLE_ISOLATED` | `HZ/50` | `wake_throttle_isolated()` |
| `VMSCAN_THROTTLE_NOPROGRESS` | 1 jiffy | `consider_reclaim_throttle()` |
| `VMSCAN_THROTTLE_CONGESTED` | 1 jiffy | none; no code wakes that queue |

- `VMSCAN_THROTTLE_WRITEBACK` has three call sites:
  - `shrink_node()`: kswapd only, when `sc->nr.immediate` is non-zero.
  - `handle_reclaim_writeback()`: when every folio taken was unqueued dirty
    and `writeback_throttling_sane()` is false, which needs
    `cgroup_reclaim(sc)`.
  - `do_writepages()` in `mm/page-writeback.c`: on `-ENOMEM` with
    `WB_SYNC_ALL`, outside reclaim.
- MGLRU root reclaim, when not `lru_gen_switching()`: `shrink_node()` returns
  after `lru_gen_shrink_node()`, before its WRITEBACK and CONGESTED call
  sites.

**Background reclaim loop**

- `sc.may_writepage`: set to `!nr_boost_reclaim` on every iteration, like
  `sc.may_swap`.
- `mm/vmscan.c` has no test of `sc.priority < DEF_PRIORITY - 2` for writeback
  and no reference to `laptop_mode`.
- `sc.priority--`: runs only when `raise_priority || !nr_reclaimed`, not on
  every pass.
- `kswapd_shrink_node()`: returns
  `max(sc->nr_scanned, sc->nr_reclaimed - nr_reclaimed) >= sc->nr_to_reclaim`,
  so pages reclaimed in the pass count as well as pages scanned; true clears
  `raise_priority`.
- MGLRU: `set_initial_priority()`, called from `lru_gen_shrink_node()`, can
  lower `sc.priority` from `DEF_PRIORITY` to as little as `DEF_PRIORITY / 2`
  inside the first pass.
- Not loop exits: `balance_pgdat()` tests neither
  `sc.nr_reclaimed >= sc.nr_to_reclaim` nor `kswapd_failures`.
- Unbalanced while boost reclaim is pending: `nr_boost_reclaim` is cleared and
  the loop restarts at `DEF_PRIORITY`; balanced with boost pending keeps
  reclaiming.
- Stop test: `kthread_freezable_should_stop()`; the loop breaks if it returns
  true or reports that the task was frozen.
- Aging call: `kswapd_age_node()`; there is no age_active_anon() here.
- After the loop: if `!sc.nr_reclaimed`, `sc.priority < 1`,
  `sc.cache_trim_mode_failed` is set and `sc.no_cache_trim_mode` is clear, it
  sets `sc.no_cache_trim_mode` and restarts at `DEF_PRIORITY`.
- `goto out` on a balanced node: skips that restart and the failure count.

**kswapd sleep and wakeup**

- `wakeup_kswapd()`: writes `kswapd_highest_zoneidx` and `kswapd_order` before
  it tests `waitqueue_active()`, so a request made while kswapd runs is kept
  for its next loop.
- `wakeup_kswapd()`: returns before recording anything only for an unmanaged
  zone or when `cpuset_zone_allowed()` fails.
- `wakeup_kswapd()` on a balanced node: skips the wake only if
  `pgdat_watermark_boosted()` is also false.
- `prepare_kswapd_sleep()`: wakes every `pfmemalloc_wait` sleeper first, before
  the hopeless and balance tests, on both calls.
- `allow_direct_reclaim()`: second waker; it calls
  `wake_up_interruptible(&pgdat->kswapd_wait)` directly when the reserve test
  fails, without going through `wakeup_kswapd()`.
- `wake_all_kswapds()`: with `defrag_mode` set, passes
  `max(order, pageblock_order)` as the order.

**kswapd failures and hopeless nodes**

- `kswapd_failures`: an `atomic_t`; `kswapd_test_hopeless()`,
  `kswapd_clear_hopeless()` and `kswapd_try_clear_hopeless()` are defined in
  `mm/vmscan.c`.
- Increment: `balance_pgdat()` counts a failure only if `!sc.nr_reclaimed` and
  the run did not start with a watermark boost (`!boosted`).
- Reset after reclaim: `shrink_node()` and `lru_gen_shrink_node()` call
  `kswapd_try_clear_hopeless(pgdat, sc->order, sc->reclaim_idx)` when the pass
  reclaimed something.
- `kswapd_try_clear_hopeless()`: resets only if `pgdat_balanced()` is true for
  that order and index; progress that leaves the node unbalanced resets
  nothing.
- `free_frozen_page_commit()` in `mm/page_alloc.c`: resets with
  `kswapd_clear_hopeless()`, with no `pgdat_balanced()` test, when it clears
  `ZONE_BELOW_HIGH` on a hopeless node and
  `next_memory_node(pgdat->node_id) < MAX_NUMNODES`.
- `demotion_enabled_store()` in `mm/memory-tiers.c`: resets every online node
  when demotion goes from off to on.
- `prepare_kswapd_sleep()` and the body of `balance_pgdat()`: contain no reset;
  `balance_pgdat()` reaches `kswapd_try_clear_hopeless()` only through
  `shrink_node()`.
- `kswapd_clear_hopeless()`: does not wake kswapd; kswapd runs again when it
  is next woken, for example by `wakeup_kswapd()`.
- `skip_throttle_noprogress()` on a hopeless node: returns true for
  `VMSCAN_THROTTLE_CONGESTED` as well as `VMSCAN_THROTTLE_NOPROGRESS`.

**kswapd reclaim order**

- Drop condition: `sc->order && sc->nr_reclaimed >= compact_gap(sc->order)`,
  tested after `shrink_node()` in every pass; `sc->nr_reclaimed` is the total
  for the whole `balance_pgdat()` run.
- The drop lasts for the run: `restart` resets `sc.priority` only, not
  `sc.order`.
- **Unsafe usage**: passing the `order` argument of `balance_pgdat()` to
  `pgdat_balanced()` after `kswapd_shrink_node()` has run.
  - Safe: pass `sc.order`, as the check at the top of the loop in
    `balance_pgdat()` does; `kswapd_shrink_node()` zeroes it so that later
    checks are at order 0.
  - Safe: pass the value `balance_pgdat()` returned, as `kswapd()` does with
    `reclaim_order` for `prepare_kswapd_sleep()`.
- `pgdat_balanced()` with `defrag_mode` and a non-zero order: compares
  `NR_FREE_PAGES_BLOCKS`, not `NR_FREE_PAGES`, with the watermark; after the
  drop it compares `NR_FREE_PAGES`.
- `kswapd()`: when `reclaim_order < alloc_order` it goes back to
  `kswapd_try_to_sleep()` without reading a new request; there `alloc_order`
  is used for `wakeup_kcompactd()` only.

**Zones in balance checks**

- `for_each_managed_zone_pgdat()`: defined in `include/linux/swap.h`.
- After the loop `zone` and `idx` point one past the bound and must not be
  used.
- Direction: the macro walks upward from index 0; code that needs the highest
  managed zone open-codes a downward loop with `managed_zone()`, as the
  `buffer_heads_over_limit` scan in `balance_pgdat()` does.
- **Unsafe usage**: a zone loop that answers "not balanced" or "throttle"
  when it visited no zone.
  - Safe: `pgdat_balanced()` returns true when `mark` is still `-1`, that is,
    no managed zone at or below `highest_zoneidx`.
  - Safe: `allow_direct_reclaim()` returns true when `pfmemalloc_reserve` is 0;
    `throttle_direct_reclaim()` waits on `pfmemalloc_wait` for it to return
    true.
- `allow_direct_reclaim()` skips a managed zone only if
  `zone_reclaimable_pages()` is 0 and the `NR_FREE_PAGES` snapshot is
  non-zero.
- A zone with nothing reclaimable and nothing free still adds its
  `min_wmark_pages()` to the reserve in `allow_direct_reclaim()`.
- `allow_direct_reclaim()` bound: `ZONE_NORMAL`, fixed.
- `allow_direct_reclaim()` when the test fails and kswapd is on
  `kswapd_wait`: lowers `kswapd_highest_zoneidx` to `ZONE_NORMAL` if it was
  higher, then wakes kswapd.
- `balance_pgdat()`: passes `highest_zoneidx` to `pgdat_balanced()`, not
  `sc.reclaim_idx`, which `buffer_heads_over_limit` may have raised.
- `kswapd_shrink_node()`: sums `sc->nr_to_reclaim` up to `sc->reclaim_idx`.
- `should_abort_scan()` (MGLRU): open-codes the loop with `managed_zone()`
  and needs every managed zone to pass; no zone visited means abort.

## Shrinkers

**Shrinker callbacks and lifetime**

- `count_objects` returning 0: `do_shrink_slab()` returns before it reads or
  writes `nr_deferred`, so no work is deferred for that call. Nothing in
  `mm/shrinker.c` stops `count_objects` from testing `sc->gfp_mask`.
- `scan_objects` returning `SHRINK_STOP`: that batch adds nothing to `freed`
  and its `sc->nr_scanned` is not read; `freed` from earlier batches is still
  returned.
- Deferred count after the loop: `nr + delta - scanned`, capped at
  `2 * freeable`. It is not the leftover `total_scan`.
- **Potentially unsafe usage**: `scan_objects` writing a smaller value to
  `sc->nr_scanned`.
  - Unsafe: leaving `sc->nr_scanned` at 0 and returning anything but
    `SHRINK_STOP`; the loop in `do_shrink_slab()` subtracts `nr_scanned` from
    `total_scan` and never ends.
  - Safe: return `SHRINK_STOP` when `sc->nr_scanned` is 0, as
    `i915_gem_shrinker_scan()` and `drm_pagemap_shrinker_scan()` do.
- **Unsafe usage**: a `SHRINKER_MEMCG_AWARE` `count_objects` returning
  `SHRINK_EMPTY` while the list for `sc->memcg` and `sc->nid` holds objects.
  `shrink_slab_memcg()` clears the bit, and `__list_lru_add()` sets it again
  only when a list goes from empty to non-empty.
  - Safe: return 0 when objects exist but must be skipped, as
    `zswap_shrinker_count()` does.
  - Safe: return `SHRINK_EMPTY` only when `list_lru_shrink_count()` is 0, as
    `deferred_split_count()` does.
- `shrinker_alloc()`: sets `seeks` to `DEFAULT_SEEKS`.
- Walkers: find the shrinker under `rcu_read_lock()`, then hold a
  `shrinker_try_get()` reference across `do_shrink_slab()` with RCU dropped;
  nothing in `mm/shrinker.c` uses SRCU.
- `shrink_slab()`: retakes `rcu_read_lock()` before `shrinker_put()`, because
  the walk continues from this shrinker's `list` node.
- `shrink_slab_memcg()`: calls `shrinker_put()` with no RCU lock held; it finds
  the next shrinker by id with `idr_find()`.
- `shrinker_free()` order, for a shrinker with `SHRINKER_REGISTERED`:
  `shrinker_put()`, `wait_for_completion()`, and only then `list_del_rcu()`
  and, with `SHRINKER_MEMCG_AWARE`, `idr_remove()` under `shrinker_mutex`.
  Without `SHRINKER_REGISTERED` there is no put and no wait.
- After the last reference is dropped, until `shrinker_free()` unlinks it: the
  shrinker is still on `shrinker_list` and in `shrinker_idr` with refcount 0.
  `shrinker_try_get()` fails, and `shrink_slab_memcg()` then clears the memcg
  bit.
- `shrinker_free()` called from that shrinker's own callback: never returns,
  because the walker drops its reference only after the callback returns.
- **Potentially unsafe usage**: calling `shrinker_free()` on a registered
  shrinker while holding a lock its callbacks take.
  - Unsafe: when a callback blocks on that lock; `shrinker_free()` sleeps in
    `wait_for_completion()` until the walker's `shrinker_put()`.
  - Safe: when the callback only trylocks and returns `SHRINK_STOP`, as
    `super_cache_scan()` does with `super_trylock_shared()`;
    `deactivate_locked_super()` calls `shrinker_free()` with `s_umount` held
    exclusively.
- **Potentially unsafe usage**: `shrinker_register()` before the object behind
  `private_data` is fully set up.
  - Unsafe: when a callback reads state that is not initialised yet.
  - Safe: when each callback first tests a readiness flag; `sget_fc()`
    registers a superblock that is not filled in, `super_cache_count()` returns
    0 until `SB_BORN`, and `super_cache_scan()` goes through
    `super_trylock_shared()`.
- `alloc_super()`: allocates and fills the shrinker but does not call
  `shrinker_register()`; `sget_fc()` in `fs/super.c` does.
- `CONFIG_SHRINKER_DEBUG`: `shrinker_debugfs_count_show()` and
  `shrinker_debugfs_scan_write()` in `mm/shrinker_debug.c` call the callbacks
  with no `shrinker_try_get()`.
- `shrinker_free()`: for a shrinker that has a debugfs entry, calls
  `shrinker_debugfs_remove()` after the wait and before `call_rcu()`.

**NUMA and memcg flags**

- Without `SHRINKER_NUMA_AWARE`: `sc->nid` is still the node being reclaimed.
  `do_shrink_slab()` never writes it; only the `nr_deferred` index is forced
  to 0, in `xchg_nr_deferred()` and `add_nr_deferred()`.
- Kerneldoc of `shrink_slab()`: says unaware shrinkers receive node 0; the code
  does not do that.
- Without `SHRINKER_NUMA_AWARE`: `shrink_slab()` does not skip the shrinker for
  any node, so `drop_slab()` calls it for each online node.
- Without `SHRINKER_MEMCG_AWARE`: `sc->memcg` is whatever `shrink_slab()` was
  given. That is `root_mem_cgroup` when memcg is enabled, and NULL only when
  memcg is disabled or without `CONFIG_MEMCG`.
- `shrinker_alloc()` clears `SHRINKER_MEMCG_AWARE` when `shrinker_memcg_alloc()`
  returns `-ENOSYS`: without `CONFIG_MEMCG`, when `mem_cgroup_disabled()`, or
  when `mem_cgroup_kmem_disabled()` and `SHRINKER_NONSLAB` is not set.
- `shrinker->nr_deferred`: not allocated while `SHRINKER_MEMCG_AWARE` is kept.
  The root pass uses the `struct shrinker_info` of `sc->memcg` too.
- `set_shrinker_bit()`: outside `mm/shrinker.c`, its callers are
  `__list_lru_add()` and `memcg_reparent_list_lru_one()` in `mm/list_lru.c`.
- `__list_lru_init()`: copies `shrinker->id` into the `shrinker_id` field of
  `struct list_lru`, so `shrinker_alloc()` must come before
  `list_lru_init_memcg()`.
- `list_lru_init()`: stores -1 as the id; `set_shrinker_bit()` ignores a
  negative id, so adding to that list sets no memcg bit.
- **Potentially unsafe usage**: a callback under a `SHRINKER_MEMCG_AWARE`
  shrinker that counts state not split by memcg.
  - Unsafe: when it returns the whole count for a non-root `sc->memcg`; the
    same objects are then counted once for every memcg whose bit is set.
  - Safe: return 0 unless `mem_cgroup_shrink_is_root()` is true, as
    `btrfs_nr_cached_objects()` and `shmem_unused_huge_count()` do under
    `super_cache_count()`.
- `shrinker_debugfs_count_show()`: passes NULL as `sc->memcg` to a
  non-memcg-aware shrinker, and calls a non-NUMA-aware one for node 0 only.
- `shrinker_debugfs_scan_write()`: passes the node the user wrote, without
  testing `SHRINKER_NUMA_AWARE`.

## Multi-generation LRU

**Generations and tiers**

- Tier: `lru_tier_from_refs()` in `include/linux/mm_inline.h` returns
  `MAX_NR_TIERS - 1` when its `workingset` argument is true, else
  `order_base_2(refs)`.
- `folio_lru_refs()`: 0 when `PG_referenced` is clear, else the
  `LRU_REFS_MASK` value plus one.
- `LRU_REFS_FLAGS`: `LRU_REFS_MASK | BIT(PG_referenced)`; `PG_workingset` is
  not part of it.
- Bit position: `LRU_REFS_PGOFF` is `LRU_GEN_PGOFF - LRU_REFS_WIDTH`, so the
  counter sits just below the generation field.
- Flags word: `folio->flags` is a struct; the generation and the counter are
  read and written through `folio->flags.f`.

**Active generations**

- `lru_gen_is_active()`: true for the generation of `max_seq` and of
  `max_seq - 1`, the two youngest; it does not read `min_seq[]`.
- Not statistics only: `lru_gen_del_folio()` with `reclaiming` false sets
  `PG_active` on a folio leaving an active generation.
- `set_initial_priority()` in `mm/vmscan.c` picks `sc->priority` from the
  node counters `NR_INACTIVE_FILE` and, when anon can be reclaimed,
  `NR_INACTIVE_ANON`; `lru_gen_update_size()` fills them according to
  `lru_gen_is_active()`.
- `inc_max_seq()`: moves the size of the `max_seq - 1` generation to inactive
  and the size of the `max_seq + 1` generation to active, as one delta.
- Active is relative to one lruvec's `max_seq`: `__lru_gen_reparent_memcg()`
  moves pages between the active and inactive counters when child and parent
  disagree on whether a generation index is active.

**Runtime switch**

- `lru_gen_switching()` in `include/linux/mm_inline.h`: tests the static key
  `lru_switch`, defined in `mm/vmscan.c`.
- `lru_gen_change_state()`: enables `lru_switch` before it flips
  `lru_gen_caps[LRU_GEN_CORE]`, and disables it after the last lruvec is
  converted.
- Reclaim entry points `shrink_lruvec()`, `shrink_node()` and
  `kswapd_age_node()`: test `lru_gen_enabled() || lru_gen_switching()`, run
  the multi-gen path, and during a switch run the classic path as well.
- Multi-gen-only shortcuts test `lru_gen_enabled() && !lru_gen_switching()`:
  for example `folio_check_references()`, `prepare_scan_control()`,
  `snapshot_refaults()`, and the `lru_gen_look_around()` call in
  `folio_referenced_one()`.
- Per-lruvec flag: `lrugen->enabled` in `struct lru_gen_folio`, written by
  `lru_gen_change_state()` under the lru lock and by `lru_gen_init_lruvec()`.
- `lru_gen_enabled()`: one global static key, not per lruvec.
- `lru_gen_in_fault()`: returns `current->in_lru_fault`; it says nothing
  about which lists are in use.
- `lru_gen_change_state()`: does not call `lru_gen_rotate_memcg()`.
- `state_is_valid()` and `seq_is_valid()`: asserted under the lru lock before
  each lruvec is converted, not after.
- Locks, in order: `cgroup_lock()`, `cpus_read_lock()`, `get_online_mems()`,
  then a function-local `state_mutex`.
- **Potentially unsafe usage**: branching on `lru_gen_enabled()` alone.
  - Unsafe: in code that can run while `lru_gen_change_state()` converts the
    lists, and that chooses which set of lists reclaim scans or assumes
    folios other than the one it holds are on `lrugen->folios[]`; during a
    switch one lruvec has folios on both kinds of list.
  - Safe: run the multi-gen path and fall through to the classic path while
    `lru_gen_switching()` is true, as `shrink_node()` does.
  - Safe: under `cgroup_mutex`, which `lru_gen_change_state()` holds through
    `cgroup_lock()` for the whole switch, as `memcg_reparent_objcgs()` does;
    `offline_css()` asserts the mutex.
  - Safe: add or remove one folio under the lru lock with
    `lruvec_add_folio()` or `lruvec_del_folio()`, as `lru_deactivate()` in
    `mm/folio.c` does; `lru_gen_add_folio()` tests `lrugen->enabled` and
    `lru_gen_del_folio()` tests `folio_lru_gen()`.

**Access tracking flags**

- `folio_update_gen()` and `lru_gen_set_refs()`: both take a `vma_flags`
  argument for `is_exec_file_folio()`.
- `folio_update_gen()`: a file folio in an executable VMA is promoted on the
  first young PTE seen, with neither flag set beforehand.
- `lru_gen_set_refs()` in `mm/vmscan.c`, called only from
  `folio_check_references()` and `walk_update_folio()`:

| Folio state | Effect | Returns |
|---|---|---|
| neither flag, exec file folio | clears `LRU_REFS_FLAGS`, sets `PG_workingset` | true |
| neither flag, other | sets `PG_referenced`, zeroes `LRU_REFS_MASK` | false |
| `folio_lru_refs()` > 1 | clears `LRU_REFS_FLAGS`, sets `PG_workingset` | true |
| any other state | calls `folio_mark_accessed()` | true |

- Last row: covers `PG_referenced` with a zero counter, and `PG_workingset`
  without `PG_referenced`; `lru_gen_set_refs()` returns true, so the folio is
  activated, without itself setting `PG_workingset`.
- Comment against code, `LRU_REFS_MASK`: the comment says it is not used for
  page table accesses; `lru_gen_set_refs()` reads it and, through
  `folio_mark_accessed()`, can increment it.
- Comment against code, promotion: the comment says later accesses set
  `PG_workingset`; on the rmap path that needs a non-zero counter or an exec
  file folio.
- Shared bits: accesses through file descriptors raise the same counter, so
  they count toward the `folio_lru_refs()` > 1 test.
- `folio_add_lru()` during a fault (`lru_gen_in_fault()`, no `PF_MEMALLOC`):
  sets `PG_active` if `PG_workingset` is set, else sets `PG_referenced`
  through `folio_mark_accessed()`.
- `lru_gen_refault()`, matching lruvec but not recent: counts
  `WORKINGSET_REFAULT_BASE` and changes no flag; the recent cases are under
  "Refault decision".

**Tier bits on generation change**

| Function | `LRU_REFS_FLAGS` | `PG_workingset` | Other flag written |
|---|---|---|---|
| `folio_update_gen()`, when it writes the generation | clears | sets | none |
| `folio_inc_gen()` | clears | keeps | none |
| `lru_gen_add_folio()` | keeps | keeps | clears `PG_active` |
| `lru_gen_del_folio()` | keeps | keeps | may set `PG_active` |

- `folio_inc_gen()`: takes `lruvec` and `folio` only; there is no
  `reclaiming` argument and it does not touch `PG_reclaim`.
- `folio_inc_gen()`: takes the old generation from `lrugen->min_seq[type]`,
  not from the folio; a folio whose generation differs is returned unchanged.
- `folio_inc_gen()` callers: `sort_folio()` and `inc_min_seq()`; the second
  runs from `inc_max_seq()` when a type already has `MAX_NR_GENS`
  generations.
- `lru_gen_folio_seq()`: picks the generation from `PG_active`,
  `PG_workingset`, `PG_referenced`, `PG_reclaim`, dirty, writeback and
  swapcache, so kept access bits change where a re-added folio lands.
- **Unsafe usage**: reading `folio_lru_refs()` or the tier after
  `folio_inc_gen()` to account `protected[]`.
  - Safe: read refs and `PG_workingset` first, as `sort_folio()` and
    `inc_min_seq()` do.
- **Potentially unsafe usage**: re-adding a folio with `lru_gen_add_folio()`
  to change its generation.
  - Unsafe: when the caller expects a given generation and leaves stale
    `PG_active`, `PG_referenced`, `PG_workingset` or `PG_reclaim`;
    `lru_gen_folio_seq()` reads them.
  - Safe: clear `PG_referenced`, `LRU_REFS_MASK` and `PG_workingset` with
    `lru_gen_clear_refs()` while the folio is still on its generation list,
    as `deactivate_file_folio()` does before it queues the folio; once the
    generation bits are cleared `lru_gen_clear_refs()` returns without
    clearing anything.
  - Safe: `lruvec_add_folio_tail()` passes `reclaiming` true, which selects
    the oldest generation once `PG_active` is clear, as `lru_move_tail()`
    does.
  - Safe: set `PG_active` and clear `LRU_REFS_FLAGS` so that the folio lands
    in one of the two youngest generations, as `evict_folios()` does for
    rejects that would land in the oldest one.

**Generation aging**

- `walk_pte_range()`: takes the PTE lock with `spin_trylock()`.
- `walk_pmd_range_locked()`: takes the PMD lock with `spin_trylock()`; it is
  the only place the walk takes a lock from `pmd_lockptr()`.
- There is no should_skip_mm() here; `get_next_mm()` skips an mm only when
  its node bit in `mm->lru_gen.bitmap` is clear and `walk->force_scan` is
  false, and pins the mm with `mmgrab()`.
- `try_to_inc_max_seq()` with `seq <= mm_state->seq`: returns false and does
  not call `inc_max_seq()`.
- Without `CONFIG_LRU_GEN_WALKS_MMU`: `get_mm_state()` returns NULL and
  `try_to_inc_max_seq()` calls `inc_max_seq()` directly.
- `iterate_mm_list_nowalk()`: used when `should_walk_mmu()` is false or
  `set_mm_walk()` returns NULL.
- Walk pause: `walk_pud_range()` tests `need_resched()` and
  `walk->batched >= MAX_LRU_BATCH`; the walk has no signal test.
- `try_to_inc_max_seq_nowalk()`: a second way to advance `max_seq` with no
  walk, used by `max_lru_gen_memcg()` before reparenting; it advances
  `mm_state->seq` and leaves `mm_state->head` and `mm_state->tail` alone.
- `reset_batch_size()`: locks with `lruvec_live_lock_irq()`, which returns an
  ancestor's lruvec when the memcg is dying; the sizes are applied there.
- `lru_gen_look_around()` without a walk: `folio_activate()` can take the lru
  lock while the PTE lock is held.
- `folio_activate()` path: takes the folio off its list and re-adds it with
  `PG_active`; `lru_gen_folio_seq()` then gives `max_seq` if `PG_workingset`
  is set, else `max_seq - 1`.

**Eviction and sorting**

- `sort_folio()` cases in this tree:

| Folio | Action | Returns |
|---|---|---|
| not evictable | none | false |
| generation is not the oldest | `list_move()` to its own list | true |
| tier above `tier_idx`, or all bits set | `folio_inc_gen()`, `list_move()` | true |
| zone above `sc->reclaim_idx` | `folio_inc_gen()`, `list_move_tail()` | true |

- Unevictable folios: isolated like any other; `move_folios_to_lru()` culls
  them with `folio_putback_lru()`.
- Dirty and writeback folios: `sort_folio()` has no case for them; they are
  isolated and `shrink_folio_list()` decides.
- Promoted case: `sort_folio()` does not call `lru_gen_set_refs()`.
- `nr_to_scan`: `try_to_shrink_lruvec()` passes at most `MIN_LRU_BATCH`;
  `run_eviction()` passes at most `MAX_LRU_BATCH`.
- `scan_folios()` return: pages scanned, also when nothing was isolated; the
  isolated count comes back through `isolatedp`.
- `isolate_folios()`: switches to the other type only when a scan returned
  0; with pages scanned and none isolated it scans the same type again.
- `evict_folios()`: calls `try_to_inc_min_seq()` before isolation, and again
  after it when anything was scanned.
- Rejects are re-added by `lruvec_add_folio()`, with `reclaiming` false.
- Retry pass: for rejects that are not active, not mapped, not dirty and not
  under writeback; dirty folios are not retried.
- Dirty file rejects: `shrink_folio_list()` sets `PG_reclaim` and
  `PG_active`, so `lru_gen_folio_seq()` places them at `max_seq - 1`, or at
  `max_seq` with `PG_workingset`.

## Swap slots and the swap cache

**Per-slot state**

- Count: lives in the top `SWP_TB_COUNT_BITS` bits of the slot's table word
  (`mm/swap_table.h`); there is no swap_map array, no SWAP_HAS_CACHE bit and
  no SWAP_MAP_MAX or SWAP_MAP_BAD in this tree.
- Formats of a table word, told apart by the low bits:

| Format | Low bits | Slot state | Test |
|---|---|---|---|
| NULL | word is 0 | free | `swp_tb_is_null()` |
| Shadow | bit 0 set | in use, not cached; count >= 1 | `swp_tb_is_shadow()` |
| PFN | `SWP_TB_PFN_MARK` (`0b10`) | folio in swap cache; count >= 0 | `swp_tb_is_folio()` |
| Bad | word equals `SWP_TB_BAD` | never allocatable | `swp_tb_is_bad()` |

- PFN format: stores the folio's PFN, not a pointer; `swp_tb_to_folio()`
  converts; no helper in `mm/swap_table.h` builds or tests a pointer format.
- Shadow format: used for every in-use uncached slot, also with a NULL
  workingset shadow (`__swap_cache_do_del_folio()` in `mm/swap_state.c`).
- Count 0: only a NULL or a PFN word has it once the cluster lock is dropped;
  `cluster_scan_range()` in `mm/swapfile.c` warns otherwise.
- `swp_tb_get_count()`: returns `-EINVAL` for a bad slot;
  `__swp_tb_get_count()` warns instead, use it only on a countable word.
- Constructors: `shadow_to_swp_tb()`, `pfn_to_swp_tb()` and its wrapper
  `folio_to_swp_tb()`, each takes the flags (count and zero flag) to keep;
  there is no shadow_swp_to_tb().
- Zero-filled marker: `SWP_TB_ZERO_FLAG` in the same word; when
  `SWAP_TABLE_HAS_ZEROFLAG` is 0 it is the per-cluster `zero_bitmap`. There is
  no zeromap bitmap in `struct swap_info_struct`; use
  `__swap_table_test_zero()`.
- `swap_table_get()`: the lockless reader; takes `rcu_read_lock()` itself and
  returns NULL format when the cluster has no table.
- `__swap_table_get()`: accepts the cluster lock or an RCU read section, and
  does not check for a missing table; `folio_maybe_swapped()` uses it under
  RCU with the folio locked.

**Swap entries in page tables**

- `softleaf_t`: defined in `include/linux/mm_types.h` as a typedef of
  `swp_entry_t`; no conversion exists or is needed, there is no
  softleaf_to_swp_entry().
- pte_to_swp_entry(): not in this tree; `softleaf_from_pte()` is the generic
  decoder, and `include/linux/swapops.h` keeps the encoders `swp_entry()`,
  `swp_entry_to_pte()` and the `swp_type()`, `swp_offset()` accessors.
- Old predicates: non_swap_entry(), is_swap_pte(), is_swap_pmd(),
  is_migration_entry(), is_pfn_swap_entry() and is_pte_marker_entry() are
  absent; `is_hwpoison_entry()` remains in `include/linux/swapops.h`.
- `softleaf_from_pte()`: clears the swap-PTE flag bits with
  `pte_swp_clear_flags()`, so exclusive, soft-dirty and uffd state must be
  read from the PTE with `pte_swp_exclusive()`, `pte_swp_soft_dirty()` and
  `pte_swp_uffd()`, as `copy_nonpresent_pte()` in `mm/memory.c` does.
- `softleaf_from_pmd()`: returns the none entry unless
  `CONFIG_ARCH_HAS_PMD_SOFTLEAVES`; only migration and device-private entries
  are valid at PMD level, see `softleaf_is_valid_pmd_entry()`.

**Swap counts**

- `folio_put_swap()`: never frees a slot or the folio; a cached slot whose
  count reaches 0 is freed when the folio leaves the swap cache.
- `swap_put_entries_direct()`: pins the device itself with
  `get_swap_device()`, range-checks against `si->max`, and splits a range
  that crosses clusters.
- `swap_dup_entry_direct()`: takes no device reference and does not check the
  offset; the caller's lock on the live swap PTE must provide both.
- `folio_dup_swap()` and `folio_put_swap()`: act on one cluster; `page ==
  NULL` means every slot of the folio.
- Count 0 to 1: reserved to `folio_dup_swap()`; `swap_dup_entry_direct()`
  only checks this with `VM_WARN_ON_ONCE()`, and `__swap_cluster_dup_entry()`
  accepts count 0 on a cached slot.
- **Potentially unsafe usage**: `swap_put_entries_direct()` without the page
  table lock.
  - Unsafe: while another task can still find the entry and drop the same
    reference; `__swap_cluster_put_entry()` only warns on count 0 and then
    writes the decremented value.
  - Safe: under the PTL of the PTE that holds the entry, as
    `zap_nonpresent_ptes()` in `mm/memory.c` does.
  - Safe: after the entry was removed from the shmem mapping under the xarray
    lock, so the caller is the only owner, as `shmem_free_swap()` in
    `mm/shmem.c` does.

**Initial count and overflow**

- Hibernation slots: start at count 1 in shadow format with no folio
  (`__swap_cluster_alloc_entries()` with a NULL folio); only slots allocated
  for a folio start at 0.
- Pin of a count-0 slot: lasts only while the folio stays locked; any task
  that locks the folio may free it, for example the allocator through
  `cluster_reclaim_range()`, whose callee `__try_to_reclaim_swap()` uses
  `folio_trylock()`.
- Count field: `SWP_TB_COUNT_BITS` wide, at most 4 bits, so
  `SWP_TB_COUNT_MAX` is at most 15.
- Overflow: there is no add_swap_count_continuation(), COUNT_CONTINUED or
  SWAP_MAP_MAX; a table count of `SWP_TB_COUNT_MAX` means the real count is in
  `extend_table` of `struct swap_cluster_info`, an `unsigned int` per slot.
- `extend_table`: allocated per cluster on demand by
  `swap_extend_table_alloc()`, freed by `swap_extend_table_try_free()` once
  every element is 0.
- `swp_tb_get_count()` and `__swap_count()`: return the saturated table
  value; of the count readers only `swp_swapcount()` reads `extend_table`.
- `swap_dup_entries_cluster()`: on overflow drops the cluster lock, tries a
  `GFP_ATOMIC` allocation, and on failure undoes the slots it raised and
  returns `-ENOMEM`.
- `folio_dup_swap()`: can therefore fail; `ttu_anon_swapbacked_folio()` in
  `mm/rmap.c` fails the unmap.
- Fork: `copy_nonpresent_pte()` turns any dup failure into `-EIO`;
  `copy_pte_range()` drops both PTLs, calls `swap_retry_table_alloc()` with
  `GFP_KERNEL`, and retries.
- **Potentially unsafe usage**: ignoring the return value of
  `folio_dup_swap()`.
  - Unsafe: when the slot's count can already be `SWP_TB_COUNT_MAX - 1`; the
    swap entry is installed without its reference.
  - Safe: right after `folio_alloc_swap()` with the folio still locked, where
    the count is 0 and `__swap_cluster_dup_entry()` cannot overflow, as
    `shmem_writeout()` does.

**Swap cache operations**

| Job | Function | Caller must hold |
|---|---|---|
| look up | `swap_cache_get_folio()` | device stabilised: `get_swap_device()`, a locked swap-cache folio, or the lock over what holds the entry (PTL) |
| add at swap-out | `folio_alloc_swap()` | folio locked and uptodate; it calls `__swap_cache_add_folio()` under the cluster lock |
| add at swap-in | `swap_cache_alloc_folio()` | device stabilised; allocates the folio, returns it locked and cached |
| delete | `swap_cache_del_folio()` | folio locked, in swap cache, not under writeback |
| delete, locked | `__swap_cache_del_folio()` | the same, plus the cluster lock |
| replace | `__swap_cache_replace_folio()` | both folios locked, cluster lock |

- swap_cache_add_folio(): not in this tree; `__swap_cache_add_folio()` has
  one caller, `__swap_cluster_alloc_entries()` in `mm/swapfile.c`.
- Lookup without a stabilised device: `__swap_type_to_info()` in `mm/swap.h`
  warns when `users` is zero.
- `__swap_cache_del_folio()`: leaves the folio's cache references to the
  caller; `swap_cache_del_folio()` drops them itself, `folio_nr_pages()` of
  them.
- `__swap_cache_del_folio()`: writes shadow format to every slot, then frees
  the slots whose count is 0.
- `__swap_cache_replace_folio()`: changes only the table; the caller sets
  `new->swap` and `PG_swapcache` on the new folio first and moves the
  references, as `shmem_replace_folio()` does.
- **Potentially unsafe usage**: `swap_cache_del_folio()` on a dirty folio.
  - Unsafe: when a slot still has a count; the slot stays in use with stale
    data on the device.
  - Safe: when every count is 0, which `folio_free_swap()` tests first.

**Swapbacked, swapcache and mapping**

- Test to choose between page-cache and swap-cache operations:
  `folio_test_swapcache()` in `include/linux/page-flags.h`, as
  `folio_mapping()` does.
- Shmem folio in both caches at once: happens with the folio locked, for
  example in `shmem_writeout()` between `folio_alloc_swap()` and
  `shmem_delete_from_page_cache()`, and in `shmem_swapin_folio()` between
  `shmem_add_to_page_cache()` and `swap_cache_del_folio()`.
- In that window: `folio_test_swapcache()` is true while `folio->mapping` is
  the shmem mapping, so the test selects the right operations only under the
  folio lock.

**Swap cache folio mapping**

- Shmem folio in the swap cache: `folio->mapping` is NULL, set by
  `shmem_delete_from_page_cache()`, outside the window described under
  "Swapbacked, swapcache and mapping".
- Folio created by `swap_cache_alloc_folio()`: `folio->mapping` is NULL and
  `folio_test_anon()` is false until `do_swap_page()` maps it, so
  `folio->mapping` cannot tell an anon swap-cache folio from a shmem one.
- `folio->swap`: shares storage with `folio->private`, not with
  `folio->index`.
- `swap_space`: its initialiser sets only `a_ops`, so `host` is NULL;
  `swap_aops` has `dirty_folio` and, under `CONFIG_MIGRATION`,
  `migrate_folio`.
- Writeback: not reachable through the result; `pageout()` in `mm/vmscan.c`
  calls `swap_writeout()` directly.
- **Potentially unsafe usage**: using `host` or `i_pages` of the mapping that
  `folio_mapping()` returned, for a folio that can be in the swap cache.
  - Unsafe: dereferencing `host` or taking the `i_pages` lock; `host` of
    `swap_space` is NULL.
  - Safe: test `folio_test_swapcache()` first and take the cluster lock with
    `swap_cluster_get_and_lock_irq()` instead, as `__remove_mapping()` in
    `mm/vmscan.c` does.
  - Safe: pass `host` only to `mapping_can_writeback()` before any
    dereference, as `folio_clear_dirty_for_io()` does; `inode_to_bdi()`
    returns `noop_backing_dev_info` for a NULL inode.

**Swap cache removal conditions**

- folio_swapped(): not in this tree; the test is `folio_maybe_swapped()`,
  static in `mm/swapfile.c`.
- `mem_cgroup_swap_full()`: not tested by `folio_free_swap()`; a caller that
  wants it tests it first, as `should_try_to_free_swap()` in `mm/memory.c`
  does; `__try_to_reclaim_swap()` tests it, when called with `TTRS_FULL`,
  before its own `swap_cache_del_folio()`.
- `pm_suspended_storage()`: when true, `folio_swapcache_freeable()` refuses.
- Folio lock: required but only asserted, with `VM_BUG_ON_FOLIO()`.
- False "unused": not possible while the caller holds the folio lock, because
  a count leaves 0 only through `folio_dup_swap()`.
- Return `true`: also means the folio was marked dirty.
- Return `false`: the folio may not be in the swap cache at all.

**Swap cache lookup rechecks**

- Before the lookup: stabilise the device with `get_swap_device()`, as
  `do_swap_page()` does.
- Match test: the returned folio may be a large folio whose `folio->swap` is
  lower than the entry; `folio_matches_swap_entry()` rounds the entry down.
- **Potentially unsafe usage**: using the returned folio without lock and
  `folio_matches_swap_entry()`.
  - Unsafe: when mapping it, changing its swap count or reading
    `folio->swap`; the folio may have left the swap cache or serve another
    entry.
  - Safe: reading only `folio_test_uptodate()` as a hint, as `mincore_swap()`
    does.
  - Safe: locking it and calling `folio_free_swap()`, which rechecks the
    folio's own state, as `try_to_unuse()` does.
  - Safe: locking it and comparing `folio_test_swapcache()` and
    `folio->swap.val` with the entry, only after large folios were rejected,
    as `move_swap_pte()` in `mm/userfaultfd.c` does; its caller
    `move_pages_ptes()` returns `-EBUSY` for a large folio.
- Lookup found nothing, swap-in: `do_swap_page()` does not recheck the PTE
  first; `swapin_sync()` or `swapin_readahead()` add a folio through
  `swap_cache_alloc_folio()`.
- Guard on that path: `__swap_cache_add_check()` under the cluster lock
  rejects a slot with count 0 or one already cached.
- Swap-in failed: `do_swap_page()` returns `VM_FAULT_OOM` only if
  `pte_same()` still holds under the PTL.
- Lookup found nothing, entry moved without a folio: under the PTL recheck
  that the PTE is unchanged and that `swap_cache_has_folio()` is still false;
  `move_swap_pte()` returns `-EAGAIN` otherwise.

## Swap devices and allocation

**Swap device and clusters**

- `struct swap_info_struct` is defined in `include/linux/swap.h`;
  `struct swap_cluster_info` in `mm/swap.h`.
- There is no swap_map array, no zeromap bitmap, no cont_lock and no
  SWP_FS_OPS flag in this tree, and no swap count continuation pages.
- Per-slot state: one `atomic_long_t` in the cluster's `table`; the entry kinds
  are in the comment at the top of `mm/swap_table.h`.
- `ci->memcg_table`: per-slot memcg id under `CONFIG_MEMCG`, written by
  `__swap_cgroup_set()`.
- `ci->flags == CLUSTER_FLAG_NONE`: the cluster is on no list, as left by
  `isolate_lock_cluster()`.
- `si->ops`: see "Swap device operations".
- `si->avail_list` on `swap_avail_head`: one plist, not one per node.
- `si->inuse_pages`: atomic; the page count in it changes under `ci->lock`; it
  carries `SWAP_USAGE_OFFLIST_BIT`, so read it with `swap_usage_in_pages()`.
- `SWP_HIBERNATION` in `si->flags`: swapoff returns `-EBUSY` while it is set.

| Lock | Protects |
|---|---|
| `swapon_mutex` | `si->swap_file` as `swap_start()` walks it |
| `swap_lock` | `swap_info[]`, `nr_swapfiles`, `swap_active_head`, `total_swap_pages`, `SWP_USED`, `SWP_WRITEOK`, `SWP_HIBERNATION` |
| `percpu_swap_cluster.lock` | this CPU's `si[]` and `offset[]` |
| `si->global_cluster_lock` | `si->global_cluster`; taken only without `SWP_SOLIDSTATE` |
| `ci->lock` | `count`, `flags`, `order`, `extend_table`, `memcg_table`, `zero_bitmap`, writes to table entries |
| `si->lock` | the cluster lists and `ci->list`; `SWP_WRITEOK` together with `swap_lock` |
| `swap_avail_lock` | `swap_avail_head`, `SWAP_USAGE_OFFLIST_BIT` |

- Allocator order: `percpu_swap_cluster.lock` -> `si->global_cluster_lock` ->
  `ci->lock` -> `si->lock`.
- `ci->lock` is outside `si->lock`: `move_cluster()` takes `si->lock` with
  `ci->lock` held.
- `isolate_lock_cluster()`: holds `si->lock`, so it only `spin_trylock()`s
  `ci->lock` and skips a contended cluster.
- `swap_avail_lock`: innermost; taken under `ci->lock` by `swap_usage_add()`
  and `swap_usage_sub()`, and under `si->lock` at swapon and swapoff.
- `swap_alloc_slow()`: takes `swap_avail_lock` under the local lock and drops
  it before it touches a device.
- Folio lock is outside `ci->lock`; `swap_cluster_get_and_lock()` asserts it.

**Swap device lifetime**

- `get_swap_device()` tests, in order: `entry.val` non-zero; type below
  `MAX_SWAPFILES` and `swap_info[type]` non-NULL (`swap_type_to_info()`);
  `percpu_ref_tryget_live(&si->users)`; then offset below `si->max`.
- `get_swap_device()` does not test `si->flags` or `nr_swapfiles`.
- swapoff before `percpu_ref_kill()`: `del_from_avail_list()` clears
  `SWP_WRITEOK`, then `wait_for_allocation()`, then `try_to_unuse()`.
- swapoff after `percpu_ref_kill()`, `synchronize_rcu()` and
  `wait_for_completion()`: frees the extent tree, `si->global_cluster`,
  `si->cluster_info` with every cluster's tables, and closes `si->swap_file`.
- A reference holds off that second half only; there is no swap_map or
  zeromap to free.
- `si->max` and `si->cluster_info`: zeroed by swapoff after
  `wait_for_completion()`.
- `synchronize_rcu()` in swapoff: an entry read and used inside one RCU
  read-side section needs no reference.
- A slot in use keeps `try_to_unuse()` looping, so swapoff never reaches
  `percpu_ref_kill()`; that is why a locked swap-cache folio or a held PTL
  over a swap PTE pins the device.
- `__swap_entry_to_info()`: indexes `swap_info[]` with no bound or NULL test,
  so the entry must be a real swap entry of a device that was swapped on.
- `swap_cache_has_folio()` and the other `swap_cache_` lookups in
  `mm/swap_state.c` call `__swap_entry_to_cluster()` and inherit its rules.
- **Potentially unsafe usage**: calling `__swap_entry_to_info()`,
  `__swap_entry_to_cluster()` or `__swap_offset_to_cluster()` with no
  `get_swap_device()` reference.
  - Unsafe: on an entry read from a page table or a shmem mapping after the
    PTL or RCU section it was read under has ended; swapoff can have freed
    `si->cluster_info`.
  - Safe: on `folio->swap` of a folio that is locked and tested to be in the
    swap cache; `swap_cluster_get_and_lock()` asserts both.
  - Safe: with the PTL held over the swap PTE, as `copy_nonpresent_pte()` does
    around `swap_dup_entry_direct()`, which reaches
    `__swap_offset_to_cluster()`; `unuse_pte()` needs that PTL.
  - Safe: inside the `rcu_read_lock()` section that read the entry, as
    `filemap_cachestat()` does with `swap_cache_get_shadow()`.
  - Safe: after `get_swap_device()` returned non-NULL, as `do_swap_page()`
    does.

**Slot allocation**

- `folio_alloc_swap()` takes only the folio; there is no `gfp_t` argument.
- Return values: 0; `-EAGAIN` for a large folio without `CONFIG_THP_SWAP`;
  `-EINVAL` above `SWAPFILE_CLUSTER` pages; `-ENOMEM` for no slots or a failed
  memcg charge. It never returns `-ENOSPC`.
- On success the slots hold PFN entries with swap count 0; only the swap cache
  pins them.
- `folio_dup_swap()`: raises the count when a swap entry replaces the folio,
  as `shmem_writeout()` does.
- Failed memcg charge: `swap_cache_del_folio()` takes the folio out and frees
  the slots; there is no put_swap_folio().
- `mem_cgroup_try_charge_swap()` also runs when no slots were found, to record
  `MEMCG_SWAP_FAIL`.
- `swap_alloc_slow()`: walks the single `swap_avail_head` plist and
  `plist_requeue()`s each device it visits.
- Large folio in `swap_alloc_slow()`: returns after the first device it could
  pin, with or without slots.
- `swap_sync_discard()`: order 0 only, after the local lock is dropped; if it
  discarded anything `folio_alloc_swap()` restarts from the per-CPU cache.
- `cluster_alloc_swap_entry()` returns 0 at once for a large order on a device
  without `SWP_BLKDEV`.
- Cluster order in `cluster_alloc_swap_entry()`:
  1. without `SWP_SOLIDSTATE`: `si->global_cluster->next[order]`
  2. with `SWP_PAGE_DISCARD`: `free_clusters`
  3. if `order < PMD_ORDER`: every cluster on `nonfull_clusters[order]`
  4. without `SWP_PAGE_DISCARD`: `free_clusters`
  5. if `vm_swap_full()`: `swap_reclaim_full_clusters()`, for any order
  6. if `order < PMD_ORDER`: one cluster from `frag_clusters[order]`
  7. order 0 only: `frag_clusters[o]` then `nonfull_clusters[o]` for each
     higher `o`

**Allocator local lock**

- `swap_cluster_populate()` is in `mm/swapfile.c`; `swap_cluster_alloc_table()`
  is the bare allocator it calls, and drops no lock itself.
- `percpu_swap_cluster.lock` is taken with `local_lock()`, in
  `folio_alloc_swap()` and `swap_alloc_hibernation_slot()`.
- `swap_cluster_populate()` is reached only from `isolate_lock_cluster()`, for
  a cluster that had `CLUSTER_FLAG_FREE`.
- `swap_cluster_populate()` asserts the local lock, `ci->lock`, and
  `si->global_cluster_lock` when `SWP_SOLIDSTATE` is clear.
- Sleeping attempt: fixed flags `__GFP_HIGH | __GFP_NOMEMALLOC | GFP_KERNEL`;
  no caller supplies a gfp mask.
- After relocking there is no recheck and no spare table to free; the cluster
  stayed off every list with `CLUSTER_FLAG_NONE`.
- Allocation failure: the cluster goes back to `si->free_clusters`, `ci->lock`
  is dropped, NULL is returned with the local lock and
  `si->global_cluster_lock` still held.
- `alloc_swap_scan_list()` on `si->free_clusters` may therefore sleep and
  change CPU; on an `SWP_SOLIDSTATE` device `alloc_swap_scan_cluster()` writes
  the cache of the CPU it ends on.
- **Potentially unsafe usage**: calling `isolate_lock_cluster()` without
  `percpu_swap_cluster.lock`.
  - Unsafe: on `si->free_clusters`; `swap_cluster_populate()` asserts the
    local lock and, when the atomic allocation fails, unlocks it.
  - Safe: on `si->full_clusters`, as `swap_reclaim_full_clusters()` does from
    `swap_reclaim_work()`; no cluster there has `CLUSTER_FLAG_FREE`.

**Swap I/O**

- `swap_writeout()` order: `folio_free_swap()`, `arch_prepare_to_swap()`,
  zero-filled test, `zswap_store()`, `mem_cgroup_zswap_writeback_enabled()`,
  then `__swap_writepage()`.
- Zero-filled mark: set by `swap_zeromap_folio_set()` in the cluster's swap
  table or `ci->zero_bitmap`; there is no si->zeromap.
- `swap_read_folio()`, after its zero-mark and `zswap_load()` tests, and
  `__swap_writepage()` have no per-device branch; both end in
  `swap_add_folio()`.
- Every device queues, block devices too: `swap_add_folio()` adds the folio
  to `ctx->sio`.
- `swap_add_folio()` sends the batch itself in three cases: the new folio
  cannot merge, the batch reached `SWAP_CLUSTER_MAX` folios, or it is a write
  to an `SWP_SYNCHRONOUS_IO` device.
- A read queued into an empty context is never sent by `swap_read_folio()`
  alone, on any device.
- There is no swap_read_unplug() or swap_write_unplug(); the flush calls are
  `swap_read_submit()` and `swap_write_submit()` in `mm/page_io.c`.
- Both submit calls return at once when `ctx->sio` is NULL.
- Until submit, a queued read folio stays locked and a queued write folio
  stays under writeback; `swap_read_end()` and `swap_write_end()` release them.
- `mempool_alloc(sio_pool, GFP_NOIO)` in `swap_add_folio()` can sleep.
- **Unsafe usage**: passing a NULL `struct swap_io_ctx` pointer;
  `swap_add_folio()` dereferences it.
  - Safe: a zeroed `struct swap_io_ctx ctx = {};` on the stack, as
    `swapin_sync()` does.
- **Potentially unsafe usage**: returning without the submit call.
  - Unsafe: after any call that may have queued a folio, such as
    `swap_read_folio()`, `read_swap_cache_async()`, `swap_writeout()` or
    `shmem_writeout()`.
  - Safe: before anything was queued, as the early error exits of
    `zswap_writeback_entry()` do.
  - Safe: one submit on the common exit, as `shrink_folio_list()` does.
- **Unsafe usage**: waiting on a folio that sits in the caller's own context.
  - Safe: submit before the folio goes to code that locks it, as
    `swapin_sync()` does before it returns the folio to `do_swap_page()`.
- **Unsafe usage**: queuing reads and writes in one context; `swap_add_folio()`
  picks the submit direction from the folio being added.
  - Safe: a context used for one direction only, as `shrink_folio_list()`
    does for writes.
- `may_enter_fs()` in `mm/vmscan.c`: a swap-cache folio needs only `__GFP_IO`
  unless `si->ops->flags` has `SWAP_OPS_F_REQUIRE_NOFS`; there is no
  SWP_FS_OPS or folio_swap_flags().

**Swap device operations**

- `struct swap_ops` is in `include/linux/swap_ops.h`; each device points at one
  through `si->ops`.
- `flags`: only `SWAP_OPS_F_REQUIRE_NOFS` exists; `may_enter_fs()` reads it.
- `can_merge()`: whether a folio may join the batch after the previous folio.
- `submit_write()` and `submit_read()`: send the whole batch `ctx->sio` to
  `ctx->sis`.
- All three hooks are called with no NULL test, by `swap_can_merge()`,
  `swap_write_submit()` and `swap_read_submit()`.
- Not decided by `struct swap_ops`: `SWP_SYNCHRONOUS_IO`, `SWP_BLKDEV` and
  `SWP_STABLE_WRITES` stay in `si->flags`; `swap_activate` and
  `swap_deactivate` stay in `struct address_space_operations`.
- There is no SWP_FS_OPS flag and no swap_rw method in this tree.
- `setup_swap_extents()`: installs `swap_bdev_ops` on every device before it
  calls `->swap_activate()`.
- `swap_fs_activate()`: called from a filesystem's `->swap_activate()`, it
  replaces `si->ops` and adds one extent for the whole file; for example
  `nfs_swap_activate()`.
- A swap file whose `->swap_activate()` only adds extents, or that goes through
  `generic_swapfile_activate()`, keeps `swap_bdev_ops` and gets bios to
  `si->bdev`.
- A filesystem submit hook calls `swap_fs_prepare_rw()`, then must call
  `sio->iocb.ki_complete()` itself when the I/O call returns anything but
  `-EIOCBQUEUED`, as `nfs_swap_submit_write()` does.
- `ctx->sio` and `ctx->sis` are cleared as soon as the hook returns; the
  completion handler frees the `struct swap_iocb` to `sio_pool`.

## Swapping out and in

**Swap-out ordering**

- Names: there is no swap_duplicate(), swap_free(), put_swap_folio(),
  __delete_from_swap_cache(), swap_writepage() or SWAP_HAS_CACHE here. The
  count is raised by `folio_dup_swap()` and dropped by `folio_put_swap()`
  (`mm/swapfile.c`); the write is `swap_writeout()` (`mm/page_io.c`); the
  cache pin is the swap table entry that holds the folio.
- `folio_alloc_swap()`: requires the folio locked and uptodate and not yet
  in the swap cache; it adds the folio itself, and the slots start with
  count 0.
- Per-PTE sequence: `try_to_unmap_one()` clears the PTE, then
  `ttu_anon_swapbacked_folio()` in `mm/rmap.c` runs `folio_dup_swap()`,
  `arch_unmap_one()`, `folio_try_share_anon_rmap_pte()`, `set_pte_at()` in
  that order.
- Unmap failure after the count was raised: `ttu_anon_swapbacked_folio()`
  calls `folio_put_swap()` for that page; `try_to_unmap_one()` then restores
  the PTE with `set_ptes()` and aborts the walk.
- `activate_locked` in `shrink_folio_list()`: calls `folio_free_swap()` only
  when `mem_cgroup_swap_full()` or `folio_test_mlocked()`; it returns false
  while any slot of the folio has a count or the folio is under writeback,
  so a partly unmapped folio keeps its slots.
- Folio lock during the write: not held throughout. `__swap_writepage()`
  calls `folio_start_writeback()` then `folio_unlock()`; in that window
  `folio_swapcache_freeable()` refuses a folio under writeback.
- After `PAGE_SUCCESS`: `shrink_folio_list()` retakes the lock with
  `folio_trylock()` and retests dirty and writeback before
  `__remove_mapping()`.
- `__swap_writepage()`: does not submit on its own; it queues the folio in
  the caller's `struct swap_io_ctx` with `swap_add_folio()`, which submits
  the earlier batch first when the folio cannot merge with it, and submits
  the folio's batch when that is full or the device is
  `SWP_SYNCHRONOUS_IO`; otherwise the I/O starts at `swap_write_submit()`,
  which `shrink_folio_list()` calls last.
- Write error: `swap_write_end()` in `mm/page_io.c` redirties the page and
  clears the reclaim flag; there is no __end_swap_bio_write().
- `arch_prepare_to_swap()` failure in `swap_writeout()`: folio redirtied and
  unlocked, negative error returned, not `AOP_WRITEPAGE_ACTIVATE`.
- Removal: `__remove_mapping()` takes the cluster lock with
  `swap_cluster_get_and_lock_irq()` and calls `__swap_cache_del_folio()`,
  which stores the shadow and frees every slot whose count is 0 in the same
  step. No separate call drops a cache reference afterwards.

**Swap-in at a fault**

- Check after the folio lock: `folio_matches_swap_entry()` in `mm/swap.h`.
  It compares `folio->swap` with the entry rounded down to the folio size,
  so a large folio that covers the entry matches; a plain compare of
  `folio->swap.val` with the entry does not.
- Names: there is no swap_free() or swap_free_nr() here; `do_swap_page()`
  drops the count with `folio_put_swap()`.
- Order, under folio lock and PTL: `arch_swap_restore()`, rmap add,
  `folio_put_swap()`, `set_ptes()`, `folio_free_swap()` if
  `should_try_to_free_swap()`, `folio_unlock()`.
- `folio_put_swap()` before `set_ptes()`: frees no slot even at count 0. It
  calls `swap_put_entries_cluster()` with `reclaim_cache` false, and that
  function leaves slots that hold a folio to `__swap_cache_del_folio()`.
- Large folio whose PTE range check fails under the PTL, folio already
  anon: one page is mapped.
- Large folio whose PTE range check fails under the PTL, folio not anon:
  `swap_cache_del_folio()` removes it and the fault returns without
  mapping.

**Reading a folio in**

- Names: there is no alloc_swap_folio(), swapin_folio(),
  swapcache_prepare() or __read_swap_cache_async() here. `swapin_sync()` in
  `mm/swap_state.c` is the synchronous path.
- Choice in `do_swap_page()`: `SWP_SYNCHRONOUS_IO` in `si->flags` alone;
  `__swap_count()` is not tested.
- `swapin_sync()`: gets `thp_swapin_suitable_orders(vmf) | BIT(0)` as
  `orders` from `do_swap_page()`; allocation, memcg charge and swap cache
  insertion all happen in `swap_cache_alloc_folio()`.
- Every path puts the folio in the swap cache before the read. The comment
  "skipping swap cache" at the `shmem_swap_alloc_folio()` call does not
  describe `swapin_sync()`.
- `thp_swapin_suitable_orders()`: filters on `userfaultfd_armed()`,
  `zswap_never_enabled()`, THP settings, alignment and `can_swapin_thp()`
  only. Zero flag, cached slots and counts are left to
  `__swap_cache_add_check()`.
- `swap_vma_readahead()` and `swap_cluster_readahead()`: call
  `swap_cache_read_folio()` per entry, then fetch the target with
  `swap_cache_read_folio_sync()`. `read_swap_cache_async()` is not on this
  path; `mm/madvise.c` uses it.
- Failure value: `swapin_sync()` returns an `ERR_PTR()` and, with
  `CONFIG_SWAP`, never NULL; `swapin_readahead()` returns NULL and never an
  `ERR_PTR()`. `do_swap_page()` tests `IS_ERR_OR_NULL()`.
- `swap_read_folio()`: after the zero-flag and `zswap_load()` checks it
  queues the folio in the caller's `struct swap_io_ctx` with
  `swap_add_folio()`. There is no swap_read_folio_fs(),
  swap_read_folio_bdev_sync() or swap_read_folio_bdev_async();
  `swap_read_submit()` calls `submit_read` of `struct swap_ops`.

**Large folio swap-in**

- `swap_cache_alloc_folio()` in `mm/swap_state.c`: returns a new folio or an
  `ERR_PTR()`, never NULL and never an existing folio. There is no
  new_page_allocated argument.

| Case | `__swap_cache_add_check()` | `swap_cache_alloc_folio()` |
|---|---|---|
| target slot holds a folio | `-EEXIST` | returned at once, at any order |
| target slot has count 0, or `ci->table` is NULL | `-ENOENT` | returned at once, at any order |
| another slot of the range is unsuitable | `-EBUSY` | retried at the next lower order in `orders` |
| folio allocation or memcg charge fails | 0 | `-ENOMEM`, retried like `-EBUSY` |
| `orders` is 0, or its highest order is above `SWAPFILE_CLUSTER` pages | not reached | `-EINVAL` |

- Target slot tests: run first, folio test before count test, so a cached
  target gives `-EEXIST` whatever the rest of the range holds.
- `-EEXIST`: handled by callers. `swap_cache_read_folio()` and
  `swapin_sync()` loop back to `swap_cache_get_folio()`;
  `zswap_writeback_entry()` returns the error.
- Unsuitable range: any slot of the aligned range that holds a folio, has
  count 0, has a zero flag different from the target slot's, or has a memcg
  id different from the target slot's.
- Memcg test: made only in the second check, where `memcg_id` is not NULL.
- Two checks in `__swap_cache_alloc()`, each under `ci->lock`: one before
  allocating, one just before insertion; a failure of the second frees the
  folio and returns the same codes.
- Not tested in `__swap_cache_add_check()`: zswap state. Callers pass no
  large order when `zswap_never_enabled()` is false; see
  `thp_swapin_suitable_orders()` and `shmem_swap_alloc_folio()`.
- `swap_zeromap_batch()`: static in `mm/page_io.c`; no caller of
  `swap_cache_alloc_folio()` pre-filters with it.
- Returned folio: locked, in the swap cache at the rounded-down entry,
  charged, passed to `folio_add_lru()`, not uptodate; the caller starts the
  read.

**Retrying a swap-in**

- Return value: `ERR_PTR(-EBUSY)`, and only when the order that failed was
  the lowest one set in `orders`.
- Callers that never see `-EBUSY`: every caller with `BIT(0)` in `orders`,
  because at order 0 `__swap_cache_add_check()` returns before the range
  loop. These are `swap_cache_read_folio()`, `zswap_writeback_entry()` and
  `do_swap_page()` through `swapin_sync()`, large orders included.
- Caller that can see `-EBUSY`: `shmem_swap_alloc_folio()` in `mm/shmem.c`,
  which passes a single `BIT(order)` to `swapin_sync()`.
- `shmem_swap_alloc_folio()`: on any error at a nonzero order it retries
  once at order 0 with the same `entry`; an error at order 0 is returned
  unchanged. It does not call `folio_put()` and does not adjust `entry`;
  `__swap_cache_alloc()` frees its own folio on failure.
- **Unsafe usage**: retrying after `-EBUSY` with the same `orders`;
  `__swap_cache_add_check()` returns `-EBUSY` again for as long as the
  slot state lasts.
  - Safe: retry once with a lower order and treat an order 0 error as
    final, as `shmem_swap_alloc_folio()` does.
  - Safe: pass `BIT(0)` together with the large orders, so the fallback
    happens inside `swap_cache_alloc_folio()`, as `do_swap_page()` does.
- **Unsafe usage**: passing an entry rounded down to the folio size as the
  target, in place of the entry of the slot wanted;
  `__swap_cache_add_check()` tests the target slot itself for `-EEXIST` and
  `-ENOENT`, and an order 0 retry reads the slot it is given.
  - Safe: pass the entry of the faulting slot; `__swap_cache_alloc()`
    rounds it down. `shmem_swapin_folio()` adds the index offset to the
    stored entry before the call.
- Folio after a retry: may be smaller than the entry in the mapping.
  `shmem_swapin_folio()` tests `order > folio_order(folio)` and calls
  `shmem_split_large_entry()` before it inserts the folio.
- Folio from `swapin_sync()`: may be an existing swap cache folio, returned
  unlocked; the caller locks it and checks `folio_matches_swap_entry()`.
- `-EEXIST` to `shmem_get_folio_gfp()`: never comes from `swapin_sync()`,
  which loops on it. `shmem_swapin_folio()` sets it itself, for example when
  `shmem_confirm_swap()` or `folio_matches_swap_entry()` fails; another
  error of `swapin_sync()` is passed up while `shmem_confirm_swap()` still
  finds the entry.

**Shmem and swap**

- Names: there is no swap_shmem_alloc() here; `shmem_writeout()` raises the
  count with `folio_dup_swap(folio, NULL)` before
  `shmem_delete_from_page_cache()`.
- Stale check in `shmem_swapin_folio()`: `folio_matches_swap_entry()` and
  `shmem_confirm_swap()` are both tested after `folio_lock()`. The folio
  test alone does not show that the mapping still holds the entry.
- `shmem_confirm_swap()`: reads the slot under `rcu_read_lock()` only, not
  the `i_pages` lock.
- `shmem_add_to_page_cache()`: with `expected` set it walks every entry in
  the folio's range and requires consecutive swap values that cover it
  exactly; otherwise `-EEXIST`.
- Large entry value: the swap entry of its first page. For an index inside
  it, `shmem_swapin_folio()` adds `index - round_down(index, 1 << order)`
  to the offset before the swap cache lookup.
- After the folio is found: `shmem_swapin_folio()` rounds `swap` and
  `index` down to the folio size before the locked checks.
- `shmem_free_swap()`: uses `xas_load()` and `xas_store()` under
  `xas_lock_irq()`, not `xa_cmpxchg_irq()`, then
  `swap_put_entries_direct()`. It leaves a large entry in place, and
  returns 0, when the entry reaches outside the range it was given.

## Memory cgroup charge

**Charging a folio**

- `commit_charge()`: stores a `struct obj_cgroup` pointer in
  `folio->memcg_data`, not a `struct mem_cgroup` pointer.
- LRU folio: `memcg_data` is the objcg pointer with no flag bits.
- Kmem page: `memcg_data` is the objcg pointer with `MEMCG_DATA_KMEM`.
- Reference held: one objcg reference per folio, taken by
  `get_obj_cgroup_from_memcg()` in `charge_memcg()`.
- `charge_memcg()`: takes no css reference for the folio; the folio does not
  pin the memcg.
- `folio_memcg()`: reads `objcg->memcg` through `obj_cgroup_memcg()`, which
  asserts `rcu_read_lock()` or `cgroup_mutex`.
- `memcg_reparent_objcgs()`: rewrites `objcg->memcg` to the parent at offline,
  so `folio_memcg()` can return a different memcg for the same folio later.
- `get_mem_cgroup_from_folio()`: use it to keep the memcg past the RCU
  section.
- Root objcg: `obj_cgroup_get()` and `obj_cgroup_put()` do nothing for it.
- `charge_memcg()`: calls `try_charge_memcg()` directly, not `try_charge()`;
  it skips the call when `obj_cgroup_is_root(objcg)` and still commits.
- Objcg choice: `charge_memcg()` takes the objcg of `folio_nid(folio)`; each
  memcg has one objcg per node in `memcg->nodeinfo[nid]->objcg`.
- Page cache add: `filemap_add_folio()` charges; `__filemap_add_folio()` does
  not.
- `AS_KERNEL_FILE` mappings: `filemap_add_folio()` charges the root memcg via
  `set_active_memcg()`.
- hugetlb: there is no mem_cgroup_hugetlb_try_charge() here;
  `mem_cgroup_charge_hugetlb()` charges and commits in one call.
- Swap-in: `mem_cgroup_swapin_charge_folio(folio, id, mm, gfp)` gets the id
  from its caller and resolves it with `mem_cgroup_from_private_id()`.
- There is no lookup_swap_cgroup_id() and no mem_cgroup_from_id() here.
- `__swap_cache_alloc()` in `mm/swap_state.c`: charges after the folio is in
  the swap cache, and removes it again if the charge fails.
- Folio of order > 1: after the charge, `folio_memcg_alloc_deferred()` is
  called and the folio is dropped if it fails; for example in
  `__swap_cache_alloc()`.

**Enforcing the limits**

- Forced charges in `try_charge_memcg()`, complete list: `PF_MEMALLOC` tasks,
  `__GFP_NOFAIL`, `__GFP_HIGH`.
- `nomem` label: every failure path reaches it, including the ones taken
  before any reclaim, and it returns `-ENOMEM` only when neither
  `__GFP_NOFAIL` nor `__GFP_HIGH` is set.
- `GFP_ATOMIC`: contains `__GFP_HIGH`, so a non-blocking `GFP_ATOMIC` charge
  is forced over the limit and does not fail.
- Dying tasks: not forced. `try_charge_memcg()` does not test `TIF_MEMDIE` or
  a pending fatal signal to let a charge through.
- OOM victim whose `oom_mm` has `MMF_OOM_SKIP`: goes to `nomem` before
  reclaim.
- `consume_stock()` hit: `try_charge_memcg()` returns 0 without touching a
  page counter.
- OOM kill: synchronous, inside the charge. `mem_cgroup_oom()` calls
  `mem_cgroup_out_of_memory()`, which takes `oom_lock`.
- There is no memcg_may_oom field here.
- `mem_cgroup_oom()` is reached only when all of these hold:
  - the charge of `nr_pages` (not the batch) failed
  - the task is not `PF_MEMALLOC` and not `task_in_memcg_oom()`
  - `gfpflags_allow_blocking()` is true
  - the task is not an OOM victim with `MMF_OOM_SKIP`
  - reclaim, then one `drain_all_stock()`, left no margin
  - `__GFP_NORETRY` is clear
  - the last reclaim freed nothing, or `nr_pages` is above
    `1 << PAGE_ALLOC_COSTLY_ORDER`
  - `MAX_RECLAIM_RETRIES` is used up
  - `__GFP_RETRY_MAYFAIL` is clear
  - not (`passed_oom` and `task_is_dying()`)
- `mem_cgroup_oom()` returning false: the charge goes to `nomem`.
- v1 `oom_kill_disable`: `memcg1_oom_prepare()` returns false, no kill. It
  sets `current->memcg_in_oom` only when `current->in_user_fault`.

**High limit handling**

- High check: runs only at `done_restock`. A charge served by
  `consume_stock()` and a forced charge both return before it.
- Inline reclaim: `try_charge_memcg()` calls
  `__mem_cgroup_handle_over_high(gfp_mask)` with the charge's own gfp mask.
- Conditions for the inline call: `current->memcg_nr_pages_over_high` above
  `MEMCG_CHARGE_BATCH`, no `PF_MEMALLOC`, `gfpflags_allow_blocking()`.
- `mem_cgroup_handle_over_high()`: inline wrapper in
  `include/linux/memcontrol.h` that tests the counter;
  `resume_user_mode_work()` calls it with `GFP_KERNEL`.
- Context test: `!in_task()`, not `in_interrupt()`.
- Non-task context: only `memory.high` queues `high_work`; `swap.high` is
  ignored there.
- Memcg used by the handler: `get_mem_cgroup_from_mm(current->mm)`. The memcg
  that was charged is not recorded.
- `__mem_cgroup_handle_over_high()`: skips reclaim and sleep when
  `task_is_dying()`; it has no `__GFP_NOFAIL` test.
- Sleep: skipped when the penalty is at most `HZ / 100`.
- Sleep: happens only once `reclaim_high()` reclaimed nothing and
  `MAX_RECLAIM_RETRIES` is used up.

**Per-CPU charge caches**

- `struct memcg_stock_pcp`: `NR_MEMCG_STOCK` slots, `cached[]` and
  `nr_pages[]`. `nr_pages[]` is `uint8_t`.
- `struct obj_stock_pcp`: a separate per-CPU `obj_stock` with its own lock and
  `NR_OBJ_STOCK` slots, `cached[]` and `nr_bytes[]`.
- Slab stat deltas in `struct obj_stock_pcp`: held for one slot and one node
  at a time, named by `index` and `node_id`.
- Css reference: dropped in `drain_stock()` and also in `consume_stock()`
  when it takes a slot to zero pages and clears the slot.
- Objcg reference: taken in `__refill_obj_stock()`, dropped in
  `drain_obj_stock_slot()`.
- Full stock: `refill_stock()` evicts round robin through `drain_idx`, not at
  random. `__refill_obj_stock()` does the same.
- `refill_stock()`: uncharges directly when `nr_pages` exceeds
  `MEMCG_CHARGE_BATCH` or the trylock fails.
- `!gfpflags_allow_spinning()`: `try_charge_memcg()` charges exactly
  `nr_pages`, so nothing is refilled.
- `drain_all_stock()`: returns without draining when `percpu_charge_mutex` is
  already held.
- `drain_all_stock()`: does not wait for remote work and skips isolated
  remote CPUs, so stocks can be non-empty on return.
- Remote drain: `schedule_drain_work()` uses `queue_work_on()` on `memcg_wq`.
- Work functions: `drain_local_memcg_stock()` and `drain_local_obj_stock()`.
  There is no drain_local_stock() here.
- CPU selection: `is_memcg_drain_needed()` wants a slot with nonzero pages in
  the target subtree. The work then drains every slot of that CPU.
- CPU hotplug: `memcg_hotplug_cpu_dead()` calls `drain_obj_stock()` and
  `drain_stock_fully()` directly. It does not call `drain_all_stock()`.
- `drain_all_stock()`: also called from `mm/memcontrol-v1.c`, for example
  `mem_cgroup_resize_max()`.

**Uncharging a folio**

- Free path: `__folio_put()` and `folios_put_refs()` are in `mm/folio.c`.
- `free_unref_folios()`: does not uncharge a folio without
  `MEMCG_DATA_KMEM`. Its callers call `mem_cgroup_uncharge_folios()` first.
- `uncharge_folio()`: drops an objcg reference with `obj_cgroup_put()` for LRU
  and kmem folios alike. It calls no `css_put()`.
- `uncharge_batch()`: resolves the memcg from `ug->objcg` under RCU, so the
  counters of the memcg the objcg points at then are uncharged.
- Root objcg: `uncharge_folio()` adds no pages to `nr_memory` for an LRU
  folio.
- Deferred split queue: one `list_lru`, `deferred_split_lru` in
  `mm/huge_memory.c`. There is no deferred_split_queue here.
- Sublist choice: `__folio_unqueue_deferred_split()` passes `folio_memcg()` and
  `folio_nid()` to `list_lru_lock_irqsave()`.
- Cleared `memcg_data`: `folio_memcg()` is NULL, so the lock taken is the
  node's root sublist, which may not be the one the folio is on.
- **Unsafe usage**: clearing or replacing `memcg_data` of a large rmappable
  folio of order > 1 that may still be on `deferred_split_lru`.
  - Safe: call `folio_unqueue_deferred_split()` first, with the refcount zero
    and the folio still charged, as `__folio_put()` does;
    `__folio_unqueue_deferred_split()` warns on a nonzero refcount and on an
    uncharged folio.
  - Safe: with the refcount frozen, as `__folio_migrate_mapping()` does before
    `mem_cgroup_migrate()` runs.
- `uncharge_folio()` backstop: the `WARN_ON_ONCE()` unqueue runs before
  `memcg_data` is cleared, and only for non-kmem folios.
- `mem_cgroup_replace_folio()`: force-charges the new folio with
  `page_counter_charge()`. The old folio stays charged until it is freed.
- v1 swap-out: `__memcg1_swapout(folio, ci)` in `mm/memcontrol-v1.c`, called
  from `__remove_mapping()`. It unqueues the folio itself.
- There is no mem_cgroup_swapout(), memcg1_swapout() or
  mem_cgroup_move_account() here.
- `folio_split_memcg_refs()`: only adds objcg references. `memcg_data` is
  copied to the new folios in `mm/huge_memory.c`.
- `split_page_memcg()`: kmem pages only.
- Offline: `memcg_reparent_objcgs()` moves LRU folios to the parent and
  repoints their objcgs, without touching `memcg_data`.

**Swap accounting**

- Memcg charged by `__mem_cgroup_try_charge_swap()`:
  `obj_cgroup_memcg(folio_objcg(folio))`, read under `rcu_read_lock()`, or the
  ancestor that `mem_cgroup_private_id_get_online()` returns for it.
- `mem_cgroup_private_id_get_online(memcg, nr_pages)`: takes all `nr_pages` id
  references at once. It walks to the parent while `id.ref` is zero.
- There is no mem_cgroup_id_get_online(), mem_cgroup_id_get_many(),
  mem_cgroup_id_put_many() or mem_cgroup_from_id() here.
- Put side: `mem_cgroup_private_id_put(memcg, n)`.
- No-slot test: `!folio_test_swapcache(folio)`. It raises `MEMCG_SWAP_FAIL`
  and returns 0.
- Caller: `folio_alloc_swap()` puts the folio in the swap cache first, then
  charges. On failure it calls `swap_cache_del_folio()`.
- Root memcg: the counter is not charged; the references and the record are
  still made.
- Owner record: `ci->memcg_table`, a `struct swap_memcg_table` per cluster,
  defined in `mm/swap_table.h`.
- There is no mm/swap_cgroup.c, swap_cgroup_record() or
  lookup_swap_cgroup_id() here.
- Record accessors: `__swap_cgroup_set()`, `__swap_cgroup_get()`,
  `__swap_cgroup_clear()`.
- Table lifetime: allocated in `swap_cluster_alloc_table()` unless
  `mem_cgroup_disabled()`, freed in `swap_cluster_free_table()`.
- Release: `__swap_cluster_free_entries()` in `mm/swapfile.c`. It clears one
  slot at a time and uncharges each run of equal ids.
- `__mem_cgroup_uncharge_swap(id, nr_pages)`: takes the id as an argument. It
  does not clear the record.
- v1 record: `__memcg1_swapout()` writes it.
- v1 swap-in: `memcg1_swapin()` clears the record and uncharges. There is no
  mem_cgroup_swapin_uncharge_swap() here.

**Swap charge and cgroup id**

- Id kind: the 16-bit private id, `mem_cgroup_private_id()`, from the
  `mem_cgroup_private_ids` xarray.
- Reference source: `mem_cgroup_private_id_get_online()`; record the id of the
  memcg it returns, which may be an ancestor.
- Cluster lock: `__swap_cgroup_set()` and `__swap_cgroup_get()` assert
  `ci->lock`.
- `swap_pte_batch()`: compares PTEs only. It does not look at the owner.
- Swap-in read: `__swap_cache_add_check()`, when given `memcg_id`, returns the
  id and gives `-EBUSY` unless every slot in the range has the same id.
- **Potentially unsafe usage**: storing `mem_cgroup_private_id()` of a memcg
  without holding id references.
  - Unsafe: in `ci->memcg_table`. `__mem_cgroup_uncharge_swap()` puts
    `nr_pages` references on whatever memcg the id resolves to, and an id
    whose `id.ref` reached zero is erased and can be allocated again by
    `mem_cgroup_alloc()`.
  - Safe: in a workingset shadow entry, as `workingset_eviction()` does.
    `workingset_test_recent()` looks the id up under RCU, accepts NULL, and
    puts no id reference.
- **Potentially unsafe usage**: clearing several slots with one
  `__swap_cgroup_clear()` and uncharging the returned id for all of them.
  - Unsafe: when the slots can have different owners. Only the first slot's id
    is returned; the rest are checked by `VM_WARN_ON_ONCE()` alone.
  - Safe: one slot at a time, as `__swap_cluster_free_entries()` does.
  - Safe: `memcg1_swapin()` on a folio from `__swap_cache_alloc()`, where
    `__swap_cache_add_check()` required one id for the whole range.

## Memory cgroup lookup and lifetime

**Looking up a folio's cgroup**

- Two bindings: folio→`struct obj_cgroup` (`folio->memcg_data`) and
  objcg→memcg (`objcg->memcg`); the `folio_memcg()` result stays the folio's
  memcg only while both are stable.
- Folio lock, LRU isolation, exclusive reference: fix only folio→objcg; the
  memcg read through it can still switch to the parent.
- objcg→memcg stable: under `cgroup_mutex` (`offline_css()` asserts it), or
  under the `lru_lock` of the folio's own lruvec as returned by
  `folio_lruvec_lock()`.
- `objcg_lock`: static in `mm/memcontrol.c`, not available to callers; there
  is no deferred split queue lock in this role (`deferred_split_lru` is a
  `struct list_lru`).
- Pointer validity: `rcu_read_lock()` or `cgroup_mutex`;
  `obj_cgroup_memcg()` has a `lockdep_assert_once()` for exactly these, so
  `folio_memcg()` under the folio lock alone trips it.
  `mem_cgroup_swap_full()` holds the folio lock and still takes RCU.
- Page counters only: folio→objcg stability plus RCU is enough, as in
  `uncharge_batch()`.
- kmem folios: accepted by `folio_memcg()`; `folio_objcg()` masks
  `MEMCG_DATA_KMEM` off.
- Slab folios and `MEMCG_DATA_OBJEXTS`: rejected by `VM_BUG_ON_FOLIO()` only,
  so unchecked without `CONFIG_DEBUG_VM`.
- `folio_memcg_check()`: returns NULL when `MEMCG_DATA_OBJEXTS` is set; adds
  no lifetime or binding guarantee and hits the same lockdep assertion.
- `get_mem_cgroup_from_folio()` on `css_tryget()` failure: re-reads
  `folio_memcg()` and retries; no fallback to root.
- `get_mem_cgroup_from_folio()` on an uncharged folio: returns
  `root_mem_cgroup`; it returns NULL when `mem_cgroup_disabled()`.
- `get_mem_cgroup_from_folio()` calls `folio_memcg()`, not
  `folio_memcg_check()`, with no NULL test inside the loop: the folio must be
  non-slab and must stay charged for the duration of the call.

**Locking a folio's lruvec**

- There is no lruvec_memcg_debug() and no unlock_page_lruvec() in this tree.
- `folio_lruvec_lock()`, `folio_lruvec_lock_irq()`,
  `folio_lruvec_lock_irqsave()` in `mm/memcontrol.c`: compare only
  `lruvec_memcg()` with `folio_memcg()`; on mismatch they drop the spinlock,
  keep RCU, and retry.
- `folio_matches_lruvec()`: also compares the pgdat; used by the relock
  helpers and the `VM_WARN_ON_ONCE_FOLIO()` checks in
  `include/linux/mm_inline.h`.
- Recheck relies on an LRU folio holding the objcg of its own node; see
  `charge_memcg()` and `get_migration_objcg()` in `mm/memcontrol.c`, both
  select by `folio_nid()`.
- Precondition: folio→objcg already stable (folio locked, LRU flag clear, or
  refcount frozen); batch callers do `folio_test_clear_lru()` first, hold a
  folio that is not on the LRU, or act on a folio whose refcount reached
  zero.
- Held on return: `lru_lock` and the RCU read lock, also in the
  `!CONFIG_MEMCG` stubs.
- Release: `lruvec_unlock()`, `lruvec_unlock_irq()`,
  `lruvec_unlock_irqrestore()` in `include/linux/memcontrol.h`; each drops
  the spinlock, then RCU.
- `lruvec_lock_irq()` (lock by lruvec, no folio): takes RCU too, so it pairs
  with `lruvec_unlock_irq()`.
- Batch users of the relock helpers are in `mm/folio.c`, `mm/mlock.c` and
  `mm/vmscan.c`; there is no mm/swap.c in this tree.
- Second batching form: `isolate_migratepages_block()` in
  `mm/compaction.c` compares `folio_lruvec()` with the lruvec it holds and
  relocks through `compact_folio_lruvec_lock_irqsave()`, its own copy of the
  retry loop.
- **Unsafe usage**: taking `lru_lock` on a `folio_lruvec()` result with no
  recheck after the lock is held.
  - Unsafe: also with the folio locked or isolated; `objcg->memcg` can move
    to the parent between lookup and lock, and the lock taken is then the
    dying child's.
  - Safe: `folio_lruvec_lock_irq()` and its variants, as
    `folio_isolate_lru()` does.
  - Safe: a folio compared with a lruvec already locked, by
    `folio_matches_lruvec()` as `folio_lruvec_relock_irq()` does, or by
    `folio_lruvec()` as `isolate_migratepages_block()` does;
    `__memcg_reparent_objcgs()` runs only with both `lru_lock`s held, so a
    match cannot change.

**Offlining a memory cgroup**

- Objcgs are per memcg per node: `objcg`, `orig_objcg` and `objcg_list` are
  fields of `struct mem_cgroup_per_node`; `struct mem_cgroup` has none.
- `memcg_reparent_objcgs()`: handles one node at a time and drops the locks
  it took between nodes.
- Per node, in one lock section: LRU lists and `lru_zone_size` first, then
  `__memcg_reparent_objcgs()` repoints that node's active and inherited
  objcgs and splices them onto the parent's node list.
- Locks, same with and without MGLRU: `reparent_locks()` takes `objcg_lock`
  with irqs off, child `lru_lock`, then parent `lru_lock`; `cgroup_mutex` is
  held by the caller (`offline_css()` asserts it).
- MGLRU is chosen at run time by `lru_gen_enabled()`.
- MGLRU sequence: `max_lru_gen_memcg()` on the parent before the locks,
  `recheck_lru_gen_max_memcg()` under them; on failure unlock,
  `cond_resched()`, retry; then `lru_gen_reparent_memcg()` in `mm/vmscan.c`
  splices each child list onto the parent list of the same generation index.
- Classic LRU: `lru_reparent_memcg()` in `mm/folio.c`; for
  `LRU_UNEVICTABLE` only the size is moved, no list is spliced.
- `percpu_ref_kill()` on the node's objcg: after the locks are dropped;
  `orig_objcg` keeps a reference until `__mem_cgroup_free()`.
- `reparent_state_local()`: runs after the node loop, does nothing on the
  default hierarchy or without `CONFIG_MEMCG_V1`.
- There is no reparent_deferred_split_queue(); `deferred_split_lru` in
  `mm/huge_memory.c` is a `struct list_lru`, reparented by
  `memcg_reparent_list_lrus()` from `memcg_offline_kmem()` before
  `memcg_reparent_objcgs()` runs.
- `folio_memcg()` mid-move, LRU folio: parent for folios on nodes already
  processed, child for folios on nodes not yet reached.

**Identifiers and references**

| Identifier | Read / lookup | After removal |
|---|---|---|
| private ID, `memcg->id.id`, 1 to `MEM_CGROUP_ID_MAX` | `mem_cgroup_private_id()` / `mem_cgroup_from_private_id()` | valid until `id.ref` reaches 0, then erased and reusable |
| cgroup ID, u64 | `mem_cgroup_id()` / `mem_cgroup_get_from_id()` | lookup fails once the kernfs node is not active or `cgroup_tryget()` fails |
| css ID, `memcg->css.id` | `css_from_id()` | lookup returns NULL from `css_release_work_fn()`; number freed in `css_free_rwork_fn()` |
| `memcg->kmemcg_id` | list_lru xarray index | copy of the private ID; -1 for root or when `mem_cgroup_kmem_disabled()` |

- `mem_cgroup_id()`: returns `cgroup_id()`, not the short ID.
- There is no mem_cgroup_idr, mem_cgroup_from_id() or
  mem_cgroup_id_get_many() here; the store is the xarray
  `mem_cgroup_private_ids` in `mm/memcontrol.c`.
- Private ID publication: reserved in `mem_cgroup_alloc()`, stored only at
  the end of `mem_cgroup_css_online()`; lookup returns NULL before that and
  for ID 0.
- Private ID base reference: dropped as the last step of
  `mem_cgroup_css_offline()`.
- At `id.ref` zero: `mem_cgroup_private_id_put()` erases the entry, sets
  `id.id` to 0 and drops the css reference the ID held.
- `mem_cgroup_private_id_get_online()`: takes the references on the memcg or
  on the nearest ancestor whose `id.ref` is not zero, and returns that one;
  its callers are `__mem_cgroup_try_charge_swap()` and `__memcg1_swapout()`.
- `mem_cgroup_get_from_id()`: searches the default hierarchy only, within the
  caller's cgroup namespace, and returns the memcg of the effective css,
  which can be an ancestor; `run_cmd()` in `mm/vmscan.c` compares
  `mem_cgroup_id()` afterwards.
- `mem_cgroup_from_private_id()` result may be NULL; `mem_cgroup_tryget()`
  returns true for NULL, so a NULL test is still needed before the result is
  dereferenced.
- `css_tryget(&memcg->css)`: needs the NULL test before it.
- **Unsafe usage**: dereferencing the `mem_cgroup_from_private_id()` result
  after `rcu_read_unlock()` with no css reference.
  - Safe: `mem_cgroup_tryget()` inside RCU plus a NULL test,
    `mem_cgroup_put()` later, as `workingset_test_recent()` does.
  - Safe: NULL test then `css_tryget_online()`, falling back to
    `get_mem_cgroup_from_mm()`, as `mem_cgroup_swapin_charge_folio()` does.
  - Safe: all use inside the RCU section with no tryget, as
    `__mem_cgroup_uncharge_swap()` does; the swap record's ID reference pins
    the css until `mem_cgroup_private_id_put()`.

## Migration

**Migration API**

- Negative return: only `-ENOMEM`, when `get_new_folio()` returns NULL.
  `-EAGAIN`, `-EBUSY` and other per-folio errors are never returned; they are
  counted.
- `-ENOMEM` on a large folio: `migrate_pages_batch()` first tries
  `try_split_folio()`; if the split works the folio counts as one failure
  and migration continues with no error. With `MR_NUMA_MISPLACED` this split
  is not tried.
- `-ENOMEM` return: folios already unmapped in the batch are still moved
  first. `from` then holds every folio that was not migrated: the failed
  ones, every untried folio and any split pieces.
- Return 0: forced whenever `from` is empty at the end. A large folio that
  was split and whose pieces all migrated then does not count as a failure.
- Positive return: counts folios, not list entries; a split large folio
  whose pieces fail to migrate leaves several pieces on `from` for one
  counted failure.
- `*ret_succeeded`: base pages, not folios, despite the kerneldoc.
- Folios left on `from`: the caller owns them and must consume the list.
  `putback_movable_pages()` is the usual way, not the only one.
  - `demote_folio_list()` in `mm/vmscan.c` leaves them on the list;
    `shrink_folio_list()` splices them back onto `folio_list`.
  - `damon_migrate_folio_list()` in `mm/damon/ops-common.c` drops
    `NR_ISOLATED_ANON` or `NR_ISOLATED_FILE` and calls `folio_putback_lru()`
    itself.

**Blocking by mode**

- `enum migrate_mode`: three values. There is no MIGRATE_SYNC_NO_COPY.

| Blocking point | `MIGRATE_ASYNC` | `MIGRATE_SYNC_LIGHT` | `MIGRATE_SYNC` |
|---|---|---|---|
| source folio lock | trylock | sleeps only if folio is uptodate | sleeps |
| folio under writeback | `-EBUSY` | `-EBUSY` | waits |
| buffer lock | trylock | sleeps only if buffer is uptodate | sleeps |
| hugetlb source lock | trylock | trylock | sleeps from the fourth pass |
| lock for `try_split_folio()` | trylock | sleeps | sleeps |

- `PF_MEMALLOC` task: `migrate_folio_unmap()` never sleeps on the source
  folio lock, in any mode.
- `MIGRATE_ASYNC` still sleeps on the rmap rwsem: `try_to_migrate()` does not
  set `try_lock` in its `struct rmap_walk_control`.
- Sync modes, non-hugetlb folios: `migrate_pages_sync()` runs the batch as
  `MIGRATE_ASYNC` first (`NR_MAX_MIGRATE_ASYNC_RETRY` passes), then retries
  failures one folio at a time in the caller's mode. A callback sees
  `MIGRATE_ASYNC` first.
- Pieces of a split large folio: migrated with `MIGRATE_ASYNC`, one pass,
  whatever mode the caller passed.
- `get_new_folio()`: not given the mode. Whether allocation blocks is decided
  by the caller's callback, not by the mode.
- Callbacks add their own mode tests; for example `nfs_migrate_folio()` in
  `fs/nfs/write.c` waits only outside `MIGRATE_ASYNC`.

**Phases of one migration**

- State between phases: stored in `dst->migrate_info` by
  `__migrate_folio_record()`. It shares a union with `private` and `swap`
  in `struct folio`; `dst->mapping` is not used.
- Flag names: `FOLIO_WAS_MAPPED` and `FOLIO_WAS_MLOCKED` in `mm/migrate.c`.
  There is no PAGE_WAS_MAPPED or PAGE_WAS_MLOCKED.
- Return values: both phases return 0 or a negative errno. MIGRATEPAGE_UNMAP
  and MIGRATEPAGE_SUCCESS are not defined.
- `migrate_folio_unmap()`: calls `get_new_folio()` before it touches `src`,
  so `-ENOMEM` needs no undo.
- movable_ops pages: the unmap phase locks both folios and records state
  without calling `try_to_migrate()`. The move phase calls
  `migrate_movable_ops_page()`, not `move_to_new_folio()`.
- Pairs still at `-EAGAIN` when the move passes run out:
  `migrate_folios_undo()` extracts the state and runs both undo helpers.

**Expected references**

- Expected count: `folio_expected_ref_count()` in `include/linux/mm.h`.
  There is no folio_expected_refs().
- `folio_expected_ref_count()`: swap cache references count for any folio;
  `mapping` and `PG_private` count only for non-anon folios.
- `folio_migrate_mapping()`: adds `extra_count + 1`, compares with
  `folio_ref_count()` for every folio, and returns `-EAGAIN` on mismatch
  before taking any lock.
- `__folio_migrate_mapping()` with no mapping: a large rmappable folio is
  still frozen with `folio_ref_freeze()`, to leave the deferred split
  queue; failure returns `-EAGAIN`. Other folios are not frozen.
- `__folio_migrate_mapping()` with a mapping: swap cache folios are frozen
  under `swap_cluster_get_and_lock_irq()`, not the xarray lock, and replaced
  with `__swap_cache_replace_folio()`.
- Xarray slot: not checked. The frozen count is the only test.
- `__folio_migrate_mapping()` makes no unlocked compare of its own.
  `__migrate_folio()` compares before `folio_mc_copy()` and passes the count
  down.
- Success: returns 0. MIGRATEPAGE_SUCCESS is not defined.

**Migration entries**

- Names in this tree: `softleaf_is_migration()`,
  `softleaf_entry_wait_on_locked()` in `mm/filemap.c`, `pte_swp_uffd()`,
  `pte_mkuffd()`. There is no is_migration_entry(),
  migration_entry_wait_on_locked() or pte_swp_uffd_wp().
- `remove_migration_ptes()` takes `enum ttu_flags`: `TTU_RMAP_LOCKED` and
  `TTU_USE_SHARED_ZEROPAGE`. There is no RMP_LOCKED or
  RMP_USE_SHARED_ZEROPAGE.
- PTEs that get no migration entry in `try_to_migrate_one()`:
  - a hwpoisoned subpage gets `make_hwpoison_entry()`;
  - a `pte_unused()` PTE in a VMA without userfaultfd is left cleared.
- `remove_migration_ptes()` restores neither of those two.
- uffd bit in `remove_migration_pte()`: `pte_mkuffd()` only when the entry is
  not writable.
- `userfaultfd_rwp()` VMA with the uffd bit: the new PTE is changed to
  `PAGE_NONE`.
- Dirty: restored only if the entry is dirty and `folio_test_dirty()` is
  still true.
- Soft-dirty: set from the entry, otherwise cleared on the new PTE.
- mlock: rebuilt by `mlock_vma_folio()` in the rmap add helpers, only when
  the call maps the whole folio. A PTE-mapped large folio does not get it.
- Device-private destination: `remove_migration_pte()` installs a
  device-private entry, not a present PTE.
- `TTU_USE_SHARED_ZEROPAGE`: allowed only when `src == dst`.

**The migrate callback**

- Return value: 0 on success. MIGRATEPAGE_SUCCESS is not defined.
- File-backed hugetlb folio that was mapped: the callback runs with
  `i_mmap_rwsem` held for write by `unmap_and_move_hugetlb_folio()`.
- Hugetlb path: does not test or wait for writeback before the callback.
- `dst->migrate_info`: zero at the call from `migrate_folio_move()`. It
  overlays `dst->private`.
- `dst` references: after success `migrate_folio_move()` calls
  `folio_put(dst)`. The callback must have given `dst` the references its
  new owner holds, as `__folio_migrate_mapping()` does with
  `folio_ref_add()`.
- `dst` and the LRU: `migrate_folio_move()` calls `folio_add_lru(dst)` after
  success; the callback does not.
- `-EAGAIN`, outside hugetlb: the callback is called again on the next pass
  with both folios still locked and `src` still unmapped.

**Ready-made migrate callbacks**

- `fallback_migrate_folio()`: a dirty folio returns `-EBUSY`. Nothing is
  written out; there is no writeout() here.
- `fallback_migrate_folio()` when `filemap_release_folio()` fails: `-EAGAIN`
  in `MIGRATE_SYNC`, `-EBUSY` in the other modes.
- `filemap_migrate_folio()`: `__migrate_folio()` plus moving the private
  pointer. It is not the fallback.
- `mapping_inaccessible()`: checked in `move_to_new_folio()` before the
  callback and before the fallback; returns `-EOPNOTSUPP`.
- Opting out: providing no callback does not stop migration, since the
  fallback migrates clean folios. A callback that always fails does; for
  example `secretmem_migrate_folio()` in `mm/secretmem.c`.
- Without `CONFIG_MIGRATION`: `filemap_migrate_folio`,
  `buffer_migrate_folio` and `buffer_migrate_folio_norefs` are defined as
  NULL. `migrate_folio()` has no such stub; `shmem_aops` and `swap_aops`
  wrap it in `#ifdef CONFIG_MIGRATION`.

**Sleeping in migrate callbacks**

- `folio_copy()` in `mm/util.c`: called directly. There is no
  folio_migrate_copy().
- `migrate_huge_page_move_mapping()`: calls `folio_mc_copy()`, so the
  hugetlb callback can sleep.
- `__buffer_migrate_folio()`: takes `mapping->i_private_lock` only with
  `check_refs`, and only around the `b_count` scan.
- **Potentially unsafe usage**: calling `folio_copy()`, `folio_mc_copy()`,
  `migrate_folio()` or `filemap_migrate_folio()` under a spinlock.
  - Unsafe: when the folio can be large; the copy calls `cond_resched()`
    between pages.
  - Safe: order-0 folios only, as `aio_migrate_folio()` does with
    `folio_copy()`; `aio_setup_ring()` allocates the ring folios with no
    order. The copy loop in `folio_copy()` defines it: no `cond_resched()`
    for one page.
  - Safe: scan under the lock, drop it, then call the helper, as
    `__buffer_migrate_folio()` does; `BH_Migrate` keeps atomic lookups out.
- **Unsafe usage**: calling `folio_migrate_mapping()` with interrupts
  disabled, for a folio that has a mapping.
  `__folio_migrate_mapping()` ends with `local_irq_enable()`.
  - Safe: call it with interrupts enabled and take the irq-disabling lock
    afterwards, as `aio_migrate_folio()` does.

**Reverse-map lock across migration**

- In-tree callers that pass `TTU_RMAP_LOCKED` to `try_to_migrate()`:
  `unmap_and_move_hugetlb_folio()` in `mm/migrate.c` and
  `unmap_folio()` in `mm/huge_memory.c`. There is no
  unmap_and_move_huge_page().
- `unmap_folio()`: passes `TTU_RMAP_LOCKED` to `try_to_migrate()` for anon
  folios only. `__folio_split()` holds `anon_vma_lock_write()` and a reference
  from `folio_get_anon_vma()`.
- `unmap_and_move_hugetlb_folio()`: holds `i_mmap_rwsem` for write across
  `try_to_migrate()`, `move_to_new_folio()` and `remove_migration_ptes()`.
  It unlocks only after the remap.
- Anon folio: `folio_anon_vma()` must be non-NULL; `rmap_walk_anon()` does
  `VM_BUG_ON_FOLIO()` otherwise. `__folio_split()` returns `-EBUSY` first.
- Folio lock: required; `rmap_walk_file()` and `rmap_walk_anon()` assert it.
- **Unsafe usage**: `try_to_migrate()` on a file-backed hugetlb folio without
  `TTU_RMAP_LOCKED`. `try_to_migrate_one()` does `VM_BUG_ON()` on it.
  - Safe: take `hugetlb_folio_mapping_lock_write()` and pass the flag, as
    `unmap_and_move_hugetlb_folio()` does.
- **Unsafe usage**: calling `remove_migration_ptes()` without
  `TTU_RMAP_LOCKED` while the rmap lock is still held. `rmap_walk()` takes
  the same rwsem again.
  - Safe: pass the flag, as `remap_page()` and
    `unmap_and_move_hugetlb_folio()` do; `rmap_walk_locked()` skips the
    lock.

**Charge transfer in migration**

- `mem_cgroup_migrate()`: gets a new objcg reference for `new` from
  `get_migration_objcg()`, then drops `old`'s with `obj_cgroup_put()`. No
  css reference is moved.
- `get_migration_objcg()`: re-derives the objcg for the node of `new` when
  the nodes differ.
- Page counters: changed in one case. If the new objcg is root and the old
  one was not, `memcg_uncharge()` settles the charge.
- Caller: only `folio_migrate_flags()`. `__folio_migrate_mapping()` does not
  call it.
- `old` must be off the LRU: `VM_BUG_ON_FOLIO(folio_test_lru(old))`.
- `old` with no objcg: early return; warns unless `old` is hugetlb.
- `migrate_folio_done()`: uses `mod_node_page_state()` on `folio_pgdat()`.
  It skips the `NR_ISOLATED_ANON` or `NR_ISOLATED_FILE` decrement for
  movable_ops pages and for `MR_DEMOTION`.
- **Unsafe usage**: calling `folio_migrate_flags()` before
  `folio_migrate_mapping()`. `mem_cgroup_migrate()` warns if `old` is still
  on the deferred split queue, and `__folio_migrate_mapping()` reads
  `folio_memcg()` of `old` for its zone statistics.
  - Safe: mapping first, then flags, as `__migrate_folio()` does.
- **Unsafe usage**: returning an error from a `migrate_folio` callback after
  `folio_migrate_flags()` ran. `old` is handed back with `memcg_data` 0; on
  LRU putback `folio_lruvec()` warns and uses the root memcg.
  - Safe: make `folio_migrate_flags()` the last step that can precede a
    return of 0, as `__migrate_folio()` does.

**Collecting folios for migration**

- Return type of `collect_longterm_unpinnable_folios()` in `mm/gup.c`:
  `unsigned long`, not void.
- Return value: the number of folios for which `folio_is_longterm_pinnable()`
  was false. It is counted before any isolation is tried.
- The count includes folios that are never listed: device-coherent folios,
  and folios for which `folio_isolate_hugetlb()` or `folio_isolate_lru()`
  failed.
- `check_and_migrate_movable_pages_or_folios()`: tests the count, not
  `list_empty()`. Only a zero count returns 0 and keeps the pins.
- Empty list: guarantees only that nothing was isolated. It says nothing
  about whether the folios are pinnable.
- Zero return: every folio examined passed `folio_is_longterm_pinnable()` at
  that moment, and the list is empty.
- Non-zero count with an empty list: `migrate_longterm_unpinnable_folios()`
  unpins everything, skips `migrate_pages()` and returns `-EAGAIN`, or
  `-EBUSY` if `migrate_device_coherent_folio()` failed.
- Retry loop: `__gup_longterm_locked()` repeats while the result is
  `-EAGAIN`. There is no __get_longterm_locked().
- Device-coherent folios: migrated in `migrate_longterm_unpinnable_folios()`
  with `migrate_device_coherent_folio()`, not during collection.
- LRU drain: `lru_cache_drain_for_folio()` in `mm/folio.c`. It drains when
  the refcount differs from `folio_expected_ref_count()` plus the pin
  references: 1 with `folio_has_pincount()`, else `GUP_PIN_COUNTING_BIAS`.

## Writeback tags, flags and throttling

**Tag lifecycle**

- `PAGECACHE_TAG_DIRTY`: within `mm/`, cleared only by
  `__folio_start_writeback()`, and only when `folio_test_dirty()` is false at
  that moment; otherwise it goes when the entry leaves the cache (for
  example `xas_init_marks()` in `page_cache_delete()`).
- `folio_clear_dirty_for_io()`, `__folio_cancel_dirty()` and
  `__folio_end_writeback()`: none clears `PAGECACHE_TAG_DIRTY`.
- After `folio_clear_dirty_for_io()`: flag clear, tag still set, until
  writeback is started or `__folio_mark_dirty()` runs again.
- Dropping a stale tag on a clean folio: done by cycling
  `__folio_start_writeback(folio, false)` then `folio_end_writeback()` with
  no I/O, for example `mpage_prepare_extent_to_map()` in `fs/ext4/inode.c`
  and `netfs_kill_dirty_pages()`.
- `tag_pages_for_writeback()`: run by the first `writeback_iter()` call when
  `wbc->sync_mode == WB_SYNC_ALL` or `wbc->tagged_writepages`, so also for
  `WB_SYNC_NONE` with `tagged_writepages`.
- Mapping with `AS_NO_WRITEBACK_TAGS`: `__folio_start_writeback()` and
  `__folio_end_writeback()` set and clear the writeback flag but no tag, and
  `keep_write` is ignored. Only `swap_space` in `mm/swap_state.c` sets it.

**Keeping the to-write tag**

- There is no folio_start_writeback_keepwrite here; callers pass `true` to
  `__folio_start_writeback()` directly. `folio_start_writeback()` is a macro
  in `include/linux/page-flags.h` that passes `false`.
- `__folio_start_writeback()`: asserts that the folio is locked and not
  under writeback (`VM_BUG_ON_FOLIO()`), not that it is clean; when the
  dirty flag is set, `PAGECACHE_TAG_DIRTY` is kept too.
- `keep_write` true is not tied to the dirty flag: on a clean folio the DIRTY
  tag is cleared and `PAGECACHE_TAG_TOWRITE` stays, stale, until a later
  start with `false`, removal from the cache, or a clear by hand.
- A `writeback_iter()` walk that finds a clean folio by a stale TOWRITE
  skips it: see the `folio_test_dirty()` test in
  `folio_prepare_writeback()`.
- **Unsafe usage**: starting writeback with `keep_write` false (which
  `folio_start_writeback()` always does) on a folio that keeps data
  unwritten that was dirty when the writer took it; a `WB_SYNC_ALL` walk
  that tagged the folio earlier follows TOWRITE only and never visits it.
  - Safe: redirty, then pass `true` only when something stays dirty, as
    `ext4_bio_write_folio()` does with its `keep_towrite`; the requirement
    comes from `wbc_to_tag()`.
  - Safe: always pass `true` and clear DIRTY and TOWRITE by hand once the
    folio is no longer dirty, as `btrfs_subpage_set_writeback()` does with
    `folio_clear_tags()`.

**Writeback iteration**

- `wbc_to_tag()`: static inline in `include/linux/writeback.h`.
- Folio handed out: dirty flag already cleared by `folio_clear_dirty_for_io()`
  in `folio_prepare_writeback()`; `PAGECACHE_TAG_DIRTY` is still set.
- Lock on the handed-out folio: owned by the caller; `writeback_iter()` never
  unlocks a folio it returned, on any path.
- First call: zeroes both `*error` and `wbc->saved_err`, so a value the
  caller put in `*error` beforehand is lost.
- `*error` passed back in: must be 0 or negative; a positive value hits
  `WARN_ON_ONCE()`.
- There is no err field in `struct writeback_control`; the first error goes
  in `wbc->saved_err`, and only under `WB_SYNC_ALL`.
- `WB_SYNC_ALL`: never stops early, neither on error nor on
  `wbc->nr_to_write`; at the end `*error` is overwritten with
  `wbc->saved_err`.
- Any other `sync_mode`, `tagged_writepages` included: stops on the first
  non-zero `*error` or `wbc->nr_to_write <= 0`; `*error` is left as the
  caller set it and `saved_err` stays 0.
- Breaking out of the loop: skips `folio_batch_release()` on `wbc->fbatch`
  (folio references leak), the `mapping->writeback_index` update, and the
  copy of `saved_err` into `*error`.

**Dirty and writeback flags**

- `folio_clear_dirty_for_io()` accounting: on a successful test-and-clear it
  decrements `NR_FILE_DIRTY`, `NR_ZONE_WRITE_PENDING`, `WB_RECLAIMABLE`, and
  `WB_DONTCACHE_DIRTY` if `folio_test_dropbehind()`.
- `folio_clear_dirty_for_io()`: does not decrement `NR_DIRTIED` and does not
  call `folio_account_cleaned()`; that helper is for cleaning without
  writeback, for example `__folio_cancel_dirty()`.
- Mapping NULL or `mapping_can_writeback()` false:
  `folio_clear_dirty_for_io()` only test-and-clears the flag; no
  `folio_mkclean()`, no accounting.
- There is no folio_account_redirty() here; `folio_redirty_for_writepage()`
  does the accounting itself.
- `folio_redirty_for_writepage()`: adds the folio's pages to
  `wbc->pages_skipped`; it does not change `wbc->nr_to_write`.
- `folio_redirty_for_writepage()`: subtracts from `current->nr_dirtied`,
  `NR_DIRTIED` and `WB_DIRTIED` even when `filemap_dirty_folio()` returns
  false because the folio was already dirty; `ext4_bio_write_folio()` tests
  `folio_test_dirty()` first.
- `wbc->pages_skipped`: read by `requeue_inode()` and `writeback_sb_inodes()`
  in `fs/fs-writeback.c`; needed because `writeback_iter()` charges
  `nr_to_write` for redirtied folios too.
- `folio_mark_dirty()` on a skipped folio: also restores the flag and the
  tag; it does not add to `pages_skipped` and it counts the folio as newly
  dirtied.
- Redirty and writeback: `folio_redirty_for_writepage()` makes no test of the
  writeback flag; `ext4_bio_write_folio()` redirties and then starts
  writeback. Writeback that was started must still be ended.
- `folio_end_writeback()`: asserts that the writeback flag is set, not that
  the folio is unlocked; the folio may still be locked, as in the
  nothing-to-submit path of `ext4_bio_write_folio()`.

**Dirty throttle domains**

- `dom` and `gdtc` in `struct dirty_throttle_control`
  (`include/linux/writeback.h`): exist only under `CONFIG_CGROUP_WRITEBACK`,
  so code outside that `#ifdef` must use `dtc_dom()` and `mdtc_gdtc()`, not
  the fields.
- **Potentially unsafe usage**: handing a dtc built with `MDTC_INIT()` to
  code that calls `dtc_dom()`.
  - Unsafe: when nothing tested the domain first and the wb belongs to a
    memcg without parent; `mem_cgroup_wb_domain()` returns NULL and
    `__wb_calc_thresh()` and `hard_dirty_limit()` dereference it.
  - Safe: after `mdtc_valid()`, as in `balance_dirty_pages()` and
    `wb_over_bg_thresh()`.
  - Safe: `cgwb_calc_thresh()`, because its caller `cgwb_debug_stats_show()`
    tests `mem_cgroup_wb_domain()` first.
- `domain_dirty_limits()` on a memcg dtc: reads only `gdtc->avail` from the
  global dtc; the ratios come from the sysctls.
- Needed first: `domain_dirty_avail()` on the gdtc, then on the mdtc
  (`mdtc_calc_avail()` reads `gdtc->avail` and `gdtc->dirty`);
  `domain_dirty_limits()` on the gdtc is not needed, see
  `cgwb_calc_thresh()`.
- `gdtc->avail` left at 0 with `vm_dirty_bytes` or `dirty_background_bytes`
  set: `domain_dirty_limits()` divides by it.
- `domain_dirty_limits()`: does not call `dtc_dom()`; its one domain read is
  `global_wb_domain.dirty_limit` in the `rt_or_dl_task()` boost, applied to
  memcg dtcs too.
- `dom->dirty_limit` readers other than `update_dirty_limit()`: plain reads
  without `dom->lock` and without `READ_ONCE()`, for example
  `hard_dirty_limit()`.
- Direct users of `global_wb_domain`: search for the name;
  `node_dirty_limit()` and the sysctl handlers are not among them, and
  `global_dirty_limits()` goes through a dtc built with `GDTC_INIT_NO_WB`.
- Tracepoints cannot call `dtc_dom()`: it is static in `mm/page-writeback.c`
  and the bodies in `include/trace/events/writeback.h` are built in
  `fs/fs-writeback.c`.
- `balance_dirty_pages` tracepoint: takes the chosen dtc and reports
  `dtc->limit`, which already holds that dtc's own hard limit.
- `dtc->limit`: written only by `wb_position_ratio()`, which
  `balance_wb_limits()` skips in freerun; a tracepoint that reads it must
  fire only after `wb_position_ratio()` ran on that dtc.
- `global_dirty_state` tracepoint: reads `global_wb_domain.dirty_limit`; it
  takes no dtc and `domain_dirty_limits()` emits it only when `mdtc_gdtc()`
  is NULL.

## Model gaps

### Other mistakes models make

- Models take `reset_batch_size()` to run under the caller's lru lock. Here it
  is called with no lruvec lock held, from `walk_mm()` and from
  `evict_folios()` after `move_folios_to_lru()`.
- Models pass a swap entry to `__mem_cgroup_try_charge_swap()`. Here it takes
  only the folio.
- Models restore userfaultfd write-protect with pte_swp_uffd_wp() and know no
  other uffd PTE state. Here the setter on a swap PTE is `pte_swp_mkuffd()`,
  and for a `userfaultfd_rwp()` VMA `do_swap_page()` re-applies `PAGE_NONE`
  when the swap PTE has the uffd bit.
- Models know one retry in `do_try_to_free_pages()`, for skipped low
  protection. Here the `sc->memcg_full_walk` retry exists because reclaimers
  other than kswapd may walk only part of the memcg tree in
  `shrink_node_memcgs()`, and the `sc->force_deactivate` retry runs only if
  `sc->skipped_deactivate`.
- Models take demotion to depend on the node only. Here `can_demote()` and
  `demote_folio_list()` take the memcg and drop target nodes with
  `mem_cgroup_node_filter_allowed()`.
- Models take `mem_cgroup_migrate()` to hand the same pointer to the new
  folio. Here, when the nodes differ, the objcg that `get_migration_objcg()`
  returns can belong to an ancestor memcg; see
  `__get_obj_cgroup_from_memcg()`.
- Models take every folio in an LRU-add batch to reach the LRU. Here
  `folio_batch_move_lru()` frees a folio whose only reference is the batch's.
- Models take `folio_mark_accessed()` to act on every folio. Here it returns
  at once when `folio_test_dropbehind()`.
- Models call isolate_hugetlb(). It is not in this tree;
  `folio_isolate_hugetlb()` in `mm/hugetlb.c` does the job.
