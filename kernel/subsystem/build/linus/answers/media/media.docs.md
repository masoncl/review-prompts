- Request API, kernel side: there is no request-api.rst under
  `Documentation/driver-api/media/`; `mc-core.rst` only includes the
  kernel-doc of `include/media/media-request.h`, with no prose.
- Request API, authority:
  `Documentation/userspace-api/media/mediactl/request-api.rst`.
- Sub-device active and try state: section "Centrally managed subdev active
  state" of `Documentation/driver-api/media/v4l2-subdev.rst`.
- Streams and routing: the section in `v4l2-subdev.rst` is one paragraph; the
  rules are in `Documentation/userspace-api/media/v4l/dev-subdev.rst`.
- `Documentation/driver-api/media/camera-sensor.rst`: clocks via
  `devm_v4l2_sensor_clk_get()`, runtime PM, no `.s_power()`, no
  `v4l2_ctrl_handler_setup()` in `runtime_resume`, rotation.
- `Documentation/userspace-api/media/drivers/camera-sensor.rst`: exists; it
  holds the blanking and frame-interval rules (`V4L2_CID_HBLANK`,
  `V4L2_CID_VBLANK`, `V4L2_CID_PIXEL_RATE`) and the flip-control rules.
- `Documentation/driver-api/media/tx-rx.rst`: describes streaming control
  with `.enable_streams()` and `.disable_streams()`, called only through
  `v4l2_subdev_enable_streams()` and `v4l2_subdev_disable_streams()`; it does
  not mention `.s_stream()`.
- `tx-rx.rst` on link frequency: a transmitter without a user-configurable
  link frequency reports it in `link_freq` of `.get_mbus_config()`, not
  through a control.
- `Documentation/driver-api/media/v4l2-videobuf2.rst`: three kernel-doc
  directives and no prose; the rules are the comments in
  `include/media/videobuf2-core.h`, `include/media/videobuf2-v4l2.h` and
  `include/media/videobuf2-memops.h`.
- Submission rules: sections "Media development workflow" and "Submit
  Checklist Addendum" of
  `Documentation/driver-api/media/maintainer-entry-profile.rst`. What the
  file requires:

| Requirement | What the file says |
|---|---|
| Compliance tools | `v4l2-compliance` for V4L2 drivers, `contrib/test/test-media` for V4L2 virtual drivers, `cec-compliance` for CEC drivers; they must pass |
| Static checks | built with `C=1 W=1` plus sparse and smatch; no new warnings without a very good reason |
| Style | `checkpatch.pl --strict --max-line-length=80`; exceptions allowed with a reason |
| Media CI | a patch moves on only if it passes, or the report is a false positive |
| API change | documentation updated in the same series |
| Devicetree bindings | Cc the Device Tree maintainers |

- The file does not ask for a warning-free documentation build, and does not
  name a test driver.
- Committers' rules: `Documentation/driver-api/media/media-committers.rst`;
  there is no media-committer.rst.
