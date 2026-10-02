- Accepted gfp bits: `__GFP_ACCOUNT`, `__GFP_ZERO`, `__GFP_NOWARN`,
  `__GFP_NOMEMALLOC`; the last two are ORed in by
  `__kmalloc_nolock_noprof()`.
- There is no __GFP_NO_OBJ_EXT gfp bit here; `SLAB_ALLOC_NO_OBJ_EXT` in
  `mm/slab.h` is a slab alloc flag and callers of `kmalloc_nolock()` cannot
  pass it.
- Any other gfp bit: only trips `VM_WARN_ON_ONCE()`; the request is neither
  rejected nor stripped of the bit.
- No-spin mode is carried in `alloc_flags` of `struct slab_alloc_context`
  (`mm/slub.c`) as `SLAB_ALLOC_NOLOCK`, and tested with
  `alloc_flags_allow_spinning()`.
- `mm/slub.c` does not call `gfpflags_allow_spinning()`; an ordinary slab
  request whose gfp has no reclaim bit still has `SLAB_ALLOC_DEFAULT` and
  spins on slab locks.
- `kmalloc_flags()` in `mm/slab.h`: internal entry that takes `alloc_flags`;
  `__kmalloc_flags_noprof()` routes to `__kmalloc_nolock_noprof()` when
  `SLAB_ALLOC_NOLOCK` is set, as for obj_exts vectors and sheaves.
- Size 0: returns `ZERO_SIZE_PTR` before any context test.
- Returns NULL without trying, in this order:
  - `can_spin_trylock()` is false, which includes `!CONFIG_SMP` in NMI;
  - `size > KMALLOC_MAX_CACHE_SIZE`;
  - `!(s->flags & __CMPXCHG_DOUBLE) && !kmem_cache_debug(s)`.
- Bucket retry: taken once after any NULL from `___slab_alloc()`, from the
  next larger kmalloc bucket (`size = s->object_size + 1`);
  `mm/slub.c` does not call `local_lock_is_locked()`.
- There is no __slab_alloc_node() here; `__kmalloc_nolock_noprof()` calls
  `alloc_from_pcs()` and then `___slab_alloc()` directly.
