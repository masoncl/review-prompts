- `virtio_fs_send_req()`: handles requests only; the queue is
  `fs->mq_map[raw_smp_processor_id()]`, which `virtio_fs_map_queues()` fills
  with indices from `VQ_REQUEST` up. Forgets come through the separate hook
  `virtio_fs_send_forget()`.
- `req->in.h.unique`: assigned in `virtio_fs_send_req()` by
  `fuse_request_assign_unique()` (`fs/fuse/dev.c`), not before the `send_req`
  op runs; `fuse_send_one()` sets only `in.h.len`.
- Scatterlist order in `virtio_fs_enqueue_req()`: `req->in.h` and the FUSE
  in-args first (device-readable); `req->out.h` and the out-args after, only
  when `FR_ISREPLY` is set.
- There is no sg_init_fuse_pages() here; `sg_init_fuse_folios()` maps
  `ap->folios` with `ap->descs`.
- Processing list: `fsvq->fud->pq.processing[]`, under `fpq->lock` nested inside
  `fsvq->lock`.
- Kick: `virtqueue_kick_prepare()` under `fsvq->lock`, `virtqueue_notify()`
  after the unlock.
- `virtio_fs_enqueue_req()` takes no reference on `req`; the `fuse_request_end()`
  in completion consumes the one from `fuse_request_alloc()`.
- `-ENOSPC` is the only error that parks a request on `fsvq->queued_reqs`.
  `-ENOMEM` and `-ENOTCONN` fail the request.
- `-ENOSPC` in `virtio_fs_send_req()`: schedules no work and arms no timer. The
  retry runs in `dispatch_work`, which `virtio_fs_requests_done_work()`
  schedules when it finds `queued_reqs` non-empty.
- `dispatch_work`: a plain `struct work_struct`, not delayed work.
- Other errors in `virtio_fs_send_req()`: the request is not ended there. It
  goes on `fsvq->end_reqs` and `virtio_fs_request_dispatch_work()` calls
  `fuse_request_end()`.
- Forget errors in `send_forget_request()`: queued only on `-ENOSPC`. On any
  other error, or on a disconnected queue, the forget is freed and silently
  dropped.
- `virtio_fs_requests_done_work()`: unlinks each request from the processing
  list itself; `virtio_fs_request_complete()` does not touch the list.
- `virtio_fs_verify_response()`: runs on every used buffer of a request queue.
  A short reply, or an `oh->len` or `oh->unique` mismatch, completes the
  request with `-EIO`.
- `req->args->may_block`: such a request completes in its own work item,
  `virtio_fs_complete_req_work()`. All others complete inline in the per-queue
  `done_work`, so a sleeping `end` callback there stalls that queue.
