- Sizes that are not a power of two: the documented guarantee is the largest
  power-of-two divisor of the requested size.
- `create_boot_cache()` in `mm/slab_common.c`: computes
  `1U << (ffs(size) - 1)` from the cache size, so the alignment an object
  gets is that of its cache, never less than the documented value.
- `create_kmalloc_cache()`: adds `SLAB_KMALLOC` to the flags and computes no
  alignment; the raise is in `create_boot_cache()`, under that flag.
- `calculate_alignment()`: also raises every cache to `arch_slab_minalign()`
  and rounds up to `sizeof(void *)`.
- Documentation: the kernel-doc of `kmalloc()` in `include/linux/slab.h`
  states the same three guarantees as
  `Documentation/core-api/memory-allocation.rst`.
- `kmem_buckets_create()` with `CONFIG_SLAB_BUCKETS`: creates its caches with
  `kmem_cache_create_usercopy()`, align 0 and no `SLAB_KMALLOC`, so the
  size-based raise is not applied to them; their floor is what
  `calculate_alignment()` gives.
