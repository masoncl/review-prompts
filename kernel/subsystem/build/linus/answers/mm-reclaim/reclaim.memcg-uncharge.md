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
