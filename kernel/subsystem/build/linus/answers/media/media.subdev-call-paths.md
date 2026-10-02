| Macro | Uses `v4l2_subdev_call_wrappers` |
|---|---|
| `v4l2_subdev_call()` | yes |
| `v4l2_subdev_call_state_active()` | yes |
| `v4l2_subdev_call_state_try()` | yes |
| `v4l2_device_call_all()` | no |
| `v4l2_device_call_until_err()` | no |
| `v4l2_device_mask_call_all()` | no |
| `v4l2_device_mask_call_until_err()` | no |

- The four `v4l2_device_` macros in `include/media/v4l2-device.h`: expand
  to `__v4l2_device_call_subdevs_p()` or
  `__v4l2_device_call_subdevs_until_err_p()`, which call
  `(sd)->ops->o->f` themselves. `__v4l2_device_call_subdevs()` and
  `__v4l2_device_call_subdevs_until_err()` expand to the same two.
- `v4l2_subdev_enable_streams()` and `v4l2_subdev_disable_streams()`: call
  through `v4l2_subdev_call()`. `enable_streams` has no wrapper entry; the
  `s_stream` fallback does go through `call_s_stream()`.
- Driver-private macros: read the expansion. For example `sensor_call()` in
  `drivers/media/platform/marvell/mcam-core.c` uses `v4l2_subdev_call()`;
  `ivtv_call_hw()` and `bttv_call_all()` use the `v4l2_device_` macros.
- **Potentially unsafe usage**: calling an operation that has a wrapper
  through one of the four `v4l2_device_` macros.
  - Unsafe: when a sub-device on the list reads the state it is given, or
    relies on the core's checks, or is queried with
    `v4l2_subdev_is_streaming()`. A NULL state stays NULL, `which`, pad and
    stream are unchecked, and `sd->s_stream_enabled` is not updated.
  - Safe: when the operation never reads its state argument and validates
    the pad itself, so it needs neither the state wrapper nor `check_pad()`,
    as `ak881x_fill_fmt()` in `drivers/media/i2c/ak881x.c` does.
- Searching for other direct calls: search for `->ops->pad->`,
  `->ops->video->` and the other group names followed by a call. Outside
  `drivers/media/v4l2-core/v4l2-subdev.c` this tree has such calls only in
  `drivers/media/usb/pvrusb2/`, all to `s_routing`, which has no wrapper.
- A second search: a driver that calls its own operation function by name;
  no wrapper runs and the caller supplies the state and lock.
