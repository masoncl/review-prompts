- `v4l2_get_link_freq()`: a plain exported function in
  `drivers/media/v4l2-core/v4l2-common.c`, signature
  `(const struct media_pad *pad, unsigned int mul, unsigned int div)`.
- There is no `_Generic` macro and no form that takes a
  `struct v4l2_ctrl_handler *`; static `v4l2_get_link_freq_ctrl()` is internal
  to that file.
- `pad`: the op is called on the subdev that owns `pad` (`pad->entity`,
  `pad->index`); no link is followed, so the caller resolves the transmitter's
  source pad first, for example with `media_pad_remote_pad_unique()`.
- First source: pad op `get_mbus_config`; a non-zero `link_freq` in
  `struct v4l2_mbus_config` is returned as is.
- `get_mbus_config` error other than `-ENOIOCTLCMD`: returned at once, the
  controls are not tried.
- Pixel-rate estimate: `V4L2_CID_PIXEL_RATE` value `* mul / div`, with no extra
  factor of 2; the caller passes 2 * lanes as `div` for D-PHY.
- `mul` or `div` zero and no `V4L2_CID_LINK_FREQ` control: `-ENOENT`, tested
  before `V4L2_CID_PIXEL_RATE` is looked up; callers pass 0, 0 to refuse the
  estimate.
- `v4l2_link_freq_to_bitmap()` with `num_of_fw_link_freqs` 0: returns
  `-ENODATA`, not 0 and not `-ENOENT`.
- `v4l2_link_freq_to_bitmap()` with no match: returns `-ENOENT`.
- `*bitmap`: zeroed first, so it is 0 on both errors; both errors log with
  `dev_err()`.
