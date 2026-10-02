- **Potentially unsafe usage**: `dma_wmb()` as the only barrier between a
  store to coherent DMA memory and `writel_relaxed()`.
  - Unsafe: in a driver that can be built for an architecture whose `writel()`
    uses a stronger barrier than `dma_wmb()`. For example, on arm with
    `CONFIG_ARM_DMA_MEM_BUFFERABLE`, `__iowmb()` is `wmb()`, which is
    `__arm_heavy_mb(st)`, while `dma_wmb()` is `dmb(oshst)`.
  - Safe: in code built only for arm64, where `__io_bw()` in
    `arch/arm64/include/asm/io.h` is `dma_wmb()`, so `writel()` is that
    barrier and then the raw store; `__arm_smmu_cmdq_issue_cmdlist()` does
    this, and `ARM_SMMU_V3` depends on `ARM64`.
  - Safe: `wmb()` and then `writel_relaxed()`, as
    `ice_xdp_ring_update_tail()` does; `__io_bw()` in
    `include/asm-generic/io.h` defaults to `wmb()`, so this is what the
    generic `writel()` does.
  - Safe: plain `writel()` after the last store, as in the `dma_wmb()` example
    in `Documentation/memory-barriers.txt`; the generic `writel()` runs
    `__io_bw()` before the store.
- `rmb()` after `readl_relaxed()`: matches the generic `readl()`, whose
  `__io_ar()` defaults to `rmb()`; `hns_nic_rx_poll_one()` does this.
- `Documentation/memory-barriers.txt` descriptor example: does not mention
  `writel_relaxed()`; its note says only that the `dma_wmb()`, `dma_rmb()`
  and `dma_mb()` barriers give no ordering for MMIO.
- `__iowmb()`, `__iormb()`: defined only by some architectures, for example
  `arch/arm64/include/asm/io.h`, which marks them as not for portable
  drivers; there they are the barriers `writel()` and `readl()` use, so they
  do order MMIO against memory.
- A missing barrier does not show on every architecture: powerpc defines
  `writel_relaxed()` as `writel()` and `readl_relaxed()` as `readl()`, so a
  test there proves nothing about the relaxed forms.
