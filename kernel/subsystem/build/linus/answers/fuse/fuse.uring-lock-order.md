- Order, outer to inner: `fi->lock`, `queue->lock`, `fch->bg_lock`.
- `fi->lock` outside `queue->lock`: `fuse_send_writepage()` runs under
  `fi->lock` and reaches `fuse_uring_queue_bq_req()` through
  `fuse_simple_background()`.
- `fch->lock`: outer to `fch->bg_lock` in `fuse_chan_abort()`; no function in
  `fs/fuse/dev_uring.c` takes it or `queue->lock` while it has taken the other.
- `fuse_uring_do_register()`: drops `fch->lock` before
  `fuse_uring_prepare_cancel()` and before it takes `queue->lock`.
- `fuse_chan_abort()` and `fuse_check_timeout()`: drop `fch->lock` before
  `fuse_uring_abort()` and `fuse_uring_request_expired()`.
- `fuse_request_end()` called from `fuse_uring_req_end()`: takes no
  `fch->bg_lock`, because `FR_BACKGROUND` is already clear.
- `fuse_request_end()` from `fuse_dev_end_requests()` or
  `fuse_uring_stop_fuse_req_end()`: still takes `fch->bg_lock` for a request
  with `FR_BACKGROUND` set.
- `ctx->uring_lock`, a mutex: `io_uring_cmd_mark_cancelable()`,
  `io_buffer_unregister()` and `io_uring_cmd_done()` may take it, so they run
  after `queue->lock` is dropped.
- `queue->stopped`: written under `queue->lock` in
  `fuse_uring_abort_end_requests()`.
