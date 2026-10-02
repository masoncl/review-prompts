- Area-to-file mapping: a source file that has a header of its own shares
  its base name with it, for example
  `drivers/media/v4l2-core/v4l2-subdev.c` and
  `include/media/v4l2-subdev.h`, or
  `drivers/media/common/videobuf2/videobuf2-core.c` and
  `include/media/videobuf2-core.h`; under `drivers/media/mc/` the prefix
  `mc-` becomes `media-`, for example `drivers/media/mc/mc-entity.c` and
  `include/media/media-entity.h`.
- Control framework: four files in `drivers/media/v4l2-core/`,
  `v4l2-ctrls-core.c`, `v4l2-ctrls-api.c`, `v4l2-ctrls-request.c` and
  `v4l2-ctrls-defs.c`, with one header `include/media/v4l2-ctrls.h`.
- `v4l2-mc.c` (header `include/media/v4l2-mc.h`): V4L2 glue to the media
  controller; part of `videodev`, built only with `CONFIG_MEDIA_CONTROLLER`.
- `mc-dev-allocator.c` (header `include/media/media-dev-allocator.h`): added
  to `mc` only when `CONFIG_USB` is set.
- `frame_vector.c` (header `include/media/frame_vector.h`): linked into
  `videobuf2-common` together with `videobuf2-core.c`.
- Private headers, not under `include/media/`:
  `drivers/media/v4l2-core/v4l2-ctrls-priv.h` and
  `drivers/media/v4l2-core/v4l2-subdev-priv.h`.
- `__v4l2_async_register_subdev_sensor()`: declared in
  `include/media/v4l2-async.h`, defined in `v4l2-fwnode.c`, so a caller needs
  `CONFIG_V4L2_FWNODE`, not only `CONFIG_V4L2_ASYNC`.
- `v4l2_create_fwnode_links()` and `v4l2_create_fwnode_links_to_pad()`: in
  `v4l2-mc.c` and `include/media/v4l2-mc.h`, not in the fwnode files.
- `v4l2_async_register_subdev()` and `v4l2_async_register_subdev_sensor()`:
  macros in `include/media/v4l2-async.h` that pass `THIS_MODULE` to the
  double-underscore functions.
- Separate objects in `drivers/media/v4l2-core/Makefile` that are easy to
  miss: `v4l2-isp.o` under `CONFIG_V4L2_ISP`, and `v4l2-dv-timings.o`, built
  with `CONFIG_VIDEO_DEV` but not part of `videodev`.
