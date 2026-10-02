| Constant | Default when the arch does not define it | Where |
|---|---|---|
| `ARCH_DMA_MINALIGN` | `__alignof__(unsigned long long)` | `include/linux/cache.h` |
| `ARCH_KMALLOC_MINALIGN` | `ARCH_DMA_MINALIGN` if `ARCH_HAS_DMA_MINALIGN` and the value is above 8, else `__alignof__(unsigned long long)` | `include/linux/slab.h` |
| `ARCH_SLAB_MINALIGN` | `__alignof__(unsigned long long)` | `include/linux/slab.h` |

- `ARCH_HAS_DMA_MINALIGN`: defined by `include/linux/cache.h` only when the
  arch supplied `ARCH_DMA_MINALIGN`.
- `dma_get_cache_alignment()` default: `ARCH_DMA_MINALIGN` with
  `ARCH_HAS_DMA_MINALIGN`, otherwise 1.
- Configurations where `ARCH_KMALLOC_MINALIGN` is smaller: arm64 (8 vs 128),
  riscv with `CONFIG_RISCV_DMA_NONCOHERENT` (8 vs `L1_CACHE_BYTES`), parisc
  (16 vs 32 or 128).
- `CONFIG_DMA_BOUNCE_UNALIGNED_KMALLOC`: selected by arm64; by riscv only
  `if SWIOTLB`; not by parisc.
- `__kmalloc_minalign()` in `mm/slab_common.c`: decides the cache minimum;
  there is no kmalloc_minalign() without the underscores.
- `__kmalloc_minalign()`: returns `max(minalign, arch_slab_minalign())` on
  both paths; `ARCH_KMALLOC_MINALIGN` is not a second floor there.
- Without the bounce option, or when `is_swiotlb_allocated()` is false: every
  kmalloc cache is at least `dma_get_cache_alignment()` aligned, and no
  `kmalloc()` buffer is bounced for alignment.
- `new_kmalloc_cache()`: when the minimum exceeds `ARCH_KMALLOC_MINALIGN`,
  aliases a small size class to the cache of the rounded-up size, for every
  cache type.
- `dma_kmalloc_needs_bounce()`: receives the device, the mapped length and
  the direction; it sees neither the address nor the enclosing object.
- `dma_kmalloc_size_aligned()`: passes any length of
  `2 * ARCH_DMA_MINALIGN` or more without a look at `kmalloc_size_roundup()`.
- `kernel/dma/direct.c`: when a bounce is needed and `is_swiotlb_active()` is
  false or `DMA_ATTR_REQUIRE_COHERENT` is set, the map returns
  `DMA_MAPPING_ERROR`.
- `ARCH_KMALLOC_MINALIGN`: not a DMA-safe alignment on these configurations;
  `ARCH_DMA_MINALIGN` is the build-time value, `dma_get_cache_alignment()`
  the run-time one.
- `____cacheline_aligned`: is `SMP_CACHE_BYTES` (`include/vdso/cache.h`);
  arm64 has `L1_CACHE_BYTES` 64 and `ARCH_DMA_MINALIGN` 128, so it does not
  isolate a DMA member there.
- `__dma_from_device_group_begin()` and `__dma_from_device_group_end()`:
  defined in `include/linux/dma-mapping.h`; they add
  `__aligned(ARCH_DMA_MINALIGN)` only under `ARCH_HAS_DMA_MINALIGN`.
- **Potentially unsafe usage**: mapping a member of a `kmalloc()`ed struct
  for `DMA_FROM_DEVICE` or `DMA_BIDIRECTIONAL`.
  - Unsafe: on a non-coherent device when the member shares
    `ARCH_DMA_MINALIGN` bytes with a field the CPU writes; the length test in
    `dma_kmalloc_needs_bounce()` cannot detect it.
  - Unsafe: when the member is aligned but the allocation size is not a
    multiple of `ARCH_DMA_MINALIGN` (for example a trailing flexible array);
    on arm64 when `__kmalloc_minalign()` took the bounce path, 136 bytes
    lands in the 192-byte cache, which `create_boot_cache()` aligns to 64.
  - Safe: member between `__dma_from_device_group_begin()` and
    `__dma_from_device_group_end()` in a struct allocated at exactly its
    `sizeof`, as `probe_common()` does for `struct virtrng_info` in
    `drivers/char/hw_random/virtio-rng.c`; the size rule in
    `create_boot_cache()` then aligns the base.
  - Safe: `DMA_TO_DEVICE`, or a coherent device; `dma_kmalloc_safe()` defines
    both.
