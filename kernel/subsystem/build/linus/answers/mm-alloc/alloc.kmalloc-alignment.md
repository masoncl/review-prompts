- Non-power-of-two size: aligned to at least the largest power-of-two divisor
  of the size, not only to `ARCH_KMALLOC_MINALIGN` (96 gives 32, 192 gives 64).
- `create_boot_cache()`: one expression, `max(align, 1U << (ffs(size) - 1))`,
  applied only when `flags` has `SLAB_KMALLOC`. KMALLOC_MAX_ALIGN is not in
  this tree.
- `SLAB_KMALLOC`: among the callers of `create_boot_cache()` only
  `create_kmalloc_cache()` passes it, so the enforcement covers the
  `kmalloc_caches` rows.
- `kmem_buckets_create()` caches: made by `kmem_cache_create_usercopy()` with
  align 0 and without `SLAB_KMALLOC`; they never pass through
  `create_boot_cache()`, so `calculate_alignment()` gives them only
  `arch_slab_minalign()` rounded up to `sizeof(void *)`, unless the caller
  passes `SLAB_HWCACHE_ALIGN`.
- `new_kmalloc_cache()`: when `__kmalloc_minalign()` exceeds
  `ARCH_KMALLOC_MINALIGN`, it rounds the cache size up to a multiple of that
  value and points the smaller index at the larger cache.
