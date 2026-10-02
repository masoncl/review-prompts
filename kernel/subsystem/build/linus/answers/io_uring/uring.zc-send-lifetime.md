- There is no io_send_zc() and no io_sendmsg_zc_prep() in this tree.
- `io_sendmsg_zc()` in `io_uring/net.c`: the issue function for both
  `IORING_OP_SEND_ZC` and `IORING_OP_SENDMSG_ZC`; see `io_issue_defs[]` in
  `io_uring/opdef.c`.
- `io_sendmsg_zc()` tells the two opcodes apart by `req->opcode`:
  `sock_sendmsg()` for `IORING_OP_SEND_ZC`, `__sys_sendmsg_sock()` otherwise.
- `io_send_zc_prep()`: the prep function for both opcodes; it also branches on
  `req->opcode`, to `io_send_setup()` or `io_sendmsg_setup()`.
- `io_send_zc_import()`: the one place that imports a registered buffer for a
  zero-copy send, with `sr->notif` as owner, through `io_import_reg_buf()` or
  `io_import_reg_vec()`.
- `io_send_zc_import()` runs at issue, from `io_sendmsg_zc()`, only while
  `REQ_F_IMPORT_BUFFER` is set on the send request; it clears the flag on
  success, so a retry does not import again.
- `notif->buf_index`: `io_send_zc_import()` copies it from `req->buf_index`
  before the import, because `io_find_buf_node()` looks up `buf_index` of the
  request it is passed and stores the node in that request's `buf_node`.
- Notification `user_data`: `sqe->addr3` when it is non-zero, otherwise the
  send request's `user_data`; see `io_send_zc_prep()`.
- `io_alloc_notif()` call in `io_send_zc_prep()`: comes after the
  `sqe->__pad2[0]` and `REQ_F_CQE_SKIP` checks, and before the flags are read.
- Prep failure before the allocation: no notification exists and
  `REQ_F_NEED_CLEANUP` is not set.
- Prep failure after the allocation (for example a flag outside
  `IO_ZC_FLAGS_VALID`, or a failed `io_msg_alloc_async()`):
  `REQ_F_NEED_CLEANUP` is already set, so `io_clean_op()` calls
  `io_send_zc_cleanup()`, and a notification CQE is still posted.
- Flag validation in `io_send_zc_prep()`: the only test that rejects is
  against `IO_ZC_FLAGS_VALID`; no combination of valid flags is rejected
  there.
