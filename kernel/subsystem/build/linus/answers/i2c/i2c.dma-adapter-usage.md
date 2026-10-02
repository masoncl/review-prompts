- Reference for the pairing: `lpi2c_imx_dma_xfer()` in
  `drivers/i2c/busses/i2c-imx-lpi2c.c`; every exit after a non-NULL get
  reaches one put, with `xferred` false on any error.
- Put after a NULL get: optional; `i2c_put_dma_safe_msg_buf()` returns at once
  for NULL.
- Atomic transfers: `start_ch()` in `drivers/i2c/busses/i2c-sh_mobile.c`
  returns before the get when `pd->atomic_xfer`; `lpi2c_imx_xfer_common()`
  takes the PIO branch when `atomic`.
- `pd->stop_after_dma` in `drivers/i2c/busses/i2c-sh_mobile.c`: set to true
  only by `sh_mobile_i2c_dma_callback()`, so the put copies back only when
  the DMA completed.
- **Unsafe usage**: calling `i2c_put_dma_safe_msg_buf()` while the bounce
  buffer is still mapped or the DMA engine may still access it; the put frees
  it with `kfree()`.
  - Safe: terminate and unmap first on failure, unmap first on success, then
    put, as `lpi2c_imx_dma_xfer()` does through `lpi2c_cleanup_dma()` and
    `lpi2c_dma_unmap()`.
- **Unsafe usage**: getting a bounce buffer for an unflagged `I2C_M_RECV_LEN`
  read and then growing `msg->len`; the get allocated the old `msg->len`
  bytes, and the put copies the new `msg->len` bytes out of it.
  - Safe: no DMA for such a message, as `is_use_dma()` in
    `drivers/i2c/busses/i2c-imx-lpi2c.c` returns false on `I2C_M_RECV_LEN`.
