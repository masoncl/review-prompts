- `fuse_req_prep()` in `fs/fuse/req.c`: returns `-ECONNREFUSED` when
  `fc->conn_error` is set and `force` is clear, then calls
  `fuse_fill_creds()`.
- `force`, background: `fuse_chan_send_bg()` allocates with the caller's gfp
  and returns `-ENOMEM` on failure; `FR_FORCE` is not set.
- `force`, notify reply: ignored by `fuse_chan_send_notify_reply()`, which
  always calls `fuse_get_req()` and so can sleep and fail.
- `nocreds` without `force`: warns, then fills credentials as if the flag were
  clear.
- `noreply`: read only by `fuse_chan_send()`; `fuse_chan_send_notify_reply()`
  never sets `FR_ISREPLY`, whatever the flag says.
- `FR_ISREPLY` is tested in `fuse_dev_do_read()` and in
  `fs/fuse/virtio_fs.c`.
- `abort_on_kill`: read only on the sync path; set only by `fuse_send_init()`
  when `fc->sync_init`.
- `abort_on_kill`, fatal signal during the wait: `request_wait_answer()` calls
  `fuse_chan_abort()` and then waits uninterruptibly for `FR_FINISHED`; the
  request is not dequeued with `-EINTR`.
- Warnings, complete list for these four flags:
  - `WARN_ON(args->nocreds)` in `fuse_fill_creds()` when `force` is clear;
    reached from all three send functions.
  - `WARN_ON(args->force && !args->nocreds)` in `fuse_simple_background()` and
    in `fuse_simple_notify_reply()`.
  - No warning involves `noreply` or `abort_on_kill`.
