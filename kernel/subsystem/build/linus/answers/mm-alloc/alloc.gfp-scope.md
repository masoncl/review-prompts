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
