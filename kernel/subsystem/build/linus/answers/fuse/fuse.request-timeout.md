- Timeout: exists; the code is in `fs/fuse/req_timeout.c`, the state is
  `fch->timeout.req_timeout` and `fch->timeout.work` in `struct fuse_chan`.
- `fuse_init_server_timeout()`: called only from `process_init_reply()`,
  for a reply with no error and a matching major, so no limit runs before
  the INIT reply.
- Limit, in order:
  1. `request_timeout` of the INIT reply if `FUSE_REQUEST_TIMEOUT` is set,
     else 0.
  2. If 0, `fuse_default_req_timeout`.
  3. `min_not_zero()` with `fuse_max_req_timeout`: a non-zero maximum alone
     turns the timeout on.
  4. If still 0, no work is queued.
  5. Raised to at least `FUSE_TIMEOUT_TIMER_FREQ` seconds; not rounded.
- Work queue: `system_percpu_wq`, re-queued every
  `FUSE_TIMEOUT_TIMER_FREQ` seconds.
- `fuse_check_timeout()`: tests only the first entry of each list, with
  `fuse_request_expired()`.
- Lists tested: `fiq->pending`, `fch->bg_queue`, then for each device on
  `fch->devices` its `fpq->io` and every `fpq->processing` bucket.
- Ring queues: `fuse_uring_request_expired()` tests four lists per queue
  under `queue->lock`; it is a stub returning false without
  `CONFIG_FUSE_IO_URING`.
- `fch->num_waiting` zero: the check re-arms without looking at any list.
- `fch->connected` clear: the check returns without re-arming.
- Expiry: calls `fuse_chan_abort()` with `abort_with_err` false and does not
  re-arm.
- Cancel: `fuse_chan_abort()` uses `cancel_delayed_work()`;
  `fuse_chan_release()` uses `cancel_delayed_work_sync()`.
