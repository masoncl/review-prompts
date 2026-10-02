- Copy-in size, command with `_IOC_WRITE`: `video_get_user()` copies
  `_IOC_SIZE` bytes only when the table entry has no `INFO_FL_CLEAR`; with
  it, only the bytes up to the end of the named field are copied and the
  rest is zeroed.
- `_IOC_NONE` command: no buffer is used; the handler gets the raw `arg`
  value as its pointer.
- `check_array_args()` groups and limits:

  | Ioctl | Count field | Limit | Error |
  |---|---|---|---|
  | `VIDIOC_QUERYBUF`, `VIDIOC_QBUF`, `VIDIOC_DQBUF`, `VIDIOC_PREPARE_BUF`, multiplanar type | `length` | `VIDEO_MAX_PLANES` | `-EINVAL` |
  | `VIDIOC_G_EDID`, `VIDIOC_S_EDID` | `blocks` | 256 | `-EINVAL` |
  | `VIDIOC_G_EXT_CTRLS`, `VIDIOC_S_EXT_CTRLS`, `VIDIOC_TRY_EXT_CTRLS` | `count` | `V4L2_CID_MAX_CTRLS` | `-EINVAL` |
  | `VIDIOC_SUBDEV_G_ROUTING`, `VIDIOC_SUBDEV_S_ROUTING` | `len_routes` | 256 | `-E2BIG` |

- Array size: no other limit is tested; the buffer comes from `kvmalloc()`.
- Array copy-back outside a compat syscall: whenever the result is copied
  back, the whole array is written back too, with the `array_size` computed
  before the handler ran. A count field the handler changed does not change
  the amount.
- Array copy-back in a compat syscall: for the plane and control arrays
  `v4l2_compat_put_array_args()` loops over the current `length` or `count`
  instead.
- `INFO_FL_ALWAYS_COPY` in `v4l2_ioctls`: search the table for the flag; it
  takes effect on `VIDIOC_G_EDID`, `VIDIOC_S_EDID` and the three EXT_CTRLS
  ioctls, all `_IOWR`.
- `VIDIOC_SUBDEV_G_ROUTING` and `VIDIOC_SUBDEV_S_ROUTING`: copied back on
  error by an explicit test on `cmd` in `video_usercopy()`; they have no
  table entry.
- `-ENOTTY` or `-ENOIOCTLCMD` from the handler: nothing is copied back, with
  or without `always_copy`.
- **Unsafe usage**: `INFO_FL_ALWAYS_COPY` on a command without `_IOC_WRITE`.
  `video_get_user()` returns for a read-only command before it reads the
  flags, so `always_copy` stays false and an error drops the result.
  - Safe: an `_IOWR` command with the flag, as `VIDIOC_G_EXT_CTRLS`;
    `video_get_user()` reads the flag only past its `_IOC_WRITE` test.
