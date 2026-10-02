- Detection: all three test `issue_flags & IO_URING_F_UNLOCKED`; none tests
  `IO_URING_F_IOWQ` or `PF_IO_WORKER`.
- `IO_URING_F_UNLOCKED` also comes from non-worker callers, for example the
  `io_uring_cmd_done()` call in `fuse_uring_entry_teardown()` in
  `fs/fuse/dev_uring.c`.

| Function | With `IO_URING_F_UNLOCKED` | Left on the request |
|---|---|---|
| `io_netmsg_recycle()` | frees the iovec, returns | `async_data`, `REQ_F_ASYNC_DATA` and `REQ_F_NEED_CLEANUP` unchanged |
| `io_rw_recycle()` | returns false, frees nothing | everything |
| `io_req_uring_cleanup()` | returns at once | everything |

- There is no io_rw_iovec_free() here; `io_req_rw_cleanup()` calls
  `io_vec_free()` when `io_rw_recycle()` returns false, including cache-full.
- rw in io-wq: `io_req_rw_cleanup()` does nothing while `REQ_F_REFCOUNT` or
  `REQ_F_REISSUE` is set, and `io_wq_submit_work()` always sets
  `REQ_F_REFCOUNT`; this also holds for the later task-work completion.
- What is left is released by `io_clean_op()`:

| Opcode | Cleanup handler, if `REQ_F_NEED_CLEANUP` | `async_data` ends |
|---|---|---|
| rw | `io_readv_writev_cleanup()`: frees iovec, then recycles | in `rw_cache` |
| net | `io_sendmsg_recvmsg_cleanup()`: frees iovec only | `kfree()`d |
| uring_cmd | `io_uring_cmd_cleanup()`: recycles with the vec | in `cmd_cache` |

- Without `REQ_F_NEED_CLEANUP` (no iovec was allocated): no handler runs and
  `io_clean_op()` `kfree()`s `async_data`.
- Cache full in the table above: `io_clean_op()` `kfree()`s `async_data`.
- `io_sendmsg_zc()` with `IO_URING_F_UNLOCKED`: skips the recycle call
  entirely and leaves the notif flush to `io_send_zc_cleanup()`; there is no
  io_send_zc() here.
