- Names: there is no fuse_abort_conn() or fuse_wait_aborted();
  `fuse_chan_abort()` and `fuse_chan_wait_aborted()` in `fs/fuse/dev.c` take
  a `struct fuse_chan`.
- Helpers: `fuse_chan_set_initialized()`, `fuse_end_polls()` and
  `fuse_dev_end_requests()` do the jobs of fuse_set_initialized(),
  end_polls() and end_requests().
- Order of the lists: `fpq->io`, then `fpq->processing`, then
  `fch->bg_queue` flushed through `flush_bg_queue()` (on `/dev/fuse` into
  `fiq->pending`), then `fiq->pending`.
- `fch->blocked`: cleared, not set, together with
  `fch->max_background = UINT_MAX`, under `fch->bg_lock`.
- Second call: does nothing to the lists once `fch->connected` is clear.
- Device read after abort: -ECONNABORTED if `fch->abort_with_err`, else
  -ENODEV; there is no fc->aborted.
- `abort_with_err`: only `fuse_conn_abort_write()` passes a value other
  than false, namely `fc->abort_err`.
- Device write after abort: -ENOENT for a reply, -EINVAL for a
  notification; not -ENODEV.
- Callers: search for `fuse_chan_abort(`; the ones easy to miss are
  `request_wait_answer()` for `args->abort_on_kill` and `fuse_dev_install()`
  when the install fails.
- `fs/fuse/dev_uring.c`: does not call `fuse_chan_abort()`;
  `fuse_uring_abort()` is called by it, after `fch->lock` is dropped.
- `fuse_dev_release()` of a device that is not the last: ends that device's
  `fpq->processing` requests with -ECONNABORTED and does not abort.
- `fuse_chan_wait_aborted()`: called only from `fuse_conn_destroy()`, right
  after the abort.
- Wake-up for `fuse_chan_wait_aborted()`: `fuse_drop_waiting()` wakes
  `fch->blocked_waitq` only when `fch->num_waiting` reaches 0 and
  `fch->connected` is clear, so the wait must follow an abort.
