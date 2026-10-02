- Wording in `Documentation/userspace-api/media/v4l/vidioc-g-fmt.rst`:
  drivers "should not return an error code unless the `type` field is
  invalid". It is stated for `VIDIOC_S_FMT`; `VIDIOC_TRY_FMT` inherits it as
  "equivalent ... with one exception".
- Adjusting: the driver "checks and adjusts the parameters against hardware
  abilities". The document also allows a simple device to ignore all input
  and return its default parameters; it does not require a nearest match.
- `EINVAL`: documented only for an invalid `type` or an unsupported buffer
  type, not for invalid fields of the format.
- `EBUSY`: for `VIDIOC_S_FMT` only; "I/O is already in progress or the
  resource is not available for other reasons".
- `VIDIOC_TRY_FMT` result: "must be identical" to what `VIDIOC_S_FMT`
  returns for the same input.
- Mandatory ioctls: `VIDIOC_G_FMT` and `VIDIOC_S_FMT` for every device that
  exchanges data; `VIDIOC_TRY_FMT` is recommended, not required.
- Core enforcement: none. `v4l_s_fmt()` and `v4l_try_fmt()` return the
  driver's result unchanged, and on an error the adjusted format is not
  copied back.
- Errors the core returns before the driver runs, besides `-ENODEV` for an
  unregistered device, `-ERESTARTSYS`, `-ENOMEM` and copy errors:

  | Error | Source | Ioctl |
  |---|---|---|
  | `-ENOTTY` | bit clear in `valid_ioctls` | both |
  | `-EBUSY` | `v4l2_prio_check()`, from `INFO_FL_PRIO` | `VIDIOC_S_FMT` |
  | `-EINVAL` | `check_fmt()`, or no op for the type | both |
  | `-EBUSY` | `v4l_enable_media_source()`, under `CONFIG_MEDIA_CONTROLLER` | `VIDIOC_S_FMT` |
