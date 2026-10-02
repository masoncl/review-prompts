- `fuse_chan_abort()`: never waits for `FR_LOCKED`; it sets `FR_ABORTED`,
  skips a locked request and leaves it on `fpq->io` for the copier to end.
- `FR_ABORTED`: set in one place, the walk of `fpq->io` in
  `fuse_chan_abort()`; a request on no `fpq->io` gets no protection from
  `lock_request()`.
- Before the copy: test `fpq->connected` under `fpq->lock`, then put the
  request on `fpq->io`; a request added after the abort walked the list is
  never ended by it.
- Read side: `fuse_dev_do_read()` does not set `FR_LOCKED`; the first
  `fuse_copy_fill()` does, after its `unlock_request()` has tested
  `FR_ABORTED`.
- Write side: `fuse_dev_do_write()` sets `FR_LOCKED` under `fpq->lock` when
  it moves the request to `fpq->io`.
- References: the copier takes none for the copy; `fuse_chan_abort()` takes
  one with `__fuse_get_request()` for each unlocked request it takes from
  `fpq->io`, so the copier's later `fuse_request_end()` has a reference to
  drop.
- After the copy, both sides: under `fpq->lock` clear `FR_LOCKED` and test
  `fpq->connected`; to end the request, call `list_del_init()` only if
  `FR_PRIVATE` is clear, then call `fuse_request_end()` outside the lock.
- `fuse_dev_do_write()`: tests `fpq->connected`, not `FR_ABORTED`, and calls
  `fuse_request_end()` on every path once it has moved the request to
  `fpq->io`.
- Steps that may sleep run between `unlock_request()` and `lock_request()`:
  `iov_iter_get_pages2()`, `pipe_buf_confirm()`, `alloc_page()` in
  `fuse_copy_fill()`; `pipe_buf_try_steal()` in `fuse_try_move_folio()`.
- `struct fuse_copy_state`: has no is_kaddr field; `is_uring`,
  `skip_folio_copy` and `ring.copied_sz` serve the io_uring copy.
- io_uring: `setup_fuse_copy_state()` sets `cs->req`, but its requests are
  never on `fpq->io`, so `lock_request()` cannot fail there.
- **Unsafe usage**: using `req->args` or its folios after `lock_request()`
  or `unlock_request()` returned `-ENOENT`.
  - Unsafe: `fuse_chan_abort()` may have handed the request to
    `fuse_dev_end_requests()`, which may already have woken the requester
    that owns the args.
  - Safe: stop copying and run the end sequence, touching only `req->flags`
    and `req->list` under `fpq->lock`, as the `out_end` path of
    `fuse_dev_do_read()` does.
