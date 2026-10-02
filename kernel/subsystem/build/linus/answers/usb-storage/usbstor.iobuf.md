- `us->iobuf`: allocated with `usb_alloc_coherent()` in `associate_dev()`, not
  `kmalloc()`; the DMA address is in `us->iobuf_dma`.
- `usb_stor_msg_common()`: sets `URB_NO_TRANSFER_DMA_MAP` only when
  `transfer_buffer == us->iobuf` (pointer equality); a pointer into the middle
  of `us->iobuf` is mapped by `usb_hcd_map_urb_for_dma()` like any other
  buffer.
- `usb_stor_msg_common()`: assigns `transfer_dma = us->iobuf_dma` for every
  transfer; only the flag is conditional.
- `usb_stor_CB_transport()`: copies `srb->cmnd` into `us->iobuf` with
  `memcpy()` and sends `us->iobuf`; it does not pass `srb->cmnd`.
- Stack command blocks in sub-drivers: for example `rts51x_read_mem()` keeps
  `cmnd[12]` on the stack and `rts51x_bulk_transport()` copies it into
  `bcb->CDB` inside `us->iobuf`.
- **Unsafe usage**: passing a buffer on the stack to
  `usb_stor_bulk_transfer_buf()`, `usb_stor_ctrl_transfer()` or
  `usb_stor_control_msg()`.
  - Unsafe: on a host controller that maps with DMA (`hcd_uses_dma()`, no
    `localmem_pool`), `usb_hcd_map_urb_for_dma()` in
    `drivers/usb/core/hcd.c` hits `WARN_ONCE()` and fails the submit with
    `-EAGAIN`; the first two helpers then return `USB_STOR_XFER_ERROR`, the
    third returns `-EAGAIN`.
  - Safe: build the bytes in `us->iobuf`, as `sddr09_request_sense()` does for
    its command.
  - Safe: a `kmalloc()` buffer, as `rts51x_read_mem()` uses for its data.
