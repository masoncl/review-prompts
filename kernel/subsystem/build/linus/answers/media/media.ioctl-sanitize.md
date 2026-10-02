- `check_fmt()`: of the driver's ops it tests only the get op of the type,
  for example `vidioc_g_fmt_vid_cap`. A missing set or try op for the type
  is caught later, by the `break` in `v4l_s_fmt()` or `v4l_try_fmt()`, also
  as `-EINVAL`.
- `check_fmt()`, single-planar video types: pass when only the mplane get op
  exists, for example `vidioc_g_fmt_vid_cap_mplane` for
  `V4L2_BUF_TYPE_VIDEO_CAPTURE`.
- `VIDIOC_S_FMT` and `VIDIOC_TRY_FMT`: have no `INFO_FL_CLEAR`; the whole
  `struct v4l2_format` is copied in. The clearing is `memset_after()` in
  the handlers, per type.
- `v4l_sanitize_format()`: clamps `fmt.pix_mp.num_planes` to
  `VIDEO_MAX_PLANES`, not to the plane count of the pixel format.
- `v4l_sanitize_colorspace()`: runs for `pix` and `pix_mp`; it does not
  depend on `V4L2_PIX_FMT_FLAG_SET_CSC`.
  - Validity tests are in `include/media/v4l2-common.h`, against
    `V4L2_COLORSPACE_LAST`, `V4L2_XFER_FUNC_LAST` and `V4L2_YCBCR_ENC_LAST`.
  - Invalid `colorspace`: all four colorimetry fields are set to default.
  - HSV pixel formats: the encoding is checked with
    `v4l2_is_hsv_enc_valid()` instead.
- Overlay types: the core sets `fmt.win.clips` and `fmt.win.bitmap` to NULL
  and `fmt.win.clipcount` to 0 before the driver runs.
- `v4l_pix_format_touch()`: applied after the driver returns, only in the
  `V4L2_BUF_TYPE_VIDEO_CAPTURE` case and only for `VFL_TYPE_TOUCH`.
- `fmt.pix.priv`: set to `V4L2_PIX_FMT_PRIV_MAGIC` after the driver returns,
  also when the driver returned an error.
- `v4l_enable_media_source()`: called by `v4l_s_fmt()` before the sanitize
  step; `v4l_try_fmt()` does not call it.
- `v4l_create_bufs()`: calls `check_fmt()` and `v4l_sanitize_format()` on
  the embedded format, but does none of the per-type `memset_after()`
  clearing; reserved bytes of the format reach the driver as written.
