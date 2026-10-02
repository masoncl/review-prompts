- First wait, `wait_event_interruptible()`: a signal never makes the task
  return; it sets `FR_INTERRUPTED` and the task goes on to the next wait.
- `queue_interrupt()` after the first wait: called only if `FR_SENT` is
  already set; otherwise `fuse_dev_do_read()` queues the interrupt.
- Second wait: `wait_event_killable()`; skipped only when `FR_FORCE` is set.
- `args->abort_on_kill`: on a fatal signal the task calls
  `fuse_chan_abort()` on the whole channel, then waits uninterruptibly.
- `args->abort_on_kill` with `args->force`: `fuse_chan_send()` leaves
  `FR_FORCE` clear, so the killable wait still runs; `fuse_send_init()` sets
  this for a synchronous INIT.
- Killed while pending: `fuse_remove_pending_req()` takes `fiq->lock`, or
  for `FR_URING` the `queue->lock` of `req->ring_queue`.
- Killed-pending request: never passes through `fuse_request_end()`;
  `FR_FINISHED` stays clear, `FR_PENDING` stays set, error is -EINTR.
- Return with no server reply, request ended by the kernel, on `/dev/fuse`:

| Case | Where | Error |
|---|---|---|
| `fiq->connected` clear at queue time | `fuse_dev_queue_req()` | -ENOTCONN |
| read buffer smaller than the request | `fuse_dev_do_read()` | -EIO; -E2BIG for `FUSE_SETXATTR` |
| `fpq->connected` clear at read | `fuse_dev_do_read()` | -ECONNABORTED |
| copy to the server fails | `fuse_dev_do_read()` | -EIO |
| `FR_ISREPLY` clear (`args->noreply`) | `fuse_dev_do_read()`, after the copy | 0 |
| abort, or release of the device | `fuse_dev_end_requests()` | -ECONNABORTED |
