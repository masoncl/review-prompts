- In-tree clients, for example: `ad5110_read()` in
  `drivers/iio/potentiometer/ad5110.c` uses both `i2c_master_send_dmasafe()`
  and `i2c_master_recv_dmasafe()`; `st1232_ts_read_data()` in
  `drivers/input/touchscreen/st1232.c` sets `I2C_M_DMA_SAFE` by hand.
- `ARCH_DMA_MINALIGN` is what defines the alignment needed for DMA of a
  buffer embedded in a struct; `____cacheline_aligned` aligns to
  `SMP_CACHE_BYTES`, which on arm64 is 64 against an `ARCH_DMA_MINALIGN` of
  128.
- **Unsafe usage**: flagging a buffer that is on the stack, in vmalloc memory,
  or shares an `ARCH_DMA_MINALIGN` block with other data. `rcar_i2c_dma()` and
  `i2c_imx_dma_xfer()` then pass `msg->buf` to `dma_map_single()`, and
  `i2c_get_dma_safe_msg_buf()` returns `msg->buf` itself, with no copy.
  - Safe: a separate heap allocation, as `ts->read_buf` from `devm_kzalloc()`
    in `drivers/input/touchscreen/st1232.c`; `struct devres` aligns `data[]`
    to `ARCH_DMA_MINALIGN`.
  - Safe: a member with `__aligned(IIO_DMA_MINALIGN)` placed last in the
    `iio_priv()` struct, as `buf` in `struct ad5110_data`;
    `iio_device_alloc()` aligns the private area to `IIO_DMA_MINALIGN`, and
    `IIO_DMA_MINALIGN` in `include/linux/iio/iio.h` is at least
    `ARCH_DMA_MINALIGN`.
  - Safe: leaving the flag off the message whose buffer does not qualify, as
    `st1232_ts_read_data()` does for the on-stack `reg` in its first message.
