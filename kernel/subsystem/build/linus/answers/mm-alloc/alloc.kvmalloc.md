- `kmalloc_gfp_adjust()`, for `size > PAGE_SIZE` only: adds `__GFP_NOWARN`,
  clears `__GFP_DIRECT_RECLAIM` unless `__GFP_RETRY_MAYFAIL` is set, clears
  `__GFP_NOFAIL`.
- `kmalloc_gfp_adjust()` does not add `__GFP_NORETRY` and does not test
  `PAGE_ALLOC_COSTLY_ORDER`.
- Masks that skip the fallback: none. `__kvmalloc_node_noprof()` has no early
  return for non-blocking masks, nor any test of `__GFP_FS` or `__GFP_IO`.
- `gfpflags_allow_blocking()` in `__kvmalloc_node_noprof()`: only decides
  whether `VM_ALLOW_HUGE_VMAP` is passed to `__vmalloc_node_range_noprof()`.
- `GFP_ATOMIC` or `GFP_NOWAIT` with `size > PAGE_SIZE`: can return vmalloc
  memory.
- Fallback skipped only when: kmalloc succeeded, `size <= PAGE_SIZE`, or
  `size > INT_MAX`.
- `__GFP_NORETRY`: the kerneldoc of `kvmalloc_node()` calls it unsupported, but
  no code in `__kvmalloc_node_noprof()` tests for it.
