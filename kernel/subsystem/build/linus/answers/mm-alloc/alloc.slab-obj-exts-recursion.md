- `alloc_slab_obj_exts()`: allocates `slab_obj_ext_size(slab) *
  slab->objects` bytes with `kmalloc_flags()` and `__GFP_ZERO`. It does not
  call `kcalloc_node()`.
- `SLAB_ALLOC_NO_OBJ_EXT`: set by `alloc_slab_obj_exts()` only when
  `is_kmalloc_normal(s)`; it makes `kmalloc_slab()` pick the cache type
  `KMALLOC_NO_OBJ_EXT`.
- `KMALLOC_NO_OBJ_EXT` caches: created in `new_kmalloc_cache()` in
  `mm/slab_common.c` with `SLAB_NO_OBJ_EXT`, so their slabs never get a
  vector. They alias `KMALLOC_NORMAL` when `need_kmalloc_no_objext()` is
  false.
- Vector of any other cache: comes from a normal kmalloc cache, because
  `OBJCGS_CLEAR_MASK` strips the bits that select another type. That slab's
  own vector then comes from `KMALLOC_NO_OBJ_EXT`, where the chain ends.
- `CONFIG_DEBUG_VM`: `alloc_slab_obj_exts()` warns if the vector came from
  any other kind of cache.
- No size adjustment keeps the vector out of its own cache; there is no
  obj_exts_alloc_size().
- There is no mark_objexts_empty(). `mark_obj_codetag_empty()` is called only
  from `__free_empty_sheaf()`, for sheaves of kmalloc caches.
- `SLAB_ALLOC_NEW_SLAB`: passed by `account_slab()`; it lets
  `alloc_slab_obj_exts()` assign the field without `cmpxchg()`.
