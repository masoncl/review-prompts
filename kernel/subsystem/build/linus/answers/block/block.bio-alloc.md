- `bio_alloc_bioset()` order of sources, all in its own body in `block/bio.c`
  (there is no bvec_alloc() or bvec_alloc_gfp() in this tree):
  1. Per-cpu cache, `bio_alloc_percpu_cache()`, when `bs->cache` is set and
     `nr_vecs <= BIO_INLINE_VECS`. Never sleeps without
     `CONFIG_DEBUG_KMEMLEAK`.
  2. `kmem_cache_alloc()` on `bs->bio_slab`, not the mempool. Never sleeps.
  3. For `nr_vecs > BIO_INLINE_VECS`, `kmem_cache_alloc()` on the slab chosen
     by `biovec_slab()`. Never sleeps. On failure the bio from step 2 goes
     back with `kmem_cache_free()` and step 4 runs if the mask has
     `__GFP_DIRECT_RECLAIM`.
  4. Slow path, only when steps 1 to 3 gave no bio and the mask has
     `__GFP_DIRECT_RECLAIM`: `punt_bios_to_rescuer()`, then `mempool_alloc()`
     on `bs->bio_pool`, then for `nr_vecs > BIO_INLINE_VECS`
     `mempool_alloc()` on `bs->bvec_pool`. Both use the caller's original
     mask and may sleep.
- Mask for steps 2 and 3: when the caller's mask has `__GFP_DIRECT_RECLAIM`,
  `try_alloc_gfp()` strips it and `__GFP_IO` for every bioset, whatever
  `current->bio_list` holds and whether or not there is a rescuer.
- Mask without `__GFP_DIRECT_RECLAIM`: NULL as soon as steps 1 to 3 fail;
  step 4 is not entered and the mempool reserve is never used.
- `nr_vecs > 0` on a bioset without `BIOSET_NEED_BVECS`: `WARN_ON_ONCE()` and
  NULL under any mask, before any allocation, also for
  `nr_vecs <= BIO_INLINE_VECS`.
- `REQ_ALLOC_CACHE` in the caller's `opf` is ignored: `bio_alloc_bioset()`
  sets it when the step 1 condition holds and clears it otherwise and on the
  slow path. Nothing outside `block/bio.c` sets or tests the flag.
- Slow path: the two `mempool_alloc()` results are used unchecked; the code
  relies on `mempool_alloc()` in `mm/mempool.c` not returning NULL when the
  mask has `__GFP_DIRECT_RECLAIM`.
- `bio_alloc_clone()` with a mask that has `__GFP_DIRECT_RECLAIM`: NULL only
  from `bio_integrity_clone()`, which runs when `bio_src` has an integrity
  payload and allocates with `kmalloc_flex()` in `bio_integrity_alloc()`.
- `bio_crypt_clone()` is backed by `mempool_alloc()` in `__bio_crypt_clone()`
  and fails only for a mask without `__GFP_DIRECT_RECLAIM`.
