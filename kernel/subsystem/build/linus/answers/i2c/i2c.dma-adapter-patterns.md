- `drivers/i2c/busses/i2c-rcar.c` and `drivers/i2c/busses/i2c-imx.c`: call
  neither helper; they are the flag-gated pattern below.
- **Unsafe usage**: mapping `msg->buf` for DMA when `I2C_M_DMA_SAFE` is clear.
  An unflagged buffer may be a stack array, as `msgbuf0` in
  `i2c_smbus_xfer_emulated()` is; `dma_map_single_attrs()` returns
  `DMA_MAPPING_ERROR` for a vmalloc address.
  - Safe: bounce through `i2c_get_dma_safe_msg_buf()`, map the returned
    pointer, use PIO on NULL, as `lpi2c_imx_dma_xfer()` with its caller
    `lpi2c_imx_xfer_common()` in `drivers/i2c/busses/i2c-imx-lpi2c.c` and
    `start_ch()` with `sh_mobile_i2c_xfer_dma()` in
    `drivers/i2c/busses/i2c-sh_mobile.c` do.
  - Safe: use DMA only when the flag is set and PIO otherwise, as
    `rcar_i2c_dma()` and `i2c_imx_xfer_common()` do; an unflagged message
    never gets DMA on these adapters.
  - Safe: copy into a driver-owned DMA buffer, as `tegra_i2c_xfer_msg()` does
    with `i2c_dev->dma_buf` from `dma_alloc_coherent()`.
