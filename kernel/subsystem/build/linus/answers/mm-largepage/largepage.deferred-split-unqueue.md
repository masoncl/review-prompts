- Refcount: must be zero, at the final put or frozen;
  `__folio_unqueue_deferred_split()` has
  `WARN_ON_ONCE(folio_ref_count(folio))`. Holding a reference is not an
  alternative.
- Why zero: a non-empty `_deferred_list` may be linked on the on-stack list
  of `deferred_split_scan()`, which no lock covers; the shrinker holds a
  reference on every folio on that list.
- Unqueue sites: every caller of `folio_unqueue_deferred_split()`, plus two
  that delete the entry directly, `__folio_freeze_and_split_unmapped()` and
  `deferred_split_isolate()`.
- `__folio_put()` and `folios_put_refs()` are in `mm/folio.c`; there is no
  mm/swap.c here.
- `free_unref_folios()`: does not unqueue; its callers do, for example
  `shrink_folio_list()` and `move_folios_to_lru()`.
- There is no folio_undo_large_rmappable() and no memcg1_swapout(); the
  swapout site is `__memcg1_swapout()` in `mm/memcontrol-v1.c`.
- `__folio_freeze_and_split_unmapped()`: takes the sublist lock before
  `folio_ref_freeze()`, for anon folios of order > 1 only, so the shrinker
  never sees the frozen folio on the list.
- `__folio_freeze_and_split_unmapped()` when the freeze fails: drops the
  lock, returns `-EAGAIN`, and the folio stays queued.
- `deferred_split_isolate()`: a folio whose `folio_try_get()` fails is
  removed from the queue and its partially-mapped flag cleared, not skipped.
- `deferred_split_scan()`: a folio that is not partially mapped and is
  mlocked or not underused is not requeued by the scan.
- Before the memcg changes: the entry must be off the queue while
  `memcg_data` is still set; `__folio_unqueue_deferred_split()` warns on
  `!folio_memcg_charged()` unless `mem_cgroup_disabled()`.
- `uncharge_folio()` and `mem_cgroup_migrate()`: the
  `WARN_ON_ONCE(folio_unqueue_deferred_split())` there is a check that runs
  just before `memcg_data` is cleared; the real unqueue must already have
  happened.
- `mem_cgroup_replace_folio()`: does not call the helper.
- Memcg offline: needs no unqueue; `memcg_reparent_list_lrus()` splices each
  sublist into the parent's and marks the old one dead.
