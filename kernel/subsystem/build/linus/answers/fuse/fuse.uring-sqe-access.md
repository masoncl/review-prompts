- `io_uring_sqe128_cmd()`: macro in `include/linux/io_uring/cmd.h`; returns
  `sqe->cmd` cast to the type, with a `BUILD_BUG_ON()` against the command area
  of a 128-byte SQE.
- Every read of the command area in `fs/fuse/dev_uring.c` goes through
  `io_uring_sqe128_cmd()`; none uses `io_uring_sqe_cmd()`.
- `io_uring_cmd_prep()`: stores the pointer into the submission ring
  (`ioucmd->sqe = sqe`); it copies only `cmd_op`, `uring_cmd_flags` and, with
  `IORING_URING_CMD_FIXED`, `buf_index`.
- `io_uring_cmd_sqe_copy()` in `io_uring/uring_cmd.c`: copies the entry and
  repoints `ioucmd->sqe`; called through `io_req_sqe_copy()` in
  `io_uring/io_uring.c` on `-EAGAIN`, on the fallback path and for links.
- Inline issue that returns `-EIOCBQUEUED`: no copy is made, `cmd->sqe` keeps
  pointing at the ring slot.
- `io_req_uring_cleanup()`: can set `ioucmd->sqe` to NULL at completion; not
  with `IO_URING_F_UNLOCKED`.
- **Unsafe usage**: reading `cmd->sqe` after the issue call returned, from task
  work, cancel or teardown.
  - Safe: read inside the call chain of `fuse_uring_cmd()`, as
    `fuse_uring_cmd_index_ok()` does; store what is needed later in
    `struct fuse_ring_ent`.
  - Safe: `cmd->cmd_op` and `cmd->flags` at any time; `io_uring_cmd_prep()`
    copied them.
  - Safe: `io_uring_cmd_import_fixed()` in task work; it uses `req->buf_index`
    copied at prep.
- **Unsafe usage**: reading one SQE field twice, to check and then to use.
  - Safe: one `READ_ONCE()` into a local, as `fuse_uring_commit_fetch()` does;
    `io_get_sqe()` hands out `ctx->sq_sqes`, shared with userspace.
- **Unsafe usage**: reading through the pointer from `io_uring_sqe128_cmd()`
  when `IO_URING_F_SQE128` was not tested.
  - Safe: after the test in `fuse_uring_cmd()`; `struct fuse_uring_cmd_req` is
    larger than the command area of a 64-byte entry.
  - Safe: the cancel call runs before that test and reads only the pdu.
