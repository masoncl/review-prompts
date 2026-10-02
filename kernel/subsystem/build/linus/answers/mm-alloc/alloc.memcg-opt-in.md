- `memcg_slab_post_alloc_hook()` in `mm/slub.c`: charges when `__GFP_ACCOUNT`
  or `SLAB_ACCOUNT` is set; either one alone is enough.
- There is no memcg_slab_pre_alloc_hook() here; `slab_pre_alloc_hook()` does
  no memcg work.
- `SLAB_MAY_ACCOUNT`: not an opt-in. It marks caches whose slabs reserve an
  objcg slot per object; see `cache_needs_objcg()` in `mm/slab.h`.
- `SLAB_MAY_ACCOUNT` is added by `__kmem_cache_create_args()` and
  `new_kmalloc_cache()` unless `mem_cgroup_kmem_disabled()`; for example the
  `KMALLOC_NORMAL` and `KMALLOC_NO_OBJ_EXT` kmalloc caches lack it when
  `CONFIG_SLUB_TINY` is off.
- `new_slab()`: keeps only `GFP_RECLAIM_MASK | GFP_CONSTRAINT_MASK`, so
  `__GFP_ACCOUNT` never reaches the page allocator for a slab page.
- Page allocator: the charge is in `__alloc_frozen_pages_noprof()` in
  `mm/page_alloc.c`; on failure the page goes to `__free_frozen_pages()` and
  NULL is returned.
- `alloc_slab_obj_exts()` failure in `__memcg_slab_post_alloc_hook()`: the
  object is returned to the caller uncharged; the allocation does not fail.
- `__GFP_NOFAIL` is stripped from the vector allocation (`OBJCGS_CLEAR_MASK`
  in `mm/slub.c`), so a `__GFP_NOFAIL | __GFP_ACCOUNT` object can also come
  back uncharged.
- KFENCE object on a slab with no vector: skipped, returned uncharged.
- `try_charge_memcg()` in `mm/memcontrol.c`: forces the charge over the limit
  for `__GFP_NOFAIL`, for `__GFP_HIGH` (so `GFP_ATOMIC | __GFP_ACCOUNT`), and
  for a `PF_MEMALLOC` task; none of these returns `-ENOMEM`.
