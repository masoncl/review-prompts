# What the mm-reclaim measurement found

Three models were asked the 88 questions in `mm-reclaim-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). This is why the build set in
`../mm-reclaim.md` holds the questions it does. The readers are labelled A, B
and C; which models they were does not matter here. Reader C was the most
current (it assumed 6.14 to 7.0), reader A a little behind it (6.12 to 6.19)
and reader B several releases older (6.8 to 6.16). The hand-written guide is
one of the six that were checked against current sources, so it was used as a
reference and not only as a list of topics.

## How it differs from the other guides

The subject is four subsystems that meet in `shrink_folio_list()`: reclaim,
swap, migration and the memory cgroup charge, with the writeback tags on the
side. Two of them have been rebuilt since any reader last saw them. The swap
core keeps all per-slot state in one table per cluster, and folios are charged
through an object that is handed to the parent when a cgroup goes offline. No
question of the 88 was answered without a correction by all three readers, and
only the entry points came through with every reader nearly right. So very
little could be dropped as already known, and the build set was chosen by
importance within the size of the hand-written guide.

## What all three readers got wrong

- **Per-slot swap state.** All three placed the swap count in a `swap_map`
  byte array, the cached bit in SWAP_HAS_CACHE, the zero-filled bit in a
  per-device zeromap and the owning cgroup in `mm/swap_cgroup.c`. None of these
  exists. A slot is one word of the cluster's swap table (`mm/swap_table.h`):
  free, shadow, PFN or bad, with the count and the zero flag in its top bits,
  overflow in `ci->extend_table` and the cgroup id in `ci->memcg_table`.
- **Swap function names.** Gone: add_to_swap(), add_to_swap_cache() (readers A
  and C guessed swap_cache_add_folio()), delete_from_swap_cache(),
  swapcache_prepare(), swap_duplicate(), swap_free() and swap_free_nr(),
  put_swap_folio(), folio_swapped(), alloc_swap_folio(), swapin_folio(),
  free_swap_and_cache(). In their place: `folio_alloc_swap()` adds the folio to
  the swap cache itself, `folio_dup_swap()` and `folio_put_swap()` move the
  count for a locked swap-cache folio, `swap_dup_entry_direct()` and
  `swap_put_entries_direct()` do it for a bare entry, `swapin_sync()` and
  `swap_cache_alloc_folio()` take a mask of orders.
- **Large folio swap-in errors.** Nobody knew that `swap_cache_alloc_folio()`
  returns -EEXIST for the caller to look the folio up again, returns -ENOENT to
  abort, and handles -EBUSY and -ENOMEM itself by stepping down the orders.
  Readers described retry loops in `do_swap_page()` that are not there:
  it passes order 0 in its mask and cannot see -EBUSY.
- **Swap I/O.** SWP_FS_OPS and `->swap_rw` are gone. A device has a
  `struct swap_ops`; NFS and SMB install one with `SWAP_OPS_F_REQUIRE_NOFS`,
  which is what `may_enter_fs()` tests. Reads and writes are queued in a
  `struct swap_io_ctx` and sent by `swap_write_submit()` and
  `swap_read_submit()`. Reader C said it did not recognise either structure.
- **Swap accounting.** mem_cgroup_id_get_online(), mem_cgroup_from_id(),
  mem_cgroup_swapout() and mem_cgroup_swapin_uncharge_swap() are
  `mem_cgroup_private_id_get_online()`, `mem_cgroup_from_private_id()`,
  `__memcg1_swapout()` and `memcg1_swapin()`. The charge starts from
  `folio_objcg()`, not `folio_memcg()`, and `mem_cgroup_id()` is now the wide
  cgroup id, not the swap record.
- **Swap-in order.** `do_swap_page()` calls `folio_put_swap()` before
  `set_ptes()` and `folio_free_swap()` after it. Every reader had the put
  after, or named swap_free().
- **The runtime switch.** No reader knew `lru_gen_switching()`: while the
  lists are being converted both implementations run, and the paths that are
  only valid for one test `lru_gen_enabled() && !lru_gen_switching()`.
- **Migration bookkeeping.** The unmap state is `FOLIO_WAS_MAPPED` and
  `FOLIO_WAS_MLOCKED` in `dst->migrate_info`, not PAGE_WAS_MAPPED in
  `dst->private`. There is no RMP_LOCKED: `remove_migration_ptes()` takes
  `enum ttu_flags`. The hugetlb caller is `unmap_and_move_hugetlb_folio()`,
  which every reader called unmap_and_move_huge_page().
- **Writeback helpers.** folio_start_writeback_keepwrite() does not exist; the
  call is `__folio_start_writeback(folio, true)`. write_cache_pages() is gone
  (readers A and B still offered it) and `writeback_iter()` is the only
  iterator.
- **The dirty throttling domain.** All three missed that
  `domain_dirty_limits()` reads `global_wb_domain.dirty_limit` for the rt/dl
  boost on memcg domains too, which is the intended exception to the rule.
- **Smaller ones.** FOLIOREF_RECLAIM_CLEAN is gone. `can_demote()` tests
  `node_get_allowed_targets()` filtered by `mem_cgroup_node_filter_allowed()`.
  The deferred split queue is a `list_lru`. `mm/swap.c` is `mm/folio.c`. A
  shrinker's `sc->nid` is always the real node; `SHRINKER_NUMA_AWARE` only
  decides how the deferred count is indexed. `lru_gen_set_refs()` counts repeat
  page-table accesses in `LRU_REFS_MASK` through `folio_mark_accessed()`, which
  the comment in `mmzone.h` denies.

## What readers A and B got wrong as well

- **What a charged folio points at.** `memcg_data` holds a
  `struct obj_cgroup`, chosen per node, for every folio, and the folio holds an
  objcg reference, not a css reference. Both said a `struct mem_cgroup`.
- **Offlining.** Both said LRU folios stay charged to the dead cgroup and pin
  it. `memcg_reparent_objcgs()` splices the LRU lists into the parent's, node by
  node, under `objcg_lock` and both lruvec locks, and redirects the objcg in the
  same section, so `folio_memcg()` returns the parent afterwards.
- **Binding stability.** The folio lock, isolation or an exclusive reference
  keep only the folio-to-objcg binding; the memcg behind it also needs the
  lruvec lock or `cgroup_mutex`. `folio_lruvec_lock()` rechecks and retries
  and returns inside an RCU section that `lruvec_unlock()` ends; reader A said
  there was no retry.
- **Reclaim counters.** `PGSCAN_*`, `PGSTEAL_*`, `PGREFILL`, `PGDEMOTE_*` and
  `PGROTATE_*` are node statistics updated with `mod_lruvec_state()`, not VM
  events. The multi-generation LRU does count `PGREFILL` and never touches
  `NR_ISOLATED_*`; reader A had both the other way round.
- **Non-present page table entries.** pte_to_swp_entry(), is_migration_entry()
  and non_swap_entry() are gone; the tree reads them through `softleaf_t` and
  `softleaf_from_pte()` in `include/linux/leafops.h`. Reader B knew none of
  the new helpers and reader A mixed the two sets.
- **list_lru walks.** A callback that returns `LRU_STOP` or `LRU_RETRY` must
  have dropped the list lock; the header comment says the opposite.
- **Shrinker return values.** `SHRINK_EMPTY` and 0 mean different things.
- **Hopeless nodes.** The failure count is reset only through
  `kswapd_try_clear_hopeless()`, which requires `pgdat_balanced()`, and
  `wakeup_kswapd()` returns early for such a node.
- **Swap devices.** There is one global `swap_avail_head`, not one list per
  node (reader A), and no SWP_VALID flag (reader B).

## What reader B got wrong as well

Reader B was wrong about fundamentals: fresh swap slots start with a count of
one (they start at zero, pinned by the swap cache); the swap cache is a set of
sharded address spaces with an xarray each; reclaim still calls `->writepage`;
the multi-generation LRU bypasses `folio_check_references()`;
`folio_inc_gen()` keeps the reference bits; kswapd ends its loop when every
zone is balanced; direct reclaimers wait on `reclaim_wait`; swapoff kills the
device's reference before `try_to_unuse()`; shrinkers are protected by
shrinker_rwsem; MIGRATE_SYNC_NO_COPY exists; movable pages are marked through
the mapping pointer. It also offered more names that do not exist than names
that do in most swap answers.

## What the readers already knew

The files and the entry points (A and C with at most a line to fix), the three
writeback tags and which function moves each (A and C), the difference between
swap-backed and in the swap cache (A and C; B half), what a `migrate_folio`
callback must do and which helpers can sleep (A and C), when kswapd drops its
order (A and C), and the rule for bounded scans under the LRU lock and the
order of the reference count and dirty tests in `__remove_mapping()` (C). These
are the questions that were shrunk or left out.

## Where the hand-written guide is stale

Nothing in it was found to be wrong: every statement checked during the survey
and every name in it holds in this tree. What it lacks is what the readers most
often got wrong: where a slot's count, zero flag and cgroup id live, the
functions that replaced the swap count and swap cache API, the per-node objcg
and the locks taken at reparenting, and the fact that the reclaim counters are
now lruvec statistics. One sentence is slightly too strong: it says the old
folio is not uncharged separately in migration, but `mem_cgroup_migrate()`
does settle the page counters itself when the objcg re-derived for the new
folio's node is the root one.

## Left out of the build set

For space, not because the readers know them: the step by step questions
(`shrink_folio_list()`, the swap-out sequence, `do_swap_page()`, swapoff,
the phases of one migration), the pressure questions (anon and file balance,
memory.min and memory.low, throttling, the kswapd loop, hopeless nodes, direct
reclaim throttling, proactive reclaim), shrinkers and `list_lru`, all of the
multi-generation LRU apart from the tier bits, the swap device and cluster
structures, slot allocation, zswap, swap readahead, shmem's side of swap,
soft leaf entries, the migration API, migration entries, movable pages, dirty
throttling itself and how the limits are enforced. The entry points were
dropped because every reader knew them. The two generic list hazards from the
hand-written guide (a counter-gated tracking list, a safe list walk that drops
its lock) were dropped because readers A and C stated both rules correctly,
needing a fix only to the example, and the rules are not about this
subsystem. If a built guide comes in under its size, the swap-in fault path
and the list_lru callback rules are the first to add back, because most
readers were wrong about both and the header comment is wrong about the
second.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too, so it overstates
reader B's gap; the corrections are what count. Reader B's first run died when
the scratch disk filled and was repeated; the figures are from the repeat.

```
reader A: 196 corrections, 41% rewritten on average
reader B: 269 corrections, 79% rewritten on average
reader C: 185 corrections, 25% rewritten on average

question                            reader A        reader B        reader C
reclaim.core-files                   0% ( 0)        22% ( 5)         0% ( 1)
reclaim.entry-points                 4% ( 1)         7% ( 4)         7% ( 3)
reclaim.docs-and-tests              15% ( 1)        56% ( 3)        18% ( 1)
reclaim.reclaim-callers             25% ( 5)        43% ( 6)        15% ( 7)
reclaim.folio-list-steps            35% ( 1)        91% ( 1)        19% ( 2)
reclaim.dirty-file-folios           30% ( 1)        80% ( 1)        46% ( 2)
reclaim.writeback-in-reclaim        37% ( 2)        79% ( 1)        18% ( 1)
reclaim.references-check            70% ( 2)        92% ( 1)        36% ( 1)
reclaim.remove-mapping              21% ( 2)        79% ( 4)         1% ( 1)
reclaim.anon-swap-step              20% ( 1)        88% ( 3)        12% ( 3)
reclaim.demotion                    53% ( 4)        88% ( 3)        22% ( 3)
reclaim.isolation                   23% ( 1)        84% ( 3)        20% ( 1)
reclaim.bounded-lru-scan            21% ( 1)        89% ( 1)         9% ( 1)
reclaim.scan-balance                63% ( 5)        81% ( 4)        28% ( 1)
reclaim.memcg-protection            49% ( 3)        88% ( 3)        23% ( 1)
reclaim.throttling                  18% ( 2)        83% ( 4)        27% ( 1)
reclaim.kswapd-loop                 58% ( 5)        80% ( 4)        33% ( 1)
reclaim.kswapd-order-drop           11% ( 1)        76% ( 1)        24% ( 1)
reclaim.kswapd-failures             62% ( 1)        86% ( 4)        22% ( 2)
reclaim.direct-throttle             38% ( 1)        79% ( 6)        20% ( 1)
reclaim.zone-skip-consistency       29% ( 1)        82% ( 3)        46% ( 1)
reclaim.proactive                   69% ( 2)        85% ( 3)        41% ( 5)
reclaim.vmstat-counters             67% ( 3)        91% ( 3)        18% ( 4)
reclaim.classic-mglru-pairing       33% ( 2)        68% ( 3)        19% ( 3)
reclaim.unevictable                  4% ( 1)        80% ( 3)        18% ( 3)
reclaim.workingset-shadows          29% ( 3)        78% ( 4)        18% ( 4)
reclaim.shrinker-api                60% ( 4)        75% ( 4)        18% ( 2)
reclaim.list-lru                    54% ( 4)        80% ( 3)        10% ( 1)
reclaim.mglru-structure             19% ( 3)        79% ( 5)         7% ( 1)
reclaim.mglru-enable                58% ( 2)        84% ( 1)        56% ( 1)
reclaim.mglru-aging                 32% ( 2)        82% ( 1)        29% ( 1)
reclaim.mglru-eviction              49% ( 4)        94% ( 1)        32% ( 1)
reclaim.mglru-refs-flags            53% ( 4)        93% ( 5)        50% ( 5)
reclaim.mglru-tier-bits             24% ( 2)        82% ( 2)        17% ( 1)
reclaim.mglru-memcg-lru             40% ( 3)        87% ( 2)        31% ( 3)
reclaim.swap-entry-encoding         63% ( 7)        76% ( 4)        41% ( 5)
reclaim.swap-device-and-clusters    43% ( 4)        71% ( 4)        45% ( 3)
reclaim.swap-slot-state             65% ( 4)        89% ( 2)        37% ( 3)
reclaim.swap-count                  85% ( 3)        85% ( 2)        27% ( 1)
reclaim.swap-cache-api              33% ( 5)        76% ( 6)        21% ( 4)
reclaim.swap-cache-lookup-usage     57% ( 1)        72% ( 2)        21% ( 2)
reclaim.swap-residency              46% ( 3)        84% ( 3)        45% ( 3)
reclaim.swap-address-space          43% ( 1)        88% ( 1)        29% ( 1)
reclaim.swapbacked-vs-swapcache      7% ( 1)        47% ( 2)         5% ( 1)
reclaim.swap-alloc                  51% ( 5)        72% ( 8)        29% ( 3)
reclaim.swap-alloc-local-lock       55% ( 1)        90% ( 1)        33% ( 2)
reclaim.swap-out-sequence           65% ( 2)        82% ( 1)        16% ( 2)
reclaim.swap-io                     84% ( 2)        91% ( 3)        78% ( 1)
reclaim.zswap                       55% ( 1)        74% ( 3)        22% ( 1)
reclaim.swapin-fault                64% ( 4)        75% ( 6)        34% ( 6)
reclaim.swapin-large                87% ( 1)        89% ( 4)        80% ( 3)
reclaim.swapin-conflict-usage       79% ( 1)        78% ( 1)        59% ( 2)
reclaim.swap-readahead              45% ( 1)        87% ( 2)        14% ( 1)
reclaim.swap-device-lifetime        59% ( 2)        80% ( 8)        20% ( 3)
reclaim.swap-device-usage           63% ( 3)        83% ( 2)        16% ( 1)
reclaim.swapoff                     40% ( 1)        82% ( 5)        28% ( 1)
reclaim.swap-memcg                  47% ( 8)        69% ( 7)        39% ( 9)
reclaim.swap-memcg-usage            20% ( 1)        87% ( 1)        26% ( 1)
reclaim.shmem-swap                  42% ( 2)        82% ( 4)        11% ( 3)
reclaim.counter-gated-list          32% ( 1)        79% ( 1)        38% ( 3)
reclaim.list-walk-lock-drop         32% ( 1)        85% ( 1)        19% ( 0)
reclaim.migrate-api                 32% ( 3)        60% ( 7)        24% ( 3)
reclaim.migrate-phases              14% ( 2)        76% ( 3)        17% ( 3)
reclaim.migrate-batch               39% ( 1)        89% ( 3)         8% ( 2)
reclaim.migrate-refcount            42% ( 1)        91% ( 2)        14% ( 1)
reclaim.migrate-callback            20% ( 1)        84% ( 3)         0% ( 0)
reclaim.migrate-callback-sleeps     14% ( 1)        82% ( 2)        13% ( 0)
reclaim.migrate-entries             23% ( 4)        78% ( 5)        15% ( 3)
reclaim.migrate-rmap-lock-scope     40% ( 2)        74% ( 5)        57% ( 3)
reclaim.migrate-state-copy          52% ( 3)        84% ( 5)        10% ( 1)
reclaim.migrate-memcg               35% ( 2)        78% ( 4)        37% ( 3)
reclaim.migrate-movable-ops         56% ( 1)        80% ( 3)        22% ( 1)
reclaim.migrate-isolation-count     41% ( 1)        74% ( 1)        20% ( 1)
reclaim.writeback-tags              16% ( 1)        44% ( 3)         0% ( 0)
reclaim.writeback-tag-lifecycle      8% ( 1)        74% ( 4)        13% ( 1)
reclaim.writeback-iter              34% ( 1)        86% ( 4)        13% ( 1)
reclaim.writeback-tag-usage         44% ( 1)        89% ( 1)        22% ( 1)
reclaim.writeback-flags             22% ( 1)        84% ( 3)        10% ( 1)
reclaim.dirty-throttling            48% ( 3)        80% ( 6)        39% ( 3)
reclaim.wb-domain-usage             46% ( 2)        81% ( 2)        51% ( 2)
reclaim.memcg-charge-api            36% ( 2)        72% ( 3)        20% ( 5)
reclaim.memcg-offline               80% ( 1)        87% ( 1)        34% ( 1)
reclaim.memcg-lookup                45% ( 1)        85% ( 1)         4% ( 1)
reclaim.memcg-lruvec-lock           57% ( 1)        88% ( 0)        20% ( 1)
reclaim.memcg-uncharge              63% ( 6)        85% ( 6)        35% ( 6)
reclaim.memcg-ids-and-refs          66% ( 3)        94% ( 1)        20% ( 1)
reclaim.memcg-stock                 35% ( 2)        90% ( 1)        20% ( 1)
reclaim.memcg-limits                37% ( 2)        93% ( 1)        36% ( 3)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `reclaim.references-check`, `reclaim.scan-balance`, `reclaim.kswapd-loop`, `reclaim.kswapd-failures`, `reclaim.shrinker-api`, `reclaim.mglru-enable`, `reclaim.mglru-refs-flags`, `reclaim.swap-entry-encoding`, `reclaim.swap-device-and-clusters`, `reclaim.swap-alloc`, `reclaim.swap-out-sequence`, `reclaim.swapin-fault`, `reclaim.memcg-limits`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `reclaim.folio-list-steps`, `reclaim.writeback-in-reclaim`, `reclaim.remove-mapping`, `reclaim.anon-swap-step`, `reclaim.isolation`, `reclaim.memcg-protection`, `reclaim.throttling`, `reclaim.workingset-shadows`, `reclaim.mglru-structure`, `reclaim.mglru-aging`, `reclaim.mglru-eviction`, `reclaim.shmem-swap`, `reclaim.migrate-api`, `reclaim.migrate-phases`, `reclaim.migrate-refcount`, `reclaim.migrate-callback`, `reclaim.migrate-entries`, `reclaim.writeback-flags`.

## Questions reorganised

72 questions became 69, by subject: shrinking a folio list, LRU lists and counters, pressure,
shrinkers, the multi-generation LRU, swap slots and cache, swap devices and allocation, swapping out
and in, the memcg charge, the folio to memcg binding, migration, writeback tags and flags. Merged:
`writeback-tags` + `writeback-tag-lifecycle` to `writeback-tag-transitions`;
`swapbacked-vs-swapcache` + `swap-address-space` to `swapcache-identity`; `swap-device-lifetime` +
`swap-device-usage` to `swap-device-pinning`. Nothing dropped whole; inventories inside questions
went (swap structure members, `migrate_pages()` arguments). The step lists (`folio-list-steps`,
`swap-out-sequence`, `swapin-fault`) ask which order must hold and which race each recheck closes.
