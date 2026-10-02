- `memblock_free_all()`: declared in `mm/mm_init.h`, called only by
  `mm_core_init()` in `mm/mm_init.c`, directly; `mem_init()` and
  `kmem_cache_init()` follow it. No arch code calls it.
- `WARN_ON_ONCE(slab_is_available())` and the `kzalloc_node(size,
  GFP_NOWAIT, nid)` fallback are in `memblock_alloc_range_nid()`, not
  `memblock_alloc_internal()`; `memblock_phys_alloc_range()` and
  `memblock_phys_alloc_try_nid()` get the fallback too and return
  `virt_to_phys()` of slab memory.
- The fallback ignores `align`, `start` and `end`.
- `memblock_alloc_hugetlb()`: does not call `memblock_alloc_range_nid()`,
  so it gets neither the warning nor the slab fallback.
- Unwarned gap: from `memblock_free_all()` until `create_kmalloc_caches()`
  sets `slab_state = UP` inside `kmem_cache_init()`; it covers `mem_init()`.
- Full region array before `memblock_allow_resize()`:
  `memblock_double_array()` panics with "cannot resize"; nothing overflows.
