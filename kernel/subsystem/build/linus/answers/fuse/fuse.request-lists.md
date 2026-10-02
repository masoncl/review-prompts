- Between `fiq->pending` and `fpq->io`: `fuse_dev_do_read()` holds the
  request on no list and under no lock while it tests the buffer size.
- Abort in that window: cannot reach the request; the reader's test of
  `fpq->connected` under `fpq->lock` ends it with -ECONNABORTED.
- `struct fuse_pqueue`: one per `struct fuse_dev`; `fuse_dev_do_write()`
  searches only the `fpq->processing` of the device written to.
- Lookup: there is no request_find(); the function is
  `fuse_request_find()` in `fs/fuse/dev.c`, which `fuse_dev_do_write()`
  calls under `fpq->lock`.
- `fch->devices`: walked under `fch->lock`, with `fpq->lock` nested inside,
  in `fuse_chan_abort()`, `fuse_chan_resend()` and `fuse_check_timeout()`.
- `fiq->lock`: nests inside `fch->bg_lock`, since `flush_bg_queue()` calls
  `fiq->ops->send_req()` with `fch->bg_lock` held.
- Private lists: `to_end` in `fuse_chan_abort()` and `fuse_dev_release()`,
  `to_queue` in `fuse_chan_resend()`; filled under the source list's lock;
  `fuse_dev_end_requests()` consumes them with no lock, and
  `fuse_chan_resend()` splices `to_queue` onto `fiq->pending` under
  `fiq->lock`.
- `fpq->io` insertion: `list_add()` on read and `list_move()` on write, both
  at the head; `fpq->processing` and `fiq->pending` are filled at the tail,
  except that `fuse_chan_resend()` splices at the head of `fiq->pending`.
