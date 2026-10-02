- Resend function: there is no fuse_resend(); `fuse_chan_resend()` in
  `fs/fuse/dev.c` does it, called by `fuse_notify_resend()` in
  `fs/fuse/notify.c`.
- Resent request: keeps its id; `fuse_chan_resend()` ORs
  `FUSE_UNIQUE_RESEND` into `req->in.h.unique` under `fiq->lock`.
- Reply after a resend: `fuse_request_find()` compares the whole id, so a
  reply with the id read before the resend fails with -ENOENT.
- `fuse_req_hash()`: masks only `FUSE_INT_REQ_BIT`, so the resent request
  lands in the bucket of the new id.
- `fiq->reqctr`: a plain `u64` under `fiq->lock` on every transport;
  `fuse_request_assign_unique()`, used by virtiofs and fuse-over-io-uring,
  calls `fuse_get_unique()`.
- Interrupted request on resend: requeued like any other;
  `fuse_chan_resend()` only unlinks its `req->intr_entry`.
- INTERRUPT after a resend: `fuse_read_interrupt()` builds both ids from
  `req->in.h.unique` at read time, so they carry `FUSE_UNIQUE_RESEND`.
- `fiq->connected` clear in `fuse_chan_resend()`: the requests go to
  `fuse_dev_end_requests()` before `FR_PENDING` is ever set.
- Scope of resend: only the `fpq->processing` buckets of devices on
  `fch->devices`; requests on `fpq->io` are left alone.
