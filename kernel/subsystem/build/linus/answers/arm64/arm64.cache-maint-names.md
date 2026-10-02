- `dcache_clean_poc_nosync()` and `dcache_inval_poc_nosync()`: defined in
  `arch/arm64/mm/cache.S`, missing from the comment in
  `arch/arm64/include/asm/cacheflush.h`; they issue the same operations to
  PoC as the forms without the suffix, without the closing `dsb sy`.
- `arch_sync_dma_for_device()`: calls `dcache_clean_poc_nosync()`, not
  `dcache_clean_poc()`.
- `arch_sync_dma_for_cpu()`: calls `dcache_inval_poc_nosync()`, not
  `dcache_inval_poc()`.
- `arch_sync_dma_flush()` in `arch/arm64/include/asm/cache.h`: the `dsb(sy)`
  that completes them; the DMA core calls it after the sync, for example
  `dma_direct_sync_single_for_device()` in `kernel/dma/direct.h`.
- `CONFIG_ARCH_HAS_BATCHED_DMA_SYNC`: selected by `arch/arm64/Kconfig`;
  without it `arch_sync_dma_flush()` is the empty stub in
  `include/linux/dma-map-ops.h`.
- **Potentially unsafe usage**: calling `dcache_clean_poc_nosync()` or
  `dcache_inval_poc_nosync()`.
  - Unsafe: when no `dsb(sy)` follows before the device or the CPU touches
    the buffer; the maintenance may not have completed.
  - Safe: when `arch_sync_dma_flush()` follows, as
    `dma_direct_sync_single_for_device()` issues it after
    `arch_sync_dma_for_device()`; elsewhere use `dcache_clean_poc()` or
    `dcache_inval_poc()`, which end in `dsb sy`.
- `arch_dma_prep_coherent()`: uses `dcache_clean_poc()`, a clean only, not
  `dcache_clean_inval_poc()`.
- Persistent memory: there is no invalidate-to-PoP routine;
  `arch_invalidate_pmem()` in `arch/arm64/mm/flush.c` uses
  `dcache_inval_poc()`.
