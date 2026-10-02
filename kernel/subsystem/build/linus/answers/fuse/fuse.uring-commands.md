- Checks before dispatch, in order: `IO_URING_F_CANCEL`; `IO_URING_F_SQE128`
  missing gives `-EINVAL`; `fuse_get_dev()` error; `fch->initialized` 0 gives
  `-EAGAIN`; `fch->abort_with_err` gives `-ECONNABORTED`; `fch->connected` 0
  gives `-ENOTCONN`; `fch->io_uring` 0 gives `-EOPNOTSUPP`.

| Input | Return of `fuse_uring_cmd()` |
|---|---|
| `IO_URING_F_CANCEL` | 0 |
| `FUSE_IO_URING_CMD_REGISTER` | `-EIOCBQUEUED`, or errno |
| `FUSE_IO_URING_CMD_COMMIT_AND_FETCH` | `-EIOCBQUEUED`, or errno |
| `FUSE_IO_URING_CMD_ADD_QUEUE` | 0 or errno; command is never held |
| `FUSE_IO_URING_CMD_ADD_BUFPOOL` | 0 or errno; command is never held |
| any other `cmd_op` | `-EINVAL` |

- `FUSE_IO_URING_CMD_COMMIT_AND_FETCH`: returns `-EIOCBQUEUED` also when
  `fuse_uring_send()` has already completed the command inline.
- Failed `FUSE_IO_URING_CMD_REGISTER`: clears `fch->io_uring` and wakes
  `fch->blocked_waitq`; a failure of the other three commands does not.
- `FUSE_IO_URING_CMD_REGISTER` that finds `fch->connected` clear in
  `fuse_uring_do_register()`: the new entry is freed and the return is
  `-ECONNABORTED`.
- `-EACCES`: not returned by `fs/fuse/dev_uring.c`; `fuse_uring_add_queue()`
  returns `-EPERM` for `FUSE_URING_ZERO_COPY` without `CAP_SYS_ADMIN`.
- CQE of a held command: 0 after a request was copied, `-ENOTCONN` from cancel
  or teardown, `-ECANCELED` from cancelled task work; a copy error is never
  posted.
- Copy failure in `fuse_uring_send_in_task()`: the request is ended, the next
  one is tried, and with none waiting the command stays held.
- Notify replies: `fuse_chan_send_notify_reply()` calls `fuse_send_one()`, so
  they go through the ring once `fiq->ops` is `fuse_io_uring_ops`.
- Still read or written on the device: forgets and interrupts
  (`fuse_io_uring_ops`), `FUSE_INIT`, `force` requests sent before ready, and
  notifications written by the server.
