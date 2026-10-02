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
