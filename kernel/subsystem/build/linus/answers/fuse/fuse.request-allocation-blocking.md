- `fuse_get_req()`: takes `(fch, for_background)`; it has no idmap or
  credential handling.
- Sleep conditions in `fuse_block_alloc()`, any one of:
  - `initialized` is clear;
  - `for_background` and `blocked`;
  - `io_uring` and `connected` set and `fuse_uring_ready()` false; this one
    blocks foreground requests too.
- Without `CONFIG_FUSE_IO_URING`: `fuse_uring_conn_init()` is an empty stub, so
  `io_uring` stays 0 and the third condition is never true.
- `blocked`: follows `max_background`, not `congestion_threshold`.
- The wait: `wait_event_state_exclusive()` with
  `TASK_KILLABLE | TASK_FREEZABLE`; only a fatal signal ends it, and the
  sleeper can be frozen.
- After the sleep: only `connected` is tested; `fc->conn_error` was tested by
  `fuse_req_prep()` before the sleep and is not tested again.
- Ordering on `initialized`: `smp_load_acquire()` in `fuse_block_alloc()` pairs
  with `smp_store_release()` in `fuse_chan_set_initialized()`.
- Wakers of `blocked_waitq`:
  - `fuse_chan_set_initialized()`: wakes all; called from
    `process_init_reply()` and `fuse_chan_abort()`.
  - `fuse_chan_abort()`: wakes all, after clearing `blocked`.
  - `fuse_request_bg_finish()`: wakes one; called by `fuse_request_end()` and
    `fuse_uring_req_end()`.
  - `fuse_chan_max_background_set()`: `wake_up_nr()` for the free slots.
  - `fuse_put_request()`: wakes one for an unsent `FR_BACKGROUND` request, only
    when `blocked` is clear.
  - `fuse_get_req()`: wakes one only on its `-ENOMEM` path with
    `for_background`, without testing `blocked`.
  - `fuse_uring_do_register()`: wakes all when the ring becomes ready.
  - `fuse_uring_cmd()`: clears `io_uring` and wakes all when registration
    fails.
  - `fuse_drop_waiting()`: wakes all for `fuse_chan_wait_aborted()`.
