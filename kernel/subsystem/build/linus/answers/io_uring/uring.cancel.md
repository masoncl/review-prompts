- `io_try_cancel()`, io-wq step: returns at once only when
  `io_async_cancel_one()` gives 0; `-EALREADY` (work running) continues to
  `io_poll_cancel()` like `-ENOENT` does.
- `io_try_cancel()` after an io-wq `-EALREADY`: returns what the later steps
  return, so with `CONFIG_FUTEX` the caller can see `-ENOENT` for a request
  that is running in io-wq.
- `__io_async_cancel()` slow path: runs whenever `io_try_cancel()` returns
  `-ENOENT`, with or without `IORING_ASYNC_CANCEL_ALL`; it searches only the
  io-wq of each task on `ctx->tctx_list`, under `uring_lock` and
  `ctx->tctx_lock`.
- `io_cancel_req_match()`: `user_data` is compared when
  `IORING_ASYNC_CANCEL_USERDATA` is set, or when neither
  `IORING_ASYNC_CANCEL_FD` nor `IORING_ASYNC_CANCEL_OP` is set; with
  `IORING_ASYNC_CANCEL_ANY` it is not compared at all.
- `io_cancel_req_match()` with `IORING_ASYNC_CANCEL_FD`: compares `req->file`
  with `cd->file` only; `REQ_F_FIXED_FILE` is used in `io_async_cancel()` to
  resolve `cd->file`, not in the match.
- Sequence mark: there is no REQ_F_CANCEL_SEQ flag; the mark is
  `cancel_seq_set` in `struct io_kiocb` plus `cancel_seq` in
  `struct io_wq_work`, both written by `io_cancel_match_sequence()` in
  `io_uring/cancel.h`.
- Sequence test: runs only with `IORING_ASYNC_CANCEL_ALL` or
  `IORING_ASYNC_CANCEL_ANY`; a keyed single cancel can match the same request
  on every call.
- `io_cancel_match_sequence()`: stamps the request as a side effect of the
  match, whether or not the cancel then succeeds.
- `io_poll_find()` in `io_uring/poll.c`: does not call
  `io_cancel_req_match()`; it compares `user_data` in one hash bucket and
  calls `io_cancel_match_sequence()` itself, only for
  `IORING_ASYNC_CANCEL_ALL`. `io_poll_file_find()` is the one that calls
  `io_cancel_req_match()`.
- Count returned with `IORING_ASYNC_CANCEL_ALL` or `IORING_ASYNC_CANCEL_ANY`:
  `nr` in `__io_async_cancel()` goes up once per `io_try_cancel()` call that
  returned anything but `-ENOENT`, and once per task on `ctx->tctx_list` whose
  io-wq had a match in the slow path; `io_cancel_remove()` with
  `IORING_ASYNC_CANCEL_ALL` cancels every match on its list in one call.
- `io_sync_cancel()`: entered with `uring_lock` held (from
  `io_uring_register()`); it runs the same `__io_async_cancel()` search and
  retries only on `-EALREADY`, never on `-ENOENT`.
- `io_sync_cancel()` retry: takes a new `cd.seq` from `ctx->cancel_seq` on
  every pass.
- `__io_sync_cancel()`: looks the fixed file up again on every pass, because
  `uring_lock` was dropped in between.
- `io_sync_cancel()` result from the wait loop: `-ENOENT` and positive counts
  are turned into 0.
