- `i2cdev_ioctl_rdwr()` in `drivers/i2c/i2c-dev.c`: ORs `I2C_M_DMA_SAFE` into
  every message after `memdup_user()`; it neither rejects nor clears a flag
  value that came from user space.
- `i2cdev_read()` and `i2cdev_write()`: pass heap buffers to
  `i2c_master_recv()` and `i2c_master_send()`, so those messages are unflagged.
- `dma_map_single_attrs()` in `include/linux/dma-mapping.h`: warns once and
  returns `DMA_MAPPING_ERROR` for a vmalloc address, with or without
  `CONFIG_DMA_API_DEBUG`; with `CONFIG_VMAP_STACK` that covers a stack buffer.
- `check_for_stack()` in `kernel/dma/debug.c`: reports a mapped stack buffer,
  built only with `CONFIG_DMA_API_DEBUG`.
