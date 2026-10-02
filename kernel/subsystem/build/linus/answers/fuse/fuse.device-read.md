- Transport state: `fuse_dev_do_read()` reads it from `struct fuse_chan`
  (`fud->chan`), not `struct fuse_conn`: `fch->max_write`,
  `fch->abort_with_err`, and `fch->minor` in `fuse_read_forget()`.
- Buffer minimum: the larger of `FUSE_MIN_READ_BUFFER` and
  `sizeof(struct fuse_in_header) + sizeof(struct fuse_write_in) +
  fch->max_write`; smaller gives `-EINVAL` before anything is dequeued.
- Forgets and requests both queued: `fiq->forget_batch` lets 8 request reads
  through, then 16 forget reads, then repeats.
- Interrupt or single forget: `fuse_read_interrupt()` and
  `fuse_read_single_forget()` make no size test; the minimum at entry is the
  only bound.
- Batch forget: `fuse_read_batch_forget()` limits the count to what fits in
  `nbytes`; the rest stay queued.
- Request larger than the buffer: the requester gets `-EIO` (`-E2BIG` for
  `FUSE_SETXATTR`); the read does not fail, it goes to `restart` and returns
  the next item, or waits.
- `fpq->connected` clear before the request goes on `fpq->io`: the request
  ends with `-ECONNABORTED` and the read returns `-ECONNABORTED`, whatever
  `fch->abort_with_err` holds.
- `fpq->connected` clear after the copy: the read returns `-ECONNABORTED` if
  `fch->abort_with_err`, else `-ENODEV`.
- Copy error: the requester gets `-EIO`; the read returns the copy's own
  error.
- `FR_INTERRUPTED` set when the request reaches `FR_SENT`: the read calls
  `queue_interrupt()`; it does not end the request.
