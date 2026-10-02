- Signature: `void (*end)(struct fuse_args *args, int error)` in
  `fs/fuse/args.h`; no `struct fuse_mount` argument, so the callback takes it
  from its container, as `process_init_reply()` does.
- `may_block`: read only by `virtio_fs_requests_done_work()`; it does not
  decide whether `end` may sleep on any other transport.
- `may_block` setters: `fuse_async_req_send()` from `io->should_dirty`, and
  `fuse_file_put()` for the async release of a DAX inode.
- Lock state: call sites of `fuse_request_end()` drop their queue spinlock
  first; see `fuse_chan_abort()`, which calls `fuse_dev_end_requests()` after
  unlocking.
- Abort contexts: `fuse_chan_abort()` runs `end` with `-ECONNABORTED`, also
  from the `fuse_check_timeout()` worker.
- `fuse_simple_notify_reply()` returning 0: `end` may already have run in the
  caller's task with `-ENOTCONN`, from `fuse_dev_queue_req()`.
- `fuse_simple_background()`: `end` is not run in the caller's task;
  `fuse_send_writepage()` relies on it, calling under `fi->lock`, which
  `fuse_writepage_end()` takes.
- **Unsafe usage**: setting `end` on a request sent with
  `fuse_simple_request()`; `fuse_args_to_req()` sets `FR_ASYNC` whenever `end`
  is set, on the sync path too, and `fuse_request_end()` wakes the waiter
  before it calls `end`, so `args` can be gone.
  - Safe: leave `end` NULL and call the function after the send returns, as
    the sync branch of `fuse_file_put()` does with `fuse_release_end()`.
- **Potentially unsafe usage**: a `send_req` op of `struct fuse_iqueue_ops`
  calling `fuse_request_end()` on the request it was given.
  - Unsafe: for an `FR_BACKGROUND` request; `flush_bg_queue()` calls `send_req`
    under `bg_lock`, which `fuse_request_end()` takes, and the sender may hold
    a lock that `end` takes.
  - Safe: `virtio_fs_send_req()` puts a failed request on `fsvq->end_reqs`, and
    `virtio_fs_request_dispatch_work()` ends it.
  - Safe: `fuse_dev_queue_req()` ends a request only when `fiq->connected` is
    clear; `fuse_chan_abort()` clears `connected` of `struct fuse_chan` and
    empties `bg_queue` before it clears `fiq->connected`, so no background
    request reaches that branch.
  - Safe: `fuse_uring_queue_fuse_req()` ends a request only for a missing or
    stopped queue; `is_ring_ready()` requires every queue before `fiq->ops` is
    switched, and `queue->stopped` is set by `fuse_uring_abort()`, which
    `fuse_chan_abort()` calls after it emptied `bg_queue`, so no background
    request reaches those branches.
