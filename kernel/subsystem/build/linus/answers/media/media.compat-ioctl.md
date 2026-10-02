- `v4l2_translate_cmd()`: defined and exported in
  `drivers/media/v4l2-core/v4l2-ioctl.c`; there is no video_translate_cmd()
  here. It maps the time32 commands, for example `VIDIOC_QBUF_TIME32`, then
  calls `v4l2_compat_translate_cmd()` when `in_compat_syscall()`.
- Time32 code in `v4l2-ioctl.c`: three places, `v4l2_translate_cmd()`,
  `video_get_user()` and `video_put_user()`, all under
  `!CONFIG_64BIT && CONFIG_COMPAT_32BIT_TIME`.
- `drivers/media/v4l2-core/v4l2-compat-ioctl32.c`: built only with
  `CONFIG_COMPAT`; its get and put functions are called from
  `video_get_user()`, `video_put_user()` and `video_usercopy()`.
- `struct v4l2_event32` and `VIDIOC_DQEVENT32`: handled only under
  `CONFIG_X86_64`; `struct v4l2_event32_time32` only under
  `CONFIG_COMPAT_32BIT_TIME`.
- Sub-device nodes: standard `'V'` ioctls take the same path through
  `video_usercopy()`; `subdev_compat_ioctl32()` is reached only for
  commands that `v4l2_compat_ioctl32()` treats as private.
- A change that adds a field to `struct v4l2_buffer` or
  `struct v4l2_event`: the converters list fields by hand, so each must be
  updated. For example `get_v4l2_buffer32()` and the `VIDIOC_QBUF_TIME32`
  case of `video_get_user()`; `put_v4l2_event32()` and the
  `VIDIOC_DQEVENT_TIME32` case of `video_put_user()`. Search for
  `v4l2_buffer32`, `v4l2_buffer_time32`, `v4l2_event32` and
  `v4l2_event_time32` to find the rest.
- A change that adds a field to `struct v4l2_create_buffers`:
  `get_v4l2_create32()` and `put_v4l2_create32()` copy fields by name.
- A change that adds a value to `enum v4l2_buf_type`:
  `get_v4l2_format32()` and `put_v4l2_format32()` return `-EINVAL` for a
  type they have no case for.
- A new command that needs conversion: add the compat struct and command
  number, as `struct v4l2_edid32` and `VIDIOC_G_EDID32`, and cases in
  `v4l2_compat_translate_cmd()`, `v4l2_compat_get_user()` and
  `v4l2_compat_put_user()`. A read-only command needs no get case.
- A new array ioctl: `v4l2_compat_get_array_args()` and
  `v4l2_compat_put_array_args()` fall back to a plain copy; add a case only
  if the element layout differs.
- **Unsafe usage**: a driver `unlocked_ioctl` that compares the raw `cmd`
  with a command that `v4l2_translate_cmd()` maps, for example
  `VIDIOC_S_FMT`, before it calls `video_ioctl2()`. The raw command of a
  32-bit or time32 caller has another size and does not match.
  - Safe: compare the result of `v4l2_translate_cmd()`, and pass the raw
    `cmd` on, as `uvc_v4l2_unlocked_ioctl()` does.
