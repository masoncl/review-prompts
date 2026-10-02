- Finish: `io_req_set_res()` then `IOU_COMPLETE`; a positive return is not a
  completion, `io_poll_check_events()` carries on as for `IOU_RETRY`.
- Run again, three forms:

  | Form | Effect | Used by |
  |---|---|---|
  | loop inside the handler | no return to the core | `io_recv_finish()` returning false, `io_accept()` |
  | `io_poll_multishot_retry()` then `IOU_RETRY` | `io_poll_check_events()` loops, calls `vfs_poll()`, reissues only if it reports events | `io_read_mshot()` |
  | `IOU_REQUEUE` | new task_work through `__io_poll_execute()`, ownership kept | `io_recv_finish()`, `io_zcrx_tcp_recvmsg()` |

- After a posted CQE with input possibly left, under `IO_URING_F_MULTISHOT`:
  a plain `IOU_RETRY` waits for a new wakeup that may never come; the handler
  must use one of the three forms.
- `io_read_mshot()`: calls `io_poll_multishot_retry()` only under
  `IO_URING_F_MULTISHOT`, and returns `IOU_RETRY` either way.
- Final CQE after `IOU_COMPLETE`: `__io_submit_flush_completions()` falls
  back to `io_cqe_overflow()` or `io_cqe_overflow_locked()`, so finishing is
  what keeps the result.
- **Potentially unsafe usage**: `IOU_RETRY` after `io_req_post_cqe()` or
  `io_req_post_cqe32()` returned false.
  - Unsafe: when the result is already consumed, such as a buffer committed
    by `io_put_kbuf()` or an installed fd; nothing posts it later.
  - Safe: `io_uring_cmd_timestamp()` splices the unposted skbs back onto
    `sk_error_queue` before it returns `-EAGAIN`.
- File would block: the handler posts nothing, calls `io_kbuf_recycle()` and
  returns `IOU_RETRY`, as `io_recv()` and `io_read_mshot()` do; they do not
  arm poll themselves.
- `io_read_mshot()` on an unpollable file: `-EBADFD`, before any read.
