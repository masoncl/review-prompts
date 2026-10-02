- Layout: `fuse_simple_request()` is an inline in `fs/fuse/fuse_i.h` around
  `__fuse_simple_request()`; that, `fuse_simple_background()` and
  `fuse_simple_notify_reply()` are in `fs/fuse/req.c`.
- Each runs `fuse_req_prep()` and then the transport half in `fs/fuse/dev.c`:
  `fuse_chan_send()`, `fuse_chan_send_bg()`, `fuse_chan_send_notify_reply()`.
- `fuse_simple_notify_reply()`: not static; called by `fuse_retrieve()` in
  `fs/fuse/notify.c`.
- `-ECONNREFUSED` and `-EOVERFLOW`: returned by `fuse_req_prep()` and
  `fuse_fill_creds()`, before any request is allocated, on all three paths.
- `fuse_get_req()`: fails only with `-EINTR`, `-ENOTCONN` or `-ENOMEM`.
- Reply with arguments of the wrong length on `/dev/fuse`: the requester gets
  `-EIO`; `-EINVAL` goes to the server's write, see `fuse_dev_do_write()`.
- `fuse_simple_notify_reply()` with the input queue disconnected: returns 0;
  `fuse_dev_queue_req()` ends the request with `-ENOTCONN`, delivered through
  `end`.
- `fuse_simple_notify_reply()` returns `-ENOTCONN` only when `fuse_get_req()`
  finds `connected` clear in `struct fuse_chan`; it never returns `-ENODEV`.
- Forgets: sent by `fuse_chan_queue_forget()` with no `struct fuse_req`, not by
  `fuse_simple_background()`; the exception is `fuse_force_forget()` in
  `fs/fuse/readdir.c`, a `fuse_simple_request()` with `force` and `noreply`.
