- `__kfence_alloc()` tests, in order: `size > PAGE_SIZE`;
  `flags & GFP_ZONEMASK`; `__GFP_THISNODE` with `num_online_nodes() > 1`;
  cache flags `SLAB_CACHE_DMA | SLAB_CACHE_DMA32`; cache flag
  `SLAB_SKIP_KFENCE`.
- `__kfence_alloc()` does not test `SLAB_NOLEAKTRACE`,
  `SLAB_TYPESAFE_BY_RCU`, or any object-extension GFP bit.
- `SLAB_SKIP_KFENCE`: returns `NULL` without counting
  `KFENCE_COUNTER_SKIP_INCOMPAT`; the earlier tests count it.
- KFENCE object after allocation: still passes through
  `slab_post_alloc_hook()`; there `is_kfence_address()` skips the
  `memset()`, and `__memcg_slab_post_alloc_hook()` returns the object
  uncharged when its slab has no extension vector.
- KFENCE zeroing: `kfence_guarded_alloc()` zeroes the object itself when
  `slab_want_init_on_alloc()` is true.
- `__alloc_contig_verify_gfp_mask()` clears silently, without rejecting or
  warning: `GFP_ZONEMASK`, `__GFP_RECLAIMABLE`, `__GFP_WRITE`,
  `__GFP_HARDWALL`, `__GFP_THISNODE`, `__GFP_MOVABLE`.
- `__alloc_contig_verify_gfp_mask()` then returns `-EINVAL` for any bit
  outside this set:
  - reclaim: `__GFP_IO`, `__GFP_FS`, `__GFP_RECLAIM`
  - action: `__GFP_COMP`, `__GFP_RETRY_MAYFAIL`, `__GFP_NOWARN`,
    `__GFP_ZERO`, `__GFP_ZEROTAGS`, `__GFP_SKIP_ZERO`, `__GFP_SKIP_KASAN`
- Rejected, for example: `__GFP_NOFAIL`, `__GFP_NORETRY`, `__GFP_HIGH`,
  `__GFP_MEMALLOC`, `__GFP_NOMEMALLOC`, `__GFP_ACCOUNT`.
- Second mask, for compaction and migration: the reclaim bits plus
  `__GFP_RETRY_MAYFAIL` and `__GFP_NOWARN` from the caller, with
  `__GFP_MOVABLE | __GFP_RETRY_MAYFAIL` always added.
- `alloc_contig_frozen_range_noprof()`: the only caller; it applies
  `current_gfp_context()` before the check.
