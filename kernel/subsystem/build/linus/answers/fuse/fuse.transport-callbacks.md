- Three tables implement `struct fuse_iqueue_ops`: `fuse_dev_fiq_ops`,
  `virtio_fs_fiq_ops`, and `fuse_io_uring_ops` in `fs/fuse/dev_uring.c`
  (built with `CONFIG_FUSE_IO_URING`).
- `fuse_io_uring_ops`: installed with `WRITE_ONCE(fiq->ops, ...)` in
  `fuse_uring_do_register()` once the ring is ready; `send_req` is
  `fuse_uring_queue_fuse_req()`.
- `fuse_io_uring_ops`: `send_forget` and `send_interrupt` are
  `fuse_dev_queue_forget()` and `fuse_dev_queue_interrupt()`, so forgets and
  interrupts still go out through a read of the device.
- Background requests queued once the ring is ready: bypass `send_req`;
  `fuse_request_queue_background_uring()` sets `in.h.len`, assigns the
  identifier and calls `fuse_uring_queue_bq_req()`.
- Locks at entry: `fuse_send_one()` holds no `fiq->lock`; `flush_bg_queue()`
  calls it under `fch->bg_lock`.
- `FR_PENDING`: set by `fuse_request_init()`, not by `send_req`.
- Identifier: use `fuse_request_assign_unique()` or, under `fiq->lock`,
  `fuse_request_assign_unique_locked()`; they skip `FUSE_NOTIFY_REPLY` and
  fire `trace_fuse_request_send()`, which a bare `fuse_get_unique()` does
  not.
- `fuse_uring_queue_fuse_req()`: keeps `FR_PENDING` set while the request
  waits on `queue->fuse_req_queue`; `fuse_uring_add_req_to_ring_ent()`
  clears it.
- `fuse_uring_queue_fuse_req()` with the queue stopped: error `-ENOTCONN`.
- virtio-fs, any error other than `-ENOSPC`, `-ENOMEM` included:
  `req->out.h.error` gets the return value of `virtio_fs_enqueue_req()`, not
  `-EIO`, and the request goes on `fsvq->end_reqs`.
- **Unsafe usage**: a `send_req` op leaving `FR_PENDING` set on a request
  that it puts on a list the lock chosen in `request_wait_answer()` does not
  protect.
  - Safe: `fuse_dev_queue_req()` queues on `fiq->pending` under `fiq->lock`,
    the lock `fuse_remove_pending_req()` is given.
  - Safe: `fuse_uring_queue_fuse_req()` sets `FR_URING` and
    `req->ring_queue`, so `fuse_uring_remove_pending_req()` takes
    `queue->lock`.
  - Safe: `virtio_fs_send_req()` clears `FR_PENDING` before it queues the
    request anywhere.
