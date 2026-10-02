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
