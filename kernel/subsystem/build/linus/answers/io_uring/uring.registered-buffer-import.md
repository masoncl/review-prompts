- Request passed in: need not be the request being issued;
  `io_send_zc_import()` in `io_uring/net.c` passes `sr->notif` to
  `io_import_reg_buf()` and to `io_import_reg_vec()`.
- **Potentially unsafe usage**: passing the issuing request as `req`.
  - Unsafe: when the pages can still be in use after that request is freed;
    `io_req_put_rsrc_nodes()` then drops the node and the last put runs
    `io_buffer_unmap()`.
  - Safe: when the request is freed only after the I/O on the iterator has
    ended, as in `io_init_rw_fixed()` in `io_uring/rw.c`.
  - Safe: pass a request that lives as long as the pages are used, as
    `io_send_zc_import()` does with the notif.
- **Unsafe usage**: importing on a request whose prep did not store
  `req->buf_index`; `io_init_req()` writes it only for
  `IOSQE_BUFFER_SELECT`, and requests are recycled.
  - Safe: prep reads `sqe->buf_index` under the same flag that later
    triggers the import, as `io_sendmsg_prep()` does for
    `IORING_RECVSEND_FIXED_BUF`.
  - Safe: `io_uring_cmd_import_fixed()` and
    `io_uring_cmd_import_fixed_vec()` return `-EINVAL` when the command lacks
    `IORING_URING_CMD_FIXED`, the flag under which `io_uring_cmd_prep()`
    stores the index.
  - Safe: copy the index to the request that is passed, as
    `io_send_zc_import()` does with `notif->buf_index`.
- **Unsafe usage**: importing on a request that also selects a provided
  buffer; `buf_node` and `kbuf` are one union in `struct io_kiocb`, and
  `req->buf_index` doubles as the buffer group or buffer id.
  - Safe: prep rejects the combination with `REQ_F_BUFFER_SELECT`, as
    `io_sendmsg_prep()` and `io_recvmsg_prep()` do.
  - Safe: `io_uring_cmd_prep()` allows `REQ_F_BUFFER_SELECT` only with
    `IORING_URING_CMD_MULTISHOT`, which it rejects together with
    `IORING_URING_CMD_FIXED`.
- `io_find_buf_node()` with `REQ_F_BUF_NODE` already set: returns
  `req->buf_node` with no lock, lookup or new reference; a changed
  `req->buf_index` is ignored.
- **Potentially unsafe usage**: passing to `io_import_reg_vec()` a request
  other than the one whose async data holds `vec`; on reallocation the
  function sets `REQ_F_NEED_CLEANUP` on the request passed in.
  - Unsafe: when the owner of `vec` does not already have
    `REQ_F_NEED_CLEANUP`; `io_clean_op()` calls the opcode's `cleanup` only
    under that flag.
  - Safe: the owner sets the flag in prep, as `io_send_zc_prep()` does.
- Direction constants: there is no IO_IMU_DEST or IO_IMU_SOURCE; the bits in
  `imu->dir` are `IO_BUF_DEST` and `IO_BUF_SOURCE` in
  `include/linux/io_uring_types.h`.
- Kernel buffer direction: `io_buffer_register_request()` stores one bit,
  `1 << rq_data_dir(rq)`; `io_buffer_register_bvec()` stores the caller's
  mask, which may hold both bits.
- `io_import_reg_vec()`: tests the direction once, before it looks at any
  iovec.
- Per-segment range in `io_import_reg_vec()`: `validate_fixed_range()` runs in
  `io_vec_fill_bvec()` for a user buffer and in `iov_kern_bvec_size()` for a
  kernel buffer.
- `io_vec_fill_kern_bvec()`: has no range check of its own; it relies on
  `io_kern_bvec_size()` having run first.
- `validate_fixed_range()`: also returns `-EFAULT` when `len` is above
  `MAX_RW_COUNT`, for the single buffer and for each iovec.
- Kernel buffer addresses: `imu->ubuf` is 0, so `buf_addr` and `iov_base` are
  byte offsets into the buffer, not user addresses.
- Zero length: `io_import_reg_buf()` accepts `len == 0` after the range and
  direction checks and returns an empty iterator; `io_import_reg_vec()`
  rejects a zero-length iovec with `-EFAULT`.
- Summed length in `io_import_reg_vec()`: overflow gives `-EOVERFLOW`; a total
  above `MAX_RW_COUNT` gives `-EINVAL`.
