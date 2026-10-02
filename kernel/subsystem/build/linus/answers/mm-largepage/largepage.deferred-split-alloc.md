- `folio_memcg_alloc_deferred()` in `mm/huge_memory.c`: allocates the
  `deferred_split_lru` sublists (`struct list_lru_memcg`) for the folio's
  memcg and for each ancestor that lacks them, through
  `folio_memcg_list_lru_alloc()`; it changes nothing in the folio.
- Precondition: the folio is already charged, since the memcg comes from
  `folio_memcg()`.
- Precondition: sleepable context, since it allocates with `GFP_KERNEL`;
  in-tree callers run it before taking the page table lock.
- Returns 0 without allocating when `mem_cgroup_disabled()`, when the lru is
  not memcg-aware, or when the memcg already has sublists; the stub without
  `CONFIG_TRANSPARENT_HUGEPAGE` returns 0.
- Returns `-ENOMEM` on failure; callers treat that as a failed folio
  allocation, for example `alloc_anon_folio()` puts the folio and falls back
  to order 0.
- Orders: required for anon folios of order > 1; `alloc_anon_folio()` and
  `__swap_cache_alloc()` guard the call with `order > 1`;
  `vma_alloc_anon_folio_pmd()` and `collapse_huge_page()` call it
  unconditionally.
- Folio from a site that did not call it, in a memcg that has no sublists:
  `deferred_split_folio()` neither fails nor skips; it queues the folio on
  the sublist of the nearest ancestor that has one, in the end the per-node
  global list.
- The only signal: `VM_WARN_ON(!css_is_dying())` in
  `lock_list_lru_of_memcg()`, compiled in under `CONFIG_DEBUG_VM` only.
- **Unsafe usage**: charging and mapping a new anon folio of order > 1
  without calling `folio_memcg_alloc_deferred()`.
  - Unsafe: once the folio is queued on an ancestor's sublist, a later
    allocation of the memcg's own sublists makes
    `__folio_unqueue_deferred_split()` lock the memcg's sublist and run
    `__list_lru_del()` on an entry that sits on the ancestor's list.
  - Safe: charge, then call it, then map, as `vma_alloc_anon_folio_pmd()`
    does; `lock_list_lru_of_memcg()` defines the requirement.
  - Safe: folios produced by a split, when the site that allocated the
    original folio called it; `__split_folio_to_order()` copies
    `memcg_data`, so they stay in the memcg of the original folio.
