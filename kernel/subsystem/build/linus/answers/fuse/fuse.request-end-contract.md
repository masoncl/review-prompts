- `FR_FINISHED`: may already be set; the call then only drops one reference.
- Double end: `fuse_chan_abort()` relies on it for a request it took from
  `fpq->io`, and takes a reference of its own for that second call.
- `WARN_ON()` for `FR_PENDING` and `FR_SENT`: runs only on the first call;
  it warns and the function goes on.
- `FR_LOCKED`: not tested by `fuse_request_end()`; `fuse_dev_do_read()` and
  `fuse_dev_do_write()` clear it under `fpq->lock` before they call.
- `fuse_dev_end_requests()`: sets -ECONNABORTED and clears `FR_SENT`, not
  `FR_PENDING`; `fuse_chan_abort()` clears `FR_PENDING` under `fiq->lock`
  before it splices.
- `req->intr_entry`: unlinked by `fuse_request_end()` only if
  `FR_INTERRUPTED` is set; `fuse_request_free()` warns if it is still linked.
- Reference consumed: the one from `fuse_request_alloc()`; a background
  request has no other, so it is freed inside the call, after `args->end`.
- Sync request: survives the call through the reference taken in
  `__fuse_request_send()`, dropped by `fuse_chan_send()`.
- **Unsafe usage**: reading `req` after `fuse_request_end()` returns,
  without a reference of one's own.
  - Safe: `fuse_dev_do_read()` takes `__fuse_get_request()` under
    `fpq->lock` before it sets `FR_SENT`, since a reply can end the request
    once that lock is dropped, and drops it after its `FR_INTERRUPTED` test.
  - Safe: `fuse_chan_send()` reads `req->out.h.error` under the reference
    from `__fuse_request_send()`.
