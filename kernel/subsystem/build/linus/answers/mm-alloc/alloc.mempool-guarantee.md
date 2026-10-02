- `mempool_alloc_from_pool()` and `mempool_adjust_gfp()`: both exist in
  `mm/mempool.c`; the wait on `pool->wait` is inside
  `mempool_alloc_from_pool()`, not in `mempool_alloc_noprof()`.
- `bio_alloc_bioset()` in `block/bio.c`: does not clear
  `__GFP_DIRECT_RECLAIM` based on `current->bio_list`.
  - Mask without `__GFP_DIRECT_RECLAIM`: returns NULL when the slab attempt
    fails, before any `mempool_alloc()`.
  - Mask with it, when the slab attempt fails: calls
    `punt_bios_to_rescuer()`, then `mempool_alloc()` with the caller's
    unchanged mask, and uses the result with no NULL check.
- `mempool_alloc_bulk_noprof()`: the way to take several elements from one
  pool.
  - Takes no mask; uses `GFP_KERNEL` internally and always returns 0 with all
    `count` elements filled.
  - Takes from the reserve only when the reserve holds every element still
    missing; otherwise it takes none and retries, waiting on `pool->wait`
    from the second pass on.
  - `count > pool->min_nr`: `VM_WARN_ON_ONCE()`, which compiles to nothing
    without `CONFIG_DEBUG_VM`.
  - A caller that needs no-IO wraps the call in `memalloc_noio_save()`, as
    `blk_crypto_alloc_enc_bio()` does.
- `mempool_alloc_noreserve()` in `include/linux/mempool.h`: calls
  `pool->alloc` directly, never touches the reserve and never waits on
  `pool->wait`, so it can return NULL also with a mask that has
  `__GFP_DIRECT_RECLAIM`, and needs a NULL check.
