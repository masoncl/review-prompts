- `congestion_threshold`: field of `struct fuse_conn`, not under `bg_lock`;
  `fs/fuse/control.c` uses `READ_ONCE()` and `WRITE_ONCE()`.
- `fuse_chan_num_background()`: lockless `READ_ONCE()`; this is what
  `fuse_handle_readahead()` and `fuse_writepages()` compare with
  `congestion_threshold`.
- No congestion state is set or cleared anywhere in `fs/fuse`.
- `fuse_request_queue_background()` when connected and the ring is not ready:
  always appends to `bg_queue`, then calls `flush_bg_queue()`.
- `fuse_request_queue_background()` returning false: `fuse_chan_send_bg()`
  drops the request and returns `-ENOTCONN`; it does not call `end`.
- `fuse_request_bg_finish()`: clears `blocked` when `num_background` equals
  `max_background` before the decrement.
- `fuse_chan_max_background_set()`: recomputes `blocked` as
  `num_background >= max_background`; used by `process_init_limits()` and the
  control file.
- With the ring ready, `fuse_request_queue_background()` hands over to
  `fuse_uring_queue_bq_req()`:
  - same `num_background` and `blocked` accounting under `bg_lock`;
  - the request waits on the per-queue `fuse_req_bg_queue`, not on `bg_queue`;
  - `fuse_uring_flush_bg()` lets one background request per queue go active
    even when `active_background` has reached `max_background`;
  - `fuse_uring_queue_bq_req()` tests `queue->stopped`, not `connected`, and
    returns false when set.
- `fuse_uring_req_end()`: calls `fuse_request_bg_finish()` itself, which clears
  `FR_BACKGROUND`, so `fuse_request_end()` skips its background branch.
