- Models take `vb2_is_busy()` to mean "buffers are allocated now". It returns
  `q->is_busy`, cleared only by the free path of `vb2_core_reqbufs()` and by
  `vb2_core_queue_release()`; `vb2_core_remove_bufs()` leaves it set.
- Models take DV timings to have video-op forms. `struct
  v4l2_subdev_video_ops` has none; `s_dv_timings`, `g_dv_timings` and
  `query_dv_timings` are pad ops that take a pad number.
- Models take `v4l2_subdev_s_stream_helper()` to refuse several source pads.
  It uses the first source pad it finds; it returns `-ENOIOCTLCMD` when the
  stream ops are missing and `-EINVAL` when there is no source pad.
- Models take a sub-device node open to pin only the sub-device module.
  `subdev_open()` also does `try_module_get()` on the owner of the media
  device's driver, when `sd->v4l2_dev->mdev` is set and the media device has
  a `dev`, and returns `-EBUSY` if that fails.
- Models take `Documentation/driver-api/media/camera-sensor.rst` to give a
  probe and remove runtime PM recipe. It names no runtime PM function for
  probe or remove; it says that runtime PM shall be enabled at probe time and
  disabled at remove time.
- Models name media_entity_remote_pad(). It does not exist; see
  `media_pad_remote_pad_first()` and `media_pad_remote_pad_unique()` in
  `drivers/media/mc/mc-entity.c`.
- Models expect `kzalloc(sizeof(*p), GFP_KERNEL)` in the core. This tree uses
  `kzalloc_obj()`, `kzalloc_objs()`, `kvzalloc_objs()` and `kvzalloc_flex()`
  from `include/linux/slab.h`.
