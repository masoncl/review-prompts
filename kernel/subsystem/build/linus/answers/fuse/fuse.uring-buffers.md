- Two ways: `FUSE_PAYLOAD_PER_ENT`, each entry registers its own payload
  buffer; `FUSE_PAYLOAD_BUFPOOL`, entries borrow from `struct fuse_bufpool` of
  the queue.
- `FUSE_PAYLOAD_UNSET`: state of a new queue; left once and never changed
  again.
- `FUSE_PAYLOAD_BUFPOOL`: set by `fuse_uring_add_bufpool()` under
  `queue->lock`, only from `FUSE_PAYLOAD_UNSET`, else `-EINVAL`.
- `FUSE_PAYLOAD_PER_ENT`: set by `fuse_uring_create_ring_ent()` at the first
  REGISTER that passes its payload tests on a queue that has no pool.
- `fuse_uring_add_bufpool()`: needs an existing queue, else `-EINVAL`;
  REGISTER creates a queue implicitly, `FUSE_IO_URING_CMD_ADD_QUEUE`
  explicitly.
- Pool layout: `nr_bufs` is `bufpool.len` divided by `ring->max_payload_sz`;
  buffer `id` starts at `base_uaddr + id * buf_size`.
- Registered pool: the ADD_BUFPOOL command had `IORING_URING_CMD_FIXED`;
  `registered_index` is its `buf_index`.
- Registered pool: `fuse_uring_import_payload()` uses
  `io_uring_cmd_import_fixed()` with `ent->cmd`, else `import_ubuf()`.
- REGISTER on a pool queue: the payload iovec must have NULL base and zero
  length, else `-EINVAL`; only the header iovec is used.
- Buffer taken: `fuse_uring_select_buffer()`, under `queue->lock`, when a
  request is assigned to the entry.
- Callers of `fuse_uring_select_buffer()`: `fuse_uring_prep_buffer()` on the
  send paths, `fuse_uring_next_req_update_buffer()` on the fetch path.
- Buffer taken only if `fuse_uring_req_has_copyable_payload()` is true; an
  entry without a buffer has `ent->payload.iov_base` NULL.
- No free buffer: `-ENOBUFS`; the request stays on `fuse_req_queue` and the
  entry stays available.
- Buffer kept: from assignment through `FRRS_USERSPACE` and the reply copy, and
  reused if the next request has a payload.
- Buffer given back: `fuse_uring_recycle_buffer()`, under `queue->lock`, when
  the fetch finds no request, when the next request has no payload, on the
  `-EIO` commit path and in cancelled task work.
- `fuse_uring_args_to_ring()`: tells the server the buffer through `offset` in
  `struct fuse_uring_ent_in_out`.
