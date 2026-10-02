- `priv` is `NULL`: every core call of a `struct v4l2_ioctl_ops` callback with
  a `(struct file *file, void *priv, ...)` prototype passes `NULL`, including
  `v4l_querycap()`, the `DEFINE_V4L_STUB_FUNC()` stubs and `vidioc_default`
  in `__video_do_ioctl()`.
- `__video_do_ioctl()` fetches the handle with `file_to_v4l2_fh()` for its own
  use only (lock choice, priority check, `vfh->ctrl_handler`); it does not
  hand it to the callback.
- `file_to_v4l2_fh()` in `include/media/v4l2-fh.h`: returns
  `filp->private_data` with no test of any flag and no `NULL` check.
- `vidioc_subscribe_event` and `vidioc_unsubscribe_event` are the exception in
  prototype: they take `struct v4l2_fh *fh` and no file; `v4l_subscribe_event()`
  and `v4l_unsubscribe_event()` pass `file_to_v4l2_fh(file)`.
- **Unsafe usage**: deriving the handle or the driver context from `priv` in a
  `struct v4l2_ioctl_ops` callback (`ctx = priv`, `container_of(priv, ...)`);
  `priv` is `NULL`, so a callback that dereferences it oopses.
  - Safe: derive it from `file`, as `file2ctx()` in
    `drivers/media/test-drivers/vim2m.c` does with
    `container_of(file_to_v4l2_fh(file), ...)`.
  - Safe: `container_of(fh, ...)` on the `struct v4l2_fh *fh` argument of a
    `vidioc_subscribe_event` callback, as `vicodec_subscribe_event()` does;
    that argument is the real handle.
  - Safe: a callback that forwards `priv` unread to another callback of the
    same driver, as `vidioc_s_fmt_vid_cap()` in
    `drivers/media/test-drivers/vim2m.c` does.
