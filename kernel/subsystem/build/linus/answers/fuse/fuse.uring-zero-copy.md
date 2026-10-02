- The path exists: the folios of a request are registered as an io_uring
  buffer of the server, at index `ent->zero_copy_index`.
- Queue: `queue->zero_copy` is set only by `FUSE_IO_URING_CMD_ADD_QUEUE` with
  `FUSE_URING_ZERO_COPY`, which needs `CAP_SYS_ADMIN`, else `-EPERM`.
- Queue: a zero-copy queue must use a buffer pool; REGISTER without one gets
  `-EINVAL` from `fuse_uring_create_ring_ent()`.
- `ent->zero_copy_index`: read from `ent_zero_copy_buf_index` at REGISTER;
  non-zero on a queue without zero copy gives `-EINVAL`.
- Request: `can_zero_copy_req()` needs `queue->zero_copy`, `args->zero_copy`,
  opcode `FUSE_READ` or `FUSE_WRITE`, and `in_pages` or `out_pages`.
- `args->zero_copy`: set in `fuse_read_args_fill()` and
  `fuse_write_args_fill()` from `FOPEN_IO_URING_ZERO_COPY` of the open file.
- `fuse_uring_set_up_zero_copy()`: takes one `folio_get()` per folio and calls
  `io_buffer_register_bvec()`; on failure the request ends with that error.
- Copy state: `skip_folio_copy` makes `fuse_copy_args()` skip the folio data;
  other arguments are still copied to the payload buffer.
- Zero-copied write: `payload_sz` sent to the server still includes the size
  of the page argument.
- Server notice: `FUSE_URING_ENT_ZERO_COPY` in `flags` of
  `struct fuse_uring_ent_in_out`.
- Unregister: `zero_copy_unregister()` calls `io_buffer_unregister()` from
  `fuse_uring_req_end()`, after `queue->lock` is dropped and before
  `fuse_request_end()`.
- Folio release: `fuse_zero_copy_release()` drops the extra references when
  io_uring drops the last reference on the buffer node (`io_free_rsrc_node()`,
  `io_buffer_unmap()`).
- `fs/fuse/dev_uring.c` drops only the references it took, in
  `fuse_zero_copy_release()`; the request's own folio references are not
  touched.
