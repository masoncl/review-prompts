- `KMALLOC_DMA` cache names: "dma-kmalloc-<size>", see `KMALLOC_DMA_NAME()` in
  `mm/slab_common.c`.
- `kmalloc_fix_flags()`: defined in `mm/slab_common.c`, not `mm/slub.c`.
- Warning form: `pr_warn()` followed by `dump_stack()`, printed on every hit;
  it is not once-only, and it is compiled out only without `CONFIG_PRINTK`.
- Large path (`___kmalloc_large_node()`): after `kmalloc_fix_flags()` it only
  adds `__GFP_COMP`, so `__GFP_DMA` and `__GFP_MOVABLE` reach the page
  allocator unchanged.
- Preferred node without `__GFP_THISNODE`: the first attempt in
  `___slab_alloc()` masks the flags to
  `GFP_NOWAIT | __GFP_NOMEMALLOC | __GFP_ACCOUNT` before `new_slab()`, so the
  bad bits are gone and no warning is printed if that attempt succeeds.
