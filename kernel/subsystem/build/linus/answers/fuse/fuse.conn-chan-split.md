- `struct fuse_conn` has no `connected`, `iq`, `devices`, `bg_lock`,
  `bg_queue`, `num_background`, `active_background`, `max_background`,
  `blocked`, `blocked_waitq`, `initialized` or `num_waiting`; all are in
  `struct fuse_chan`, reached as `fc->chan` (back pointer `fch->conn`).

| State | Lives in | Protected by |
|---|---|---|
| `iq` (`struct fuse_iqueue`) | channel | `fiq->lock` |
| `devices`, `connected`, the stores that publish `ring` and `ring->queues[qid]` | channel | `fch->lock` |
| `max_background`, `num_background`, `active_background`, `bg_queue`, `blocked` | channel | `fch->bg_lock` |
| `initialized` | channel | none; `smp_store_release()` / `smp_load_acquire()` |
| `minor`, `max_write`, `max_pages` | both, one copy each | none |
| `max_read`, `max_pages_limit`, `congestion_threshold`, feature bits | connection | none |
| `polled_files`, `backing_files_map`, `curr_bucket` | connection | `fc->lock` |
| `mounts` | connection | `fc->killsb` |

- `fch->connected`: cleared only in `fuse_chan_abort()`, holding `fch->lock`
  and `fch->bg_lock`; `fuse_get_req()` reads it with no lock,
  `fuse_request_queue_background()` under `fch->bg_lock`.
- There is no fuse_set_initialized() here; `fuse_chan_set_initialized()`
  copies a non-NULL `struct fuse_chan_param` into the channel, then does
  `smp_store_release(&fch->initialized, 1)`.
- Channel copies of `minor`, `max_write`, `max_pages`: read by `fs/fuse/dev.c`
  and `fs/fuse/dev_uring.c`; filesystem code reads the `struct fuse_conn`
  copies.
- `fch->abort_with_err`: per-abort argument of `fuse_chan_abort()`;
  `fc->abort_err` is the INIT feature bit that `fuse_conn_abort_write()`
  passes in.
- Lock order in `fuse_chan_abort()`: `fch->lock` outermost; inside it
  `fch->bg_lock`, `fpq->lock` then `req->waitq.lock`, `fiq->lock`, and
  `fc->lock` through `fuse_end_polls()`.
