- `queue_interrupt()`: takes no lock and touches no list; it returns
  -EINVAL if `FR_INTERRUPTED` is clear, else calls
  `fiq->ops->send_interrupt()` and returns 0.
- `fuse_dev_queue_interrupt()`: under `fiq->lock`, queues only if
  `req->intr_entry` is empty and `FR_SENT` is set.
- `FR_SENT` test under `fiq->lock`: orders the queueing against
  `fuse_chan_resend()`, which clears `FR_SENT` under `fpq->lock` and then
  unlinks `req->intr_entry` under `fiq->lock`.
- Resent request with `FR_INTERRUPTED`: gets its INTERRUPT when it is read
  again, from the `FR_INTERRUPTED` test in `fuse_dev_do_read()`.
- -EAGAIN reply to an INTERRUPT: `fuse_dev_do_write()` returns the result of
  `queue_interrupt()`, so the write fails with -EINVAL if `FR_INTERRUPTED`
  is clear.
- Interrupt reply lookup: uses `fpq->processing`, so a reply for a request
  that is no longer there fails with -ENOENT.
- virtiofs: `virtio_fs_send_interrupt()` is empty.
