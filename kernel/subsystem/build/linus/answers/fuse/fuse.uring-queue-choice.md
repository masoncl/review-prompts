- `fuse_uring_task_to_queue()`: only `task_cpu(current)`; no NUMA or
  neighbour fallback.
- Missing queue, foreground: `fuse_uring_queue_fuse_req()` ends the request
  with `-EINVAL`.
- Missing or stopped queue, background: `fuse_uring_queue_bq_req()` returns
  false and `fuse_chan_send_bg()` returns `-ENOTCONN`.
- `fuse_uring_flush_bg()`: asserts `queue->lock` and `fch->bg_lock`; it takes
  neither.
- `fch->blocked`: set in `fuse_uring_queue_bq_req()` when `num_background`
  reaches `max_background`.
