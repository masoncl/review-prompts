- There is no io_req_assign_rsrc_node() in this tree: `io_file_get_fixed()` in
  `io_uring/io_uring.c` and `io_find_buf_node()` in `io_uring/rsrc.c` do
  `node->refs++` themselves, inside `io_ring_submit_lock()`.
- `io_rsrc_node_lookup()` in `io_uring/rsrc.h`: bounds check only, takes no
  reference and asserts no lock.
- `io_file_get_fixed()`: does not set `REQ_F_FIXED_FILE`; the flag is set
  before the call, by the SQE flags copied in `io_init_req()` or by the
  opcode, as `io_nop_prep()` does. It ORs in `io_slot_flags()`.
- `io_req_put_rsrc_nodes()`: has one caller, `io_free_batch_list()`.
  `io_clean_op()` touches neither `req->file_node` nor `req->buf_node`.
- Splice and tee with `SPLICE_F_FD_IN_FIXED`: `io_splice_get_file()` in
  `io_uring/splice.c` takes its own reference on the input file's node,
  stores it in `rsrc_node` of `struct io_splice` and sets
  `REQ_F_NEED_CLEANUP`.
- `io_splice_cleanup()`: puts that reference; it is reached through
  `io_clean_op()` from `io_free_batch_list()`, so under `uring_lock`.
- Fixed-file lookup without a node reference: `io_msg_grab_file()` in
  `io_uring/msg_ring.c` takes `get_file()` on the file before it unlocks,
  and leaves `node->refs` alone.
- `io_clone_buffers()`: does `node->refs++` for each destination node it
  carries into the new table; the old table's reference goes in
  `io_rsrc_data_free()`.
- `io_clone_buffers()`: a cloned source buffer gets a new node from
  `io_rsrc_node_alloc()` in the destination ring; the node is not shared
  between rings, only its `struct io_mapped_ubuf` is.
- `io_free_rsrc_node()`: when `node->tag` is non-zero it first posts a CQE
  with `io_post_aux_cqe(ctx, node->tag, 0, 0)`, then releases by type.
- Failed registration: `io_sqe_files_register()` and
  `io_sqe_buffers_register()` call `io_clear_table_tags()` before they free
  the table, so no tag CQE is posted for those nodes.
