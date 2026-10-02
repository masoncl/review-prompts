- `filemap_alloc_folio()`: takes three arguments, `(gfp, order, policy)`; the
  third is a `struct mempolicy *`, NULL at every caller except
  `__filemap_get_folio_mpol()`.
- `filemap_alloc_folio()` with a non-NULL `policy`: allocates through
  `folio_alloc_mpol_noprof()` with `NO_INTERLEAVE_INDEX`, and applies neither
  cpuset spreading nor the task mempolicy.
- `filemap_alloc_folio()` without `CONFIG_NUMA`: the inline in
  `include/linux/pagemap.h` ignores `policy`.
- `__filemap_get_folio_mpol()`: the only path that hands a caller's policy to
  `filemap_alloc_folio()`; `virt/kvm/guest_memfd.c` uses it.
- `folio_alloc()`: uses `default_policy`, not the task mempolicy, when
  `in_interrupt()` or `__GFP_THISNODE` is set; see
  `alloc_frozen_pages_noprof()` in `mm/mempolicy.c`.
- `vma_alloc_folio()` without `CONFIG_NUMA`: the inline in
  `include/linux/gfp.h` ignores `vma` and `addr`, and does not add
  `__GFP_NOWARN` for `VM_DROPPABLE`; only the `mm/mempolicy.c` body adds it.
- There is no folio_prep_large_rmappable() here; `page_rmappable_folio()` in
  `mm/internal.h` sets the large-rmappable flag on any large folio, page
  cache folios included.
- `_deferred_list`: initialised by `prep_compound_head()` only for order > 1;
  an order-1 folio has none.
- Contents: `post_alloc_hook()` zeroes when `want_init_on_alloc()` is true,
  which is `__GFP_ZERO` or `init_on_alloc` enabled, and
  `want_init_on_free()` is false.
- User folios: `alloc_anon_folio()` and `vma_alloc_anon_folio_pmd()` zero by
  hand, with `folio_zero_user()`, only when `user_alloc_needs_zeroing()`.
- `vma_alloc_zeroed_movable_folio()`, generic version in
  `include/linux/highmem.h`: passes no `__GFP_ZERO`; it calls
  `clear_user_highpage()` under the same test.
- memcg: uncharged unless `__GFP_ACCOUNT`; with it and
  `memcg_kmem_online()`, `__alloc_frozen_pages_noprof()` kmem-charges the
  page, and a failed charge frees it and returns NULL.
- Large anon folio, order > 1: the allocator does not allocate the memcg's
  sublist of `deferred_split_lru`; callers call
  `folio_memcg_alloc_deferred()` after `mem_cgroup_charge()`, for example
  `alloc_anon_folio()` and `vma_alloc_anon_folio_pmd()`.
- Without `folio_memcg_alloc_deferred()`, when the memcg has no sublist yet:
  `lock_list_lru_of_memcg()` hits `VM_WARN_ON()` unless the memcg is dying,
  and returns the sublist of the nearest ancestor that has one, so the folio
  is queued there.
