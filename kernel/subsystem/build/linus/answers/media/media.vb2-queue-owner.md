- `vb2_fop_mmap()` and `vb2_fop_poll()`: make no owner test.
- `vb2_fop_poll()`: makes the caller owner when the poll started file I/O.
- `vb2_fop_read()`: sets `owner` before `vb2_read()` and clears it afterwards
  when `q->fileio` is not set.
- `vb2_fop_write()`: sets `owner` only after `vb2_write()` left `q->fileio`
  set, and never clears it.
- `vb2_ioctl_reqbufs()`: `vb2_verify_memory_type()` runs before the owner
  test, so a non-owner can get `-EINVAL` instead of `-EBUSY`.
- `vb2_ioctl_create_bufs()` and `vb2_ioctl_remove_bufs()` with count 0:
  return before the owner test.
- `vb2_ioctl_remove_bufs()`: never changes `owner`, even when it removes the
  last buffer.
- In `drivers/media/common/videobuf2/videobuf2-v4l2.c` owner tests exist only
  in the `vb2_ioctl_` and `vb2_fop_` helpers; `vb2_reqbufs()`, `vb2_qbuf()`,
  `vb2_streamon()` and the rest of the file make none.
- `v4l2_m2m_reqbufs()`: sets `vq->owner` like `vb2_ioctl_reqbufs()`, but
  nothing in `drivers/media/v4l2-core/v4l2-mem2mem.c` tests it.
