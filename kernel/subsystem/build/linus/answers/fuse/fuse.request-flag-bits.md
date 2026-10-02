- `FR_SYNC_WAKEUP`: `__fuse_request_send()` sets it;
  `fuse_dev_queue_req()` takes it with `test_and_clear_bit()` before
  `fiq->lock` and uses it to pick `wake_up_sync()`.
- `FR_URING`: set under `queue->lock` of `struct fuse_ring_queue` in
  `fuse_uring_queue_fuse_req()` and `fuse_uring_queue_bq_req()`; never
  cleared; `request_wait_answer()` tests it with no lock.
- `FR_ASYNC`: set by `fuse_args_to_req()` when `args->end` is set; it has
  nothing to do with io_uring.
- `FR_FORCE`: set by `fuse_chan_send()` only when `args->force` is set and
  `args->abort_on_kill` is not; its only test is in `request_wait_answer()`.
- `FR_BACKGROUND`: cleared by `fuse_request_bg_finish()`, which asserts
  `fch->bg_lock`.
- `FR_PENDING`: set in `fuse_request_init()`; set again only by
  `fuse_chan_resend()` under `fiq->lock`.
- `FR_PENDING` cleared under `fiq->lock`: by `fuse_dev_do_read()` and
  `fuse_chan_abort()`.
- `FR_PENDING` cleared with no lock: where the request is on no list, for
  example `fuse_dev_queue_req()` when `fiq->connected` is clear, and
  `virtio_fs_send_req()`.
- `fuse_remove_pending_req()`: tests `FR_PENDING` under the list lock and
  leaves it set.
- `FR_LOCKED`: `lock_request()` and `unlock_request()` change it under
  `req->waitq.lock`; `fuse_dev_do_write()` sets it and both device paths
  clear it under `fpq->lock`; `fuse_chan_abort()` tests it under both.
- `FR_LOCKED` on the read path: first set by `lock_request()` inside
  `fuse_copy_fill()`, so a request just added to `fpq->io` is not yet locked.
- `FR_SENT`: `fuse_dev_do_read()` sets it under `fpq->lock`;
  `fuse_dev_do_write()` and `fuse_chan_resend()` clear it under `fpq->lock`;
  `fuse_dev_end_requests()` clears it with no lock, on a private list.
- `FR_ABORTED` and `FR_PRIVATE`: set only in `fuse_chan_abort()`, only on
  requests found on `fpq->io`, under `fpq->lock` plus `req->waitq.lock`.
- `FR_PRIVATE`: set only if `FR_LOCKED` is clear; resend and release do not
  set it.
- `FR_PENDING` (initial), `FR_WAITING`, `FR_BACKGROUND`, `FR_FORCE`,
  `FR_ISREPLY`, `FR_ASYNC`: set with `__set_bit()`, not an atomic bitop,
  before the request is queued; `__clear_bit()` is used for `FR_ISREPLY`
  before queueing and for `FR_WAITING` at the last put.
