- Channel fields: `io_uring`, `ring`, `initialized`, `connected`,
  `blocked_waitq` and the background counters are in `struct fuse_chan`
  (`fs/fuse/fuse_dev_i.h`), written `fch->...`; `ring` exists only under
  `CONFIG_FUSE_IO_URING`; `struct fuse_ring` points back with `chan`.
- `process_init_reply()`: only sets `io_uring_enabled` in
  `struct fuse_chan_param`, when the reply has `FUSE_OVER_IO_URING` and
  `fuse_uring_enabled()` is true.
- `fuse_uring_conn_init()`: called from `fuse_chan_set_initialized()` in
  `fs/fuse/dev.c`, before `fch->initialized` is stored.
- `fuse_uring_conn_init()`: calls `fuse_uring_create()` and sets
  `fch->io_uring` only if that returned a ring.
- `fuse_uring_create()`: returns NULL on allocation failure or when
  `fch->connected` is 0; the connection then stays on the device path.
- `fuse_uring_register()`: does not create the ring; returns `-EINVAL` when
  `fch->ring` is NULL.
- `fuse_uring_cmd()`: returns `-EOPNOTSUPP` when its test finds
  `fch->io_uring` 0, whatever `enable_uring` holds.
- `is_ring_ready()`: walks all `ring->nr_queues` queues and skips the queue that
  just registered; there is no nr_queues_ready counter.
- Request with `force`: `fuse_chan_send()` and `fuse_chan_send_bg()` skip
  `fuse_get_req()`; if `fuse_send_one()` runs for it before ready, it lands on
  `fiq->pending` through `fuse_dev_queue_req()` and is served by a read of the
  device.
- `fuse_new_init()`: offers `FUSE_HAS_IO_URING_BUFPOOL` together with
  `FUSE_OVER_IO_URING`.
