- `kmalloc_gfp_adjust()`: in `mm/slub.c`, not `mm/util.c`.
- `kmalloc_gfp_adjust()` keeps `__GFP_KSWAPD_RECLAIM`, so without
  `__GFP_RETRY_MAYFAIL` the slab attempt of a large `kvmalloc()` cannot sleep
  but can still wake kswapd.
- `kmalloc_gfp_adjust()` callers: `__kvmalloc_node_noprof()` and
  `kvrealloc_node_align_noprof()`.
- `mempool_adjust_gfp()`: in `mm/mempool.c`; it takes a pointer to the mask.
  - Through the pointer: adds
    `__GFP_NOMEMALLOC | __GFP_NORETRY | __GFP_NOWARN` for every pass.
  - Return value: that mask without `__GFP_DIRECT_RECLAIM | __GFP_IO`, used
    for the first pass only.
- `vmalloc_gfp_adjust()` in `mm/vmalloc.c`: adds `__GFP_NOWARN`, and clears
  `__GFP_NOFAIL` for a high-order attempt.
- `vm_area_alloc_pages()`: also clears `__GFP_DIRECT_RECLAIM` for its
  large-order attempt.
- `pcpu_alloc_noprof()`: passes to its backing allocators only
  `gfp & (GFP_NOIO | __GFP_NORETRY | __GFP_NOWARN)`, after
  `current_gfp_context()`; `__GFP_NOFAIL` is dropped.
- There is no limit_gfp_mask() here; `thp_shmem_limit_gfp_mask()` in
  `include/linux/huge_mm.h` does that job for `mm/shmem.c`.
- There are no __GFP_NOFS or __GFP_NOIO bits; the restriction is the absence
  of `__GFP_FS` or `__GFP_IO`, so a wrapper keeps it by not setting them.
- **Potentially unsafe usage**: clearing `__GFP_NOFAIL` from the caller's
  mask.
  - Unsafe: when the attempt without the bit is the last one and its failure
    is returned to the caller; a `__GFP_NOFAIL` caller does not test for
    NULL.
  - Safe: `allocate_slab()` retries at the minimum order with the unmodified
    `flags`.
  - Safe: `__kvmalloc_node_noprof()` passes the unmodified `flags` to
    `__vmalloc_node_range_noprof()` for a size up to `INT_MAX`; for size up
    to `PAGE_SIZE` the bit is never cleared.
  - Safe: when the allocation is optional and the caller's request succeeds
    without it, as `alloc_slab_obj_exts()` with `OBJCGS_CLEAR_MASK`;
    `__memcg_slab_post_alloc_hook()` then returns the object uncharged.
