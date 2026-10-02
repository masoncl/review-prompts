- `io_is_compat()`: tests `IO_RING_F_COMPAT` in `ctx->int_flags`; `struct
  io_ring_ctx` has no field named compat; `io_uring_create()` sets the bit.
- Message header: there is no io_compat_msg_copy_hdr() or
  io_sendmsg_copy_hdr(); `io_msg_copy_hdr()` in `io_uring/net.c` reads both
  layouts, called from `io_sendmsg_setup()` and `io_recvmsg_copy_hdr()`.
- Iovec for read/write: there is no io_compat_import() or
  io_iov_compat_buffer_select_prep(); see `io_import_vec()` and
  `io_iov_buffer_select_prep()` in `io_uring/rw.c`.
- `__import_iovec()` and `iovec_from_user()`: take the layout as an explicit
  `bool compat` argument; they do not call `in_compat_syscall()`.
- Negative compat iovec length: rejected with `-EINVAL` inside
  `copy_compat_iovec_from_user()` in `lib/iov_iter.c`; a handler that reads
  through `iovec_from_user()` or `__import_iovec()` needs no check of its own.
- Socket opcodes: prep also sets `MSG_CMSG_COMPAT` in the message flags on a
  compat ring; see `io_sendmsg_prep()` and `io_recvmsg_prep()`.
- `->uring_cmd()` handlers: `io_uring_cmd()` passes the ring state as
  `IO_URING_F_COMPAT` in `issue_flags`; `io_uring_cmd_getsockopt()` in
  `io_uring/cmd_net.c` hands it to `do_sock_getsockopt()`.
- Provided buffers in `io_uring/kbuf.c` and `io_get_ext_arg()` in
  `io_uring/io_uring.c`: no compat test; their structures have one layout.
- `io_epoll_ctl_prep()`: plain `copy_from_user()` of `struct epoll_event`, no
  compat branch.
- Register opcodes: none under `io_uring/` rejects a compat ring.
- **Potentially unsafe usage**: choosing the layout with `in_compat_syscall()`,
  directly or through a helper that hides it such as `import_iovec()`.
  - Unsafe: in a prep, issue or `->uring_cmd()` handler; `io_submit_sqes()` is
    also called from `__io_sq_thread()`, so the result describes the running
    thread, not the ring whose user wrote the structure.
  - Safe: pass `io_is_compat(req->ctx)` to `__import_iovec()` or
    `iovec_from_user()`, as `io_net_import_vec()` and `io_prep_reg_iovec()` do.
  - Safe: in code that runs only inside the caller's syscall and reads the
    caller's own argument, as `io_cqring_wait()` does for the signal mask and
    `io_register_iowq_aff()` for the CPU mask.
