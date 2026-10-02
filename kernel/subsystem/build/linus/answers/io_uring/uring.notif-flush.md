- `io_notif_flush()` has two callers, `io_sendmsg_zc()` and
  `io_send_zc_cleanup()`, both in `io_uring/net.c`.
- `io_tx_ubuf_complete()` at the last reference: queues
  `io_notif_tw_complete()` with `__io_req_task_work_add()`, also when the
  flush itself drops the last reference with `ctx->uring_lock` held; a
  notification linked by `io_link_skb()` instead passes the drop to the chain
  head.
- `io_tx_ubuf_complete()`: never puts the notification on the completion list
  directly and does not call `io_req_complete_post()`.
- `IORING_NOTIF_USAGE_ZC_COPIED`: `io_notif_tw_complete()` ORs it into
  `notif->cqe.res`, not into the CQE flags.
- Lock requirement of `io_notif_flush()`: stated only by its
  `__must_hold(&notif->ctx->uring_lock)` annotation; neither it nor
  `io_tx_ubuf_complete()` has a `lockdep_assert_held()`.
- `io_notif_tw_complete()`: this is where `lockdep_assert_held()` on
  `ctx->uring_lock` is.
- Where the flush is done:

  | Case | Flush done in |
  |---|---|
  | issue returns `IOU_COMPLETE`, no `IO_URING_F_UNLOCKED` | `io_sendmsg_zc()` |
  | issue returns `IOU_COMPLETE` with `IO_URING_F_UNLOCKED` (io-wq) | `io_send_zc_cleanup()` |
  | issue returns `-ENOTSOCK`, `-EOPNOTSUPP` or an import error, in any context | `io_send_zc_cleanup()` |
  | issue returns `-EAGAIN` | nowhere yet; the notification is kept for the retry |
  | request fails or is cancelled before issue | `io_send_zc_cleanup()` |

- `io_send_zc_cleanup()`: reached only through `io_clean_op()`, which
  `io_free_batch_list()` calls with `ctx->uring_lock` held, and only while
  `REQ_F_NEED_CLEANUP` is set on the send request.
- io-wq order: after `io_sendmsg_zc()` returns, `io_req_complete_post()`
  posts the send CQE, or queues `io_req_task_complete()` on a ring with
  `IO_RING_F_LOCKLESS_CQ`; the cleanup flush runs later, when the request is
  freed, so the notification CQE cannot be queued ahead of the send CQE.
- `io_sendrecv_fail()`: writes only the send request's CQE; for the two
  zero-copy opcodes it sets `IORING_CQE_F_MORE` while `REQ_F_NEED_CLEANUP` is
  still set, and it copies `sr->done_io` into `cqe.res` if non-zero. It does
  not touch the notification.
- **Unsafe usage**: calling `io_req_msg_cleanup()` on a zero-copy send, without
  `IO_URING_F_UNLOCKED`, while `sr->notif` is still set.
  - Unsafe: `io_netmsg_recycle()` clears `REQ_F_NEED_CLEANUP` when it puts the
    header in `netmsg_cache`, so `io_clean_op()` never calls
    `io_send_zc_cleanup()` and the notification is never flushed.
  - Safe: flush, set `sr->notif = NULL`, then call `io_req_msg_cleanup()`, as
    `io_sendmsg_zc()` does.
