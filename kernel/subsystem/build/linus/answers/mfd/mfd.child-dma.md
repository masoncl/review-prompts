- `dma_mask`: assigned in `mfd_add_device()` as a shared pointer to the
  parent's storage.
- The three assignments (`dma_mask`, `dma_parms`, `coherent_dma_mask`) are
  unconditional and replace the defaults that `setup_pdev_dma_masks()` set in
  `platform_device_alloc()`.
- Parent with NULL `dma_mask` or `dma_parms`: the child gets NULL.
  - For example an I2C or SPI parent; `drivers/i2c/i2c-core-base.c` and
    `drivers/spi/spi.c` set neither.
  - `dma_set_mask()` on a child with NULL `dma_mask` returns `-EIO`.
  - `dma_set_max_seg_size()` on a child with NULL `dma_parms` hits
    `WARN_ON_ONCE()` and does nothing.
- Child with an OF node, at probe: `platform_dma_configure()` calls
  `of_dma_configure()`, the inline wrapper of `of_dma_configure_id()`, which
  narrows `*dev->dma_mask` in place, so it writes the parent's mask.
  - With a NULL `dma_mask` it warns "DMA mask not set" and points `dma_mask`
    at the child's own `coherent_dma_mask`.
