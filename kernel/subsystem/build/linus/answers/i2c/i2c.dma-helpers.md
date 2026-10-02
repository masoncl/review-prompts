- `i2c_put_dma_safe_msg_buf()`: calls only `memcpy()` and `kfree()`, nothing
  that sleeps; `stm32f7_i2c_dma_callback()` calls it from a dmaengine
  completion callback.
- `i2c_get_dma_safe_msg_buf()` on a zero-length message: returns NULL whatever
  the threshold, including a threshold of 0.
- `i2c_put_dma_safe_msg_buf()` reads `msg->buf`, `msg->len` and `msg->flags`
  at put time: `buf == msg->buf` is the only test for "not a bounce buffer",
  and the copy-back length is the current `msg->len`, not the length at get.
- NULL after the driver has already chosen DMA by length: means the allocation
  failed; `mxs_i2c_xfer_msg()` returns `-ENOMEM` there instead of using PIO.
