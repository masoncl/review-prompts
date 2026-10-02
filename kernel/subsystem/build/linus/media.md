# Media and V4L2 Subsystem

## Main structures

### Objects and how they relate

- `struct media_entity`: not always embedded in a `struct video_device` or a
  `struct v4l2_subdev`. `obj_type` `MEDIA_ENTITY_TYPE_BASE` marks the rest,
  for example the entities that `dvb_create_media_entity()` in
  `drivers/media/dvb-core/dvbdev.c` allocates.
- mem2mem node in the graph: `video_register_media_controller()` skips
  `VFL_DIR_M2M`. `v4l2_m2m_register_media_controller()` registers three
  entities instead: `&vdev->entity` as source, plus `proc` and `sink`
  embedded in `struct v4l2_m2m_dev`.
- mem2mem entities: all three get `MEDIA_ENTITY_TYPE_BASE`, so
  `is_media_entity_v4l2_video_device()` is false even for the one embedded
  in the `struct video_device`.
- `struct media_link`: three kinds, told apart by
  `link->flags & MEDIA_LNK_FL_LINK_TYPE`:

  | Kind | Ends | List it is on | Created by |
  |---|---|---|---|
  | data | `source` pad, `sink` pad | `links` of each entity | `media_create_pad_link()` |
  | interface | `intf`, `entity` | `links` of the interface | `media_create_intf_link()` |
  | ancillary | `gobj0`, `gobj1`, both entities | `links` of the primary entity | `media_create_ancillary_link()` |

- `struct media_pipeline`: a set of pads, not of entities.
  `media_pipeline_start()` takes a `struct media_pad` and sets `pad->pipe`
  on every pad it reaches.
- Pads of one entity: can be in different pipelines when the entity's
  `has_pad_interdep` op says they are independent.
  `media_entity_pipeline()` returns the pipe of the first pad that has one.
- `struct media_pipeline` storage, three choices: a driver's own object; the
  `pipe` member of `struct video_device`; or one that
  `media_pipeline_alloc_start()` allocates and `__media_pipeline_stop()`
  frees when `start_count` reaches zero.
- `media_pipeline_start()`: collects pads and calls `link_validate` on
  enabled links. It starts no hardware; the driver calls
  `v4l2_subdev_enable_streams()` or the `s_stream` op itself.
- `struct media_devnode`: this, not `struct media_device`, is `/dev/mediaN`.
  `__media_device_register()` allocates it; it has its own `struct device`
  and is freed in `media_devnode_release()` on the last put.
- `struct media_device`: has no reference count of its own.
- `v4l2_fh_add()` and `v4l2_fh_del()`: both take the `struct file` as well
  as the `struct v4l2_fh`; that is how they set and clear
  `file->private_data`.
- `struct v4l2_subdev_fh`: embeds a `struct v4l2_fh`, so subdev nodes use the
  same per-open object as video nodes.
- Subdev node: a separate `struct video_device` that
  `__v4l2_device_register_subdev_nodes()` allocates and stores in
  `sd->devnode`. The way back is `vdev_to_v4l2_subdev()`, which reads
  driver data, not `container_of()`.
- Subdev node in the graph: the `entity` member of that `struct video_device`
  is not registered; the interface link goes to `sd->entity`.
- `struct v4l2_device` reference count: `v4l2_device_register()` starts it
  at one for the driver, and each registered `struct video_device` takes one
  more.
- `v4l2_device_unregister()`: does not drop the driver's reference;
  `v4l2_device_put()` does. The `release` callback needs both the last node
  gone and that put.
- Active `struct v4l2_subdev_state`: exists only after
  `__v4l2_subdev_init_finalize()`, which the `v4l2_subdev_init_finalize()`
  macro calls. Otherwise `sd->active_state` is NULL and pad ops receive a
  NULL state for `V4L2_SUBDEV_FORMAT_ACTIVE`; see
  `subdev_ioctl_get_state()`.
- `struct v4l2_ctrl_handler` lock: the member is `lock`, which defaults to
  `_lock`. `ctrl_lock` is not a member of the handler.
- `struct vb2_v4l2_buffer`: embeds `struct vb2_buffer` as `vb2_buf`, and a
  driver's buffer struct embeds `struct vb2_v4l2_buffer`.
- Buffer allocation: vb2 allocates each buffer itself, `q->buf_struct_size`
  bytes in `__vb2_queue_alloc()`, and uses the start of it as the
  `struct vb2_buffer`.
- `struct v4l2_async_connection`: one connection, not one subdev. A subdev
  can hold several on `sd->asc_list`; `v4l2_async_connection_unique()`
  returns NULL unless there is exactly one.
- Async match: by fwnode or by I2C adapter and address, see
  `enum v4l2_async_match_type`.
- `struct v4l2_m2m_dev`: opaque to drivers, defined in
  `drivers/media/v4l2-core/v4l2-mem2mem.c`. It has a `kref`:
  `v4l2_m2m_put()` frees on the last reference, `v4l2_m2m_release()` frees
  at once.
- DVB, RC and CEC: of the three, only DVB adds objects to the media graph, in
  `drivers/media/dvb-core/dvbdev.c` under `CONFIG_MEDIA_CONTROLLER_DVB`.
  Nothing under `drivers/media/rc/` or `drivers/media/cec/` references graph
  objects.

## Where to look

**Core files**

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

**Authoritative documentation**

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

**Configuration symbols**

- MEDIA_CONTROLLER_REQUEST_API is not in this tree; the request stubs in
  `include/media/media-request.h` are keyed on `CONFIG_MEDIA_CONTROLLER`.
- `drivers/media/mc/`: `drivers/media/Makefile` enters it only when
  `CONFIG_MEDIA_CONTROLLER` is `y`; inside, `mc.o` is built on
  `CONFIG_MEDIA_SUPPORT`.
- `include/media/media-entity.h`: no configuration guard and no stubs; for
  example `media_entity_pads_init()` and `media_create_pad_link()` are
  defined only in `drivers/media/mc/mc-entity.c`.
- `CONFIG_VIDEO_V4L2_SUBDEV_API`: depends on `VIDEO_DEV && MEDIA_CONTROLLER`
  and has no prompt, so it is on only when something selects it, as
  `VIDEO_CAMERA_SENSOR` in `drivers/media/i2c/Kconfig` does.
- Members that exist only under a symbol; an initialiser or access outside
  the same guard breaks the build:

| Symbol | Guarded members |
|---|---|
| `CONFIG_MEDIA_CONTROLLER` | `entity`, `intf_devnode`, `pipe` in `struct video_device`; `entity` in `struct v4l2_subdev`; `link_validate` in `struct v4l2_subdev_pad_ops` |
| `CONFIG_VIDEO_V4L2_SUBDEV_API` | `state`, `client_caps` in `struct v4l2_subdev_fh` |
| `CONFIG_VIDEO_ADV_DEBUG` | `vidioc_g_register`, `vidioc_s_register`, `vidioc_g_chip_info` in `struct v4l2_ioctl_ops`; `g_register`, `s_register` in `struct v4l2_subdev_core_ops`; the op counters in `struct vb2_queue` and `struct vb2_buffer`, for example `cnt_queue_setup` and `cnt_buf_done` |
| `CONFIG_COMPAT` | `compat_ioctl32` in `struct v4l2_file_operations` and `struct v4l2_subdev_core_ops` |

- `mdev` in `struct v4l2_device` and `active_state` in `struct v4l2_subdev`:
  unconditional.
- Sub-device helpers in `include/media/v4l2-subdev.h`, none with a stub:

| Needs | Helpers |
|---|---|
| nothing | lock helpers, for example `v4l2_subdev_lock_state()` and `v4l2_subdev_lock_and_get_active_state()`; `v4l2_subdev_call()`; `v4l2_subdev_is_streaming()` |
| `CONFIG_MEDIA_CONTROLLER` | `v4l2_subdev_init_finalize()`, `v4l2_subdev_cleanup()`, `v4l2_subdev_link_validate()`, `v4l2_subdev_state_get_format()` and the crop, compose and interval accessors |
| both symbols | for example `v4l2_subdev_get_fmt()`, `v4l2_subdev_set_routing()`, `v4l2_subdev_enable_streams()`, `v4l2_subdev_s_stream_helper()`; everything between the inner guard and its `#endif` |

- There is no v4l2_subdev_get_try_format(), v4l2_subdev_get_try_crop() or
  v4l2_subdev_get_try_compose() here; `v4l2_subdev_state_get_format()` and
  its siblings do that job.
- Without `CONFIG_VIDEO_V4L2_SUBDEV_API`: `subdev_open()`, `subdev_close()`
  and `subdev_ioctl()` in `v4l2-subdev.c` return `-ENODEV`;
  `subdev_do_ioctl()` is not built.
- `v4l2_device_register_subdev_nodes()` and
  `v4l2_device_register_ro_subdev_nodes()` without
  `CONFIG_VIDEO_V4L2_SUBDEV_API`: return 0 and create no node.
- `include/media/media-request.h` stubs without `CONFIG_MEDIA_CONTROLLER`:
  `media_request_lock_for_access()` and `media_request_lock_for_update()`
  return `-EINVAL`; `media_request_object_bind()` returns 0;
  `media_request_object_find()` returns `NULL`.
- No stub without `CONFIG_MEDIA_CONTROLLER`: `v4l2_get_link_freq()` and
  `v4l2_get_active_data_lanes()` in `include/media/v4l2-common.h`;
  `v4l2_create_fwnode_links()` and `v4l2_create_fwnode_links_to_pad()` in
  `include/media/v4l2-mc.h`.
- `v4l2_m2m_register_media_controller()` without `CONFIG_MEDIA_CONTROLLER`:
  stub in `include/media/v4l2-mem2mem.h` returns 0.
- `VIDIOC_DBG_G_REGISTER` and `VIDIOC_DBG_S_REGISTER` with
  `CONFIG_VIDEO_ADV_DEBUG`: both return `-EPERM` without `CAP_SYS_ADMIN`, on
  video nodes (`v4l2-ioctl.c`) and on sub-device nodes (`subdev_do_ioctl()`);
  `VIDIOC_DBG_G_CHIP_INFO` has no capability check.
- `CONFIG_VIDEO_ADV_DEBUG` in
  `drivers/media/common/videobuf2/videobuf2-core.c`: counts each successful
  queue, buffer and memory op, and prints "unbalanced counters" when buffers
  are freed and paired ops differ.
- Without `CONFIG_VIDEO_V4L2_I2C` or `CONFIG_SPI`: stubs in
  `include/media/v4l2-common.h`; the new-subdev functions return `NULL`, the
  init functions do nothing, and `v4l2_i2c_subdev_addr()` returns
  `I2C_CLIENT_END`.
- `CONFIG_VIDEO_FIXED_MINOR_RANGES`: `__video_register_device()` maps the
  node number to the minor one to one inside a fixed range per type; without
  it the minor is the first free one and is independent of the node number.

## Video devices

**Release callback**

- `v4l2_device_release()` in `drivers/media/v4l2-core/v4l2-dev.c`: calls
  `vdev->release(vdev)`, then `v4l2_device_put()` last.
- `v4l2_device_put()` there: skipped when `v4l2_dev->release` is NULL, so a
  driver without that callback may free its `struct v4l2_device` from
  `vdev->release`; a driver with it must not.
- No file open and no other reference: `vdev->release` runs inside
  `video_unregister_device()`, from `device_unregister()`; the caller must
  not touch a vdev that its release frees.
- `vb2_video_unregister_device()`: holds its own reference across the
  unregister, so release runs at its final `put_device()` at the earliest.
- `struct v4l2_device` after unregister: `v4l2_release()` and
  `v4l2_device_release()` still read `vdev->v4l2_dev`, `v4l2_dev->mdev` and
  `v4l2_dev->release`; it must outlive the last close.
- `vdev->fops` after unregister: `v4l2_release()` calls
  `vdev->fops->release` on every close, under `mdev->req_queue_mutex` when
  `v4l2_device_supports_requests()` is true.
- **Unsafe usage**: `video_device_release_empty()` on a
  `struct video_device` whose memory is freed at a point not ordered after
  `v4l2_device_release()`, for example in the driver's remove path.
  - Safe: `video_device_release_empty()` with the container freed from
    `v4l2_dev->release`, as `gspca_release()` and `vivid_dev_release()` do;
    `v4l2_device_release()` drops the node's `struct v4l2_device` reference
    only after `vdev->release` returned.
  - Safe: a `vdev->release` that frees the container itself, as
    `v4l2_device_release_subdev_node()` in
    `drivers/media/v4l2-core/v4l2-device.c` does for its own allocation.

**Unregistering a video device**

- `video_unregister_device()`: does not call `cdev_del()`; the cdev, the
  `video_devices[]` slot and the node number stay taken until
  `v4l2_device_release()` runs at the last put.
- `v4l2_event_wake_all()`: called after the flag is cleared; wakes
  `fh->wait` of every `struct v4l2_fh` on `vdev->fh_list`, nothing else.
- `v4l2_ioctl()`: tests `video_is_registered()` with no lock held.
- `__video_do_ioctl()`: tests `video_is_registered()` again after taking the
  lock from `v4l2_ioctl_get_lock()` and returns `-ENODEV`.
- Holding one lock across `video_unregister_device()`: excludes only the
  ioctls that `v4l2_ioctl_get_lock()` maps to that lock, and only for
  drivers whose `unlocked_ioctl` reaches `__video_do_ioctl()`, as
  `video_ioctl2()` does.
- `v4l2_read()`, `v4l2_write()`, `v4l2_poll()`, `v4l2_mmap()`: one unlocked
  test before the driver op, no recheck under any lock.
- `v4l2_poll()` on an unregistered device:
  `EPOLLERR | EPOLLHUP | EPOLLPRI`.
- `v4l2_get_unmapped_area()`: `NULL` under `CONFIG_MMU`; otherwise `-ENOSYS`
  for a missing op is tested before registration, then `-ENODEV`.
- `v4l2_compat_ioctl32()` on an unregistered device: `-ENODEV`.
- `vb2_video_unregister_device()` in
  `drivers/media/common/videobuf2/videobuf2-v4l2.c`: after the unregister it
  calls `vb2_queue_release()` under `queue->lock` or `vdev->lock` and clears
  `queue->owner`; it WARNs when `vdev->queue` is NULL.

**Failed registration**

- `vdev->release`: runs on no failure path of `__video_register_device()`.
- `device_register()` failure: the core does not call `put_device()`; it
  goes straight to `cleanup`.
- `vdev->dev.release`: assigned `v4l2_device_release()` only after
  `device_register()` succeeded.
- Caller after any failure: frees the vdev itself exactly once, as
  `__v4l2_device_register_subdev_nodes()` does with `kfree(vdev)`.
- `fops` check: `-EINVAL` with `WARN_ON` when `vdev->fops`, `fops->open` or
  `fops->release` is NULL, before anything is reserved.
- `V4L2_FL_REGISTERED`: never set on a failure path.
- `video_unregister_device()` after a failed registration: returns early
  when `video_is_registered()` is false, frees nothing; the vdev memory must
  still exist.
- `v4l2_device_get()`: called only after `device_register()` succeeded; a
  failed registration holds no `struct v4l2_device` reference.
- `video_register_media_controller()` failure: ignored;
  `__video_register_device()` still sets `V4L2_FL_REGISTERED` and returns 0.

**Lifetime of the parent device**

- Holders other than the registered nodes: drivers call `v4l2_device_get()`
  directly for their own users, for example
  `drivers/media/usb/usbtv/usbtv-audio.c`.

| Function | Effect on the parent `struct device` |
|---|---|
| `v4l2_device_register()` | `get_device(dev)`; sets drvdata only if it is NULL |
| `v4l2_device_disconnect()` | clears drvdata if it points to `v4l2_dev`; `put_device()`; `v4l2_dev->dev = NULL`; returns at once if `dev` is already NULL |
| `v4l2_device_unregister()` | calls `v4l2_device_disconnect()`, so it drops the device reference if still held; then unregisters subdevs |

- `v4l2_device_register()` with empty `name`: reads `dev->driver->name`, so
  `dev` must be bound to a driver or `name` must be preset.
- `v4l2_device_unregister()`: returns at once when `name[0]` is 0, and sets
  `name[0]` to 0 at the end, so a second call does nothing.
- `v4l2_i2c_subdev_unregister()` and `v4l2_spi_subdev_unregister()`: called
  from `v4l2_device_unregister()`; both leave a client that has a firmware
  node registered.
- Hot-unplug order with `v4l2_dev->release` set: see `gspca_disconnect()`
  and `gspca_release()` in `drivers/media/usb/gspca/gspca.c`;
  `v4l2_device_unregister()` runs from the release callback, not from
  disconnect.

**Enabled ioctls**

- `vdev->valid_ioctls`: the only bitmap; there is no separate disable
  bitmap. Before registration a set bit means disabled, after it means
  valid.
- `determine_valid_ioctls()`: called only when `vdev->ioctl_ops` is set.
- Bitmap at registration: nothing clears `vdev->valid_ioctls` first; every
  stale set bit is treated as a disabled ioctl.
- Non-NULL op is not sufficient: buffer ioctls also need
  `V4L2_CAP_STREAMING`, format ioctls on `VFL_TYPE_VIDEO` need a video or
  meta capability in `device_caps`.
- Non-NULL op is not necessary: with `V4L2_CAP_IO_MC` on a video, VBI or
  metadata node the input ioctls (`vfl_dir` not `VFL_DIR_TX`) and the output
  ioctls (`vfl_dir` not `VFL_DIR_RX`) are enabled without ops;
  `VIDIOC_G_PRIORITY` and `VIDIOC_S_PRIORITY` always;
  `VIDIOC_DBG_G_CHIP_INFO`, `VIDIOC_DBG_G_REGISTER` and
  `VIDIOC_DBG_S_REGISTER` always under `CONFIG_VIDEO_ADV_DEBUG`.
- `VIDIOC_QUERYCAP`: enabled only when `vidioc_querycap` is set.
- Event ioctls: `VIDIOC_DQEVENT` and `VIDIOC_SUBSCRIBE_EVENT` follow
  `vidioc_subscribe_event`; no flag is involved.
- There is no V4L2_FL_USE_FH_PRIO in this tree.
- `v4l2_fh_init()` in `drivers/media/v4l2-core/v4l2-fh.c`: sets both
  priority bits in `vdev->valid_ioctls` at every open, so disabling them
  with `v4l2_disable_ioctl()` does not last past the first open.
- Control ioctls (`INFO_FL_CTRL`): `__video_do_ioctl()` lets them through
  with a clear bit when `vfh->ctrl_handler` is set; `v4l2_fh_init()` copies
  `vdev->ctrl_handler` there, so `v4l2_disable_ioctl()` on them has no
  effect for such a handle.
- Disabling `VIDIOC_G_SELECTION`: also leaves `VIDIOC_G_CROP` and
  `VIDIOC_CROPCAP` off; disabling `VIDIOC_S_SELECTION` leaves
  `VIDIOC_S_CROP` off.
- **Unsafe usage**: calling `v4l2_disable_ioctl()` after
  `video_register_device()`; it does `set_bit()`, so it cannot disable
  anything and marks an ioctl valid even when its op is NULL.
  - Safe: before registration, as `vivid_disable_unused_ioctls()` does ahead
    of `vivid_create_devnodes()`.
- **Unsafe usage**: assigning the whole `struct video_device` after
  `v4l2_disable_ioctl()`; the copy overwrites the disabled bits.
  - Safe: copy the template first, then disable, as `vdev_init()` in
    `drivers/media/pci/bt8xx/bttv-driver.c` does.

**Registering a video device**

- `vdev->fops`, `fops->open`, `fops->release`: mandatory;
  `__video_register_device()` WARNs and returns `-EINVAL` without them.
- `vdev->fops->owner`: read by `video_register_device()` and
  `video_register_device_no_warn()` before any check, and used as the cdev
  owner; a NULL `fops` is dereferenced there.
- Missing `vdev->release`: `__video_register_device()` WARNs and returns
  `-EINVAL`.
- Zeroed struct: required; the core uses `vdev->flags` and
  `vdev->valid_ioctls` without initialising them.
- First successful open: after `set_bit(V4L2_FL_REGISTERED)`, the last step
  of `__video_register_device()`, not after `cdev_add()` or
  `device_register()`.
- `videodev_lock`: held from before `device_register()` until the flag is
  set; `v4l2_open()` takes it, so an earlier open waits or gets `-ENODEV`.

## File handles

**File handle lifecycle**

- `v4l2_fh_init()`: leaves `fh->prio` at `V4L2_PRIORITY_UNSET`; `v4l2_fh_add()`
  raises it to `V4L2_PRIORITY_DEFAULT` through `v4l2_prio_open()`.
- `v4l2_fh_init()` writes neither `fh->m2m_ctx` nor `fh->navailable`;
  `v4l2_ioctl_get_lock()` and `v4l2_event_dequeue()` read them, so the handle
  must come from zeroed memory, as in `v4l2_fh_open()`.
- `v4l2_fh_init()` overwrites `fh->ctrl_handler` with `vdev->ctrl_handler`; a
  per-open handler is assigned after it.
- `v4l2_fh_open()` allocates with `kzalloc_obj(*fh)`, not a direct `kzalloc()`
  call.
- `v4l2_fh_add()` in `open`: the only ordering it needs is `v4l2_fh_init()`
  first, since it reads `fh->vdev`. It need not be the last step:
  `subdev_open()` in `drivers/media/v4l2-core/v4l2-subdev.c` adds right after
  init and on a later failure unwinds with `v4l2_fh_del()`, `v4l2_fh_exit()`,
  then `kfree()`.
- `v4l2_fh_del()` is what sets `filp->private_data = NULL`; after it
  `file_to_v4l2_fh()` returns `NULL`, so a `release` op fetches its context
  from the file before calling it.
- `v4l2_fh_exit()` sets `fh->vdev = NULL` and returns at once when it is
  already `NULL`; `v4l2_fh_del()` dereferences `fh->vdev`, so it cannot run
  after `v4l2_fh_exit()`.
- `vb2_fop_release()` and `_vb2_fop_release()` end in `v4l2_fh_release()`,
  which calls `kfree()` on the `struct v4l2_fh` pointer itself; they fit only
  a handle that is the start of its own allocation.

**Use of file handles**

- `struct v4l2_fh` is mandatory: after a successful `vdev->fops->open()`,
  `v4l2_open()` in `drivers/media/v4l2-core/v4l2-dev.c` tests
  `V4L2_FL_USES_V4L2_FH` in `vdev->flags`; if clear it hits `WARN_ON()`, calls
  `vdev->fops->release()`, drops the device reference and returns `-ENODEV`.
- `V4L2_FL_USES_V4L2_FH` is defined in `include/media/v4l2-dev.h` and set by
  `v4l2_fh_init()`, not by `v4l2_fh_add()`.
- The test in `v4l2_open()` is per device, not per file: the bit stays set
  once any open has called `v4l2_fh_init()` on that `struct video_device`, and
  `filp->private_data` is not examined.
- **Unsafe usage**: an `open` op that returns 0 without having called
  `v4l2_fh_add()` on the file; `__video_do_ioctl()` reads `vfh->prio` and
  `vfh->ctrl_handler` from `file_to_v4l2_fh()` with no `NULL` test, and
  `vb2_poll()` reads `fh->wait` the same way.
  - Safe: `v4l2_fh_init()` then `v4l2_fh_add()` before returning 0, as
    `v4l2_fh_open()` does; `v4l2_fh_add()` sets `filp->private_data`.
- `V4L2_FL_USES_V4L2_FH` is tested nowhere but `v4l2_open()`.

**Callback arguments**

- `priv` is `NULL`: every core call of a `struct v4l2_ioctl_ops` callback with
  a `(struct file *file, void *priv, ...)` prototype passes `NULL`, including
  `v4l_querycap()`, the `DEFINE_V4L_STUB_FUNC()` stubs and `vidioc_default`
  in `__video_do_ioctl()`.
- `__video_do_ioctl()` fetches the handle with `file_to_v4l2_fh()` for its own
  use only (lock choice, priority check, `vfh->ctrl_handler`); it does not
  hand it to the callback.
- `file_to_v4l2_fh()` in `include/media/v4l2-fh.h`: returns
  `filp->private_data` with no test of any flag and no `NULL` check.
- `vidioc_subscribe_event` and `vidioc_unsubscribe_event` are the exception in
  prototype: they take `struct v4l2_fh *fh` and no file; `v4l_subscribe_event()`
  and `v4l_unsubscribe_event()` pass `file_to_v4l2_fh(file)`.
- **Unsafe usage**: deriving the handle or the driver context from `priv` in a
  `struct v4l2_ioctl_ops` callback (`ctx = priv`, `container_of(priv, ...)`);
  `priv` is `NULL`, so a callback that dereferences it oopses.
  - Safe: derive it from `file`, as `file2ctx()` in
    `drivers/media/test-drivers/vim2m.c` does with
    `container_of(file_to_v4l2_fh(file), ...)`.
  - Safe: `container_of(fh, ...)` on the `struct v4l2_fh *fh` argument of a
    `vidioc_subscribe_event` callback, as `vicodec_subscribe_event()` does;
    that argument is the real handle.
  - Safe: a callback that forwards `priv` unread to another callback of the
    same driver, as `vidioc_s_fmt_vid_cap()` in
    `drivers/media/test-drivers/vim2m.c` does.

**Event queue**

- `fh->subscribed`: writers hold both `fh->subscribe_lock` (mutex) and
  `vdev->fh_lock`; `__v4l2_event_unsubscribe()` asserts both. The queue path
  takes only `vdev->fh_lock`.
- `v4l2_event_queue()`: tests no flag; it returns when `vdev` is `NULL` and
  otherwise walks `vdev->fh_list`.
- `vdev->fh_lock` and `vdev->fh_list` are initialised in
  `__video_register_device()`, not when the `struct video_device` is
  allocated.
- `replace` and `merge` of `struct v4l2_subscribed_event_ops` run inside
  `__v4l2_event_queue_fh()` under `vdev->fh_lock` with interrupts off, in the
  context of whoever queued the event; `add` and `del` run under
  `fh->subscribe_lock`, with `vdev->fh_lock` released.
- `fh->sequence`: incremented only after a subscription matched the type and
  id; an event with no subscription on that handle leaves it unchanged.
- Full queue with `sev->elems == 1`: `replace(old, new)` is called if set and
  the core then skips copying `ev->u`, so `replace` must leave the final
  payload in its first argument; `merge` is not called in this case.
- Full queue with `sev->elems` above 1: `merge(oldest, second_oldest)` is
  called if set; `replace` is not called.
- Full queue with no matching op: the oldest event of that subscription is
  dropped and the new one stored.
- **Unsafe usage**: calling `v4l2_event_dequeue()` with `nonblocking` 0 while
  `fh->vdev->lock` is set and the caller does not hold it; the function calls
  `mutex_unlock()` on it without testing that it is held.
  - Safe: from `v4l_dqevent()`; `__video_do_ioctl()` holds the mutex chosen by
    `v4l2_ioctl_get_lock()`, which is `vdev->lock` for `VIDIOC_DQEVENT`.
  - Safe: from `subdev_do_ioctl()`; `__v4l2_device_register_subdev_nodes()`
    leaves `vdev->lock` `NULL`, so `v4l2_event_dequeue()` skips the unlock,
    and `subdev_do_ioctl_lock()` takes `vdev->lock` whenever it is set.
  - Safe: with `nonblocking` nonzero, as `v4l_dqevent()` passes for an
    `O_NONBLOCK` file; `v4l2_event_dequeue()` returns before it touches
    `vdev->lock`.
- `v4l2_event_dequeue()` retakes `fh->vdev->lock` with `mutex_lock()` also
  when the wait was interrupted, so it returns `-ERESTARTSYS` with the lock
  held.

## Ioctl dispatch

**Locks taken by the dispatcher**

- `v4l2_ioctl_get_lock()` and the locking: both in
  `drivers/media/v4l2-core/v4l2-ioctl.c`; `__video_do_ioctl()` locks and
  unlocks. `v4l2_ioctl()` in `drivers/media/v4l2-core/v4l2-dev.c` takes no
  lock.
- Both mutexes that `__video_do_ioctl()` takes, `req_queue_mutex` and the
  lock from `v4l2_ioctl_get_lock()`: taken with
  `mutex_lock_interruptible()`; a signal gives `-ERESTARTSYS`.
- `req_queue_mutex` of `struct media_device`: taken first, for
  `VIDIOC_STREAMON`, `VIDIOC_STREAMOFF` and `VIDIOC_REQBUFS`, when
  `v4l2_device_supports_requests()` is true. The lock from
  `v4l2_ioctl_get_lock()` is taken second; unlock is in reverse order.
- Order of tests in `v4l2_ioctl_get_lock()`:
  1. `_IOC_NR(cmd) >= V4L2_IOCTLS` (private or unknown number): `vdev->lock`.
  2. `INFO_FL_QUEUE` ioctl and `vfh->m2m_ctx->q_lock` set: that lock.
  3. `INFO_FL_QUEUE` ioctl and `vdev->queue->lock` set: that lock.
  4. Otherwise `vdev->lock`.
- `INFO_FL_QUEUE` ioctls: search the `v4l2_ioctls` table for the flag;
  `VIDIOC_REMOVE_BUFS` is one of them.
- `m2m_ctx->q_lock`: `v4l2_m2m_ctx_init()` sets it to the output queue's
  lock and fails with `-EINVAL` if the capture queue uses another mutex.
- No per-ioctl opt-out: `struct video_device` has no `disable_locking`
  member, and there is no v4l2_disable_ioctl_locking() or
  V4L2_FL_LOCK_ALL_FOPS. An ioctl runs with no core lock only when the
  pointer chosen above is NULL and `req_queue_mutex` is not taken.
- Other file operations in `v4l2-dev.c`: `v4l2_release()` holds
  `req_queue_mutex` around the driver's `release` when requests are
  supported; the others hold no lock around the driver op. `vb2_fop_mmap()`
  takes neither `q->lock` nor `vdev->lock`.
- Sub-device nodes: `subdev_do_ioctl_lock()` in
  `drivers/media/v4l2-core/v4l2-subdev.c` takes `vdev->lock` if set, then
  the state lock, if the state is non-NULL, for the ioctls listed in
  `subdev_ioctl_get_state()`. It never takes `req_queue_mutex`.

**Copying arguments**

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

**Checks before the driver runs**

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

**32-bit compatibility**

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

**Changing the userspace API**

- Flag names: the table flags are `INFO_FL_PRIO`, `INFO_FL_CTRL`,
  `INFO_FL_QUEUE`, `INFO_FL_ALWAYS_COPY` and `INFO_FL_CLEAR()`; there is no
  INFO_FL_STD or INFO_FL_FUNC.
- `INFO_FL_CLEAR()`: zeroes everything after the named field, input fields
  included, not only `reserved`.
- Without `INFO_FL_CLEAR()`: reserved fields reach the handler as user space
  wrote them; `video_get_user()` rejects nothing. The handler or driver
  zeroes them, for example `v4l_reqbufs()` with `memset_after()`.
- `'V'` numbers: shared by `include/uapi/linux/videodev2.h` and
  `include/uapi/linux/v4l2-subdev.h`, since both node types use
  `video_usercopy()`.
  - `video_get_user()` and `check_array_args()` match on the full command
    value, so a `v4l2_ioctls` flag also applies on a sub-device node when
    the values are equal, as for `VIDIOC_SUBDEV_G_EDID` and `VIDIOC_G_EDID`.
  - A new command must not equal an existing one of the other header unless
    the argument handling is meant to be shared.
- New video ioctl, easy to miss:
  - number below `BASE_VIDIOC_PRIVATE`; `valid_ioctls` has that many bits;
  - `func` in `IOCTL_INFO()` is called with no NULL test;
  - `determine_valid_ioctls()` in `drivers/media/v4l2-core/v4l2-dev.c` must
    set the bit, or `__video_do_ioctl()` returns `-ENOTTY`.
- Command not in the table, also a known number with another size: goes to
  `vidioc_default` with no `valid_ioctls` test; the priority result is
  passed as an argument, not enforced.
- New sub-device ioctl, besides the `case` in `subdev_do_ioctl()`:
  - add it to `subdev_ioctl_get_state()` if it has `which`, or `state` is
    NULL;
  - zero `reserved`, and `stream` without `V4L2_SUBDEV_CLIENT_CAP_STREAMS`,
    by hand;
  - return `-EPERM` for a setter on `V4L2_FL_SUBDEV_RO_DEVNODE`, as the
    `VIDIOC_SUBDEV_S_FMT` case does when `which` is not
    `V4L2_SUBDEV_FORMAT_TRY`;
  - an array argument needs `check_array_args()`, and copy-back on error
    needs its own test in `video_usercopy()`.
- Media ioctls: the file is `drivers/media/mc/mc-device.c`; add with
  `MEDIA_IOC()` to `ioctl_info`.
  - `media_device_ioctl()` matches the full command; a resized struct gets
    `-ENOIOCTLCMD`.
  - It copies in all `_IOC_SIZE` bytes of a command with `_IOC_WRITE` and
    copies out only when the handler returned 0.
  - Reserved fields are zeroed by each handler, for example
    `media_device_enum_links()`.
  - Request ioctls are in `media_request_ioctl()` in
    `drivers/media/mc/mc-request.c`.

**Format negotiation contract**

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

## Sub-device registration

**Registering with a parent**

- Order in `__v4l2_device_register_subdev()`: `v4l2_ctrl_add_handler()`, then
  `media_device_register_entity()`, then `internal_ops->registered()`, then
  `sd->owner = module`, then the list insertion.
- `registered()`: runs with the entity already in the graph (when
  `v4l2_dev->mdev` is set), but with `sd` not yet on `v4l2_dev->subdevs`.
- `sd->name`: an empty name returns `-EINVAL`, in the same test as the NULL
  and already-registered checks.
- Module reference: taken on the `module` argument, not on `sd->owner`; not
  taken when `module` is the owner of the driver of `v4l2_dev->dev`
  (`sd->owner_v4l2_dev`).
- `v4l2_device_register_subdev()` macro in `include/media/v4l2-device.h`:
  passes the caller's `THIS_MODULE`.
- `v4l2_async_match_notify()` and the helpers in
  `drivers/media/v4l2-core/v4l2-i2c.c` and
  `drivers/media/v4l2-core/v4l2-spi.c`: pass `sd->owner`.
- Success overwrites `sd->owner` with `module`;
  `__v4l2_device_register_subdev_nodes()` later uses it as the cdev owner.
- Error path: unless `sd->owner_v4l2_dev` is set, calls `module_put()` on
  `sd->owner`, which is assigned from `module` only after `registered()` has
  succeeded.
- Error path: calls neither `internal_ops->unregistered()` nor
  `internal_ops->release()`.
- `v4l2_ctrl_add_handler()`: also fails registration with the parent
  handler's stored `error` when `sd->ctrl_handler` is set and
  `v4l2_dev->ctrl_handler` is already in error.

**Device nodes of sub-devices**

- `V4L2_FL_SUBDEV_RO_DEVNODE`: set by `__v4l2_device_register_subdev_nodes()`
  from its `read_only` argument, on every node that call creates.
- The read-only choice belongs to the bridge driver, per call; no sub-device
  flag selects it.
- `vdev->device_caps`: not set for a sub-device node;
  `__video_register_device()` exempts `VFL_TYPE_SUBDEV` from that check.
- `vdev->ctrl_handler`: copied from `sd->ctrl_handler` once, at node creation;
  if it is NULL, `__video_register_device()` substitutes
  `v4l2_dev->ctrl_handler`.
- Media interface: created inside `__video_register_device()` by
  `video_register_media_controller()`; `__v4l2_device_register_subdev_nodes()`
  only adds the link.
- Error path of `__v4l2_device_register_subdev_nodes()`: walks
  `v4l2_dev->subdevs` from the head and stops at the first sub-device whose
  `sd->devnode` is NULL, so nodes behind it stay registered.
- That error path also unregisters nodes that an earlier successful call
  created.
- Read-only tests: search `ro_subdev` in `subdev_do_ioctl()` in
  `drivers/media/v4l2-core/v4l2-subdev.c`; there are seven, all `-EPERM`, and
  none in `subdev_do_ioctl_lock()`.

| ioctl | Refused on a read-only node |
|---|---|
| `VIDIOC_SUBDEV_S_FMT`, `VIDIOC_SUBDEV_S_CROP`, `VIDIOC_SUBDEV_S_SELECTION`, `VIDIOC_SUBDEV_S_FRAME_INTERVAL`, `VIDIOC_SUBDEV_S_ROUTING` | when `which` is not `V4L2_SUBDEV_FORMAT_TRY` |
| `VIDIOC_SUBDEV_S_STD`, `VIDIOC_SUBDEV_S_DV_TIMINGS` | always |
| `VIDIOC_S_EDID`, `VIDIOC_SUBDEV_S_CLIENT_CAP`, `VIDIOC_S_CTRL`, `VIDIOC_S_EXT_CTRLS`, `VIDIOC_DBG_S_REGISTER`, anything passed to the `ioctl` core op | never |

- `VIDIOC_SUBDEV_S_FRAME_INTERVAL` from a client without
  `V4L2_SUBDEV_CLIENT_CAP_INTERVAL_USES_WHICH`: `subdev_ioctl_get_state()`
  forces `which` to `V4L2_SUBDEV_FORMAT_ACTIVE` first, so a read-only node
  always refuses it.

**Initialising a sub-device**

- `v4l2_subdev_init()`: does not clear `sd->internal_ops`, `sd->ctrl_handler`,
  `sd->state_lock`, `sd->active_state`, `sd->devnode`, `sd->owner` or
  `sd->dev`.
- Those fields are read later, for example `sd->devnode` by
  `__v4l2_device_register_subdev_nodes()` and `sd->state_lock` by
  `__v4l2_subdev_state_alloc()`, so the structure has to start zeroed.
- `sd->entity.function`: `v4l2_subdev_init()` sets it to
  `MEDIA_ENT_F_V4L2_SUBDEV_UNKNOWN`, and `media_device_register_entity()`
  warns if it still has that value.
- `media_entity_pads_init()` does not read `sd->entity.function`; the function
  only has to be set before registration.
- `__v4l2_subdev_init_finalize()` reads these, so all must be final before it
  is called:
  - `sd->ops`, for the stream-op checks
  - `sd->flags`, for `V4L2_SUBDEV_FL_STREAMS`
  - `sd->ctrl_handler`
  - `sd->state_lock`
  - `sd->entity.num_pads`
  - `sd->internal_ops`, for `init_state`
- `v4l2_subdev_cleanup()`: also frees the entries of
  `sd->async_subdev_endpoint_list`, so it is needed after
  `v4l2_async_subdev_endpoint_add()` even without an active state.
- `v4l2_subdev_cleanup()` on a zeroed `sd` that never went through
  `v4l2_subdev_init()`: valid, it returns after the state free.
- `media_entity_cleanup()`: an empty inline in `include/media/media-entity.h`,
  so its place in the removal order changes nothing.
- `v4l2_subdev_cleanup()` and `v4l2_ctrl_handler_free()`: the core imposes no
  order between them; `__v4l2_subdev_state_free()` destroys only
  `state->_lock` and never touches `sd->state_lock`.

**Unregistering and freeing**

- `v4l2_subdev_release()`: static in `drivers/media/v4l2-core/v4l2-device.c`,
  with two callers, `v4l2_device_unregister_subdev()` when there is no node
  and `v4l2_device_release_subdev_node()` when there is.
- With a node, `release` is driven by the `struct device` inside
  `struct video_device`, through `v4l2_device_release()` in
  `drivers/media/v4l2-core/v4l2-dev.c`; the media entity plays no part.
- `v4l2_device_unregister_subdev()` on a sub-device with `sd->v4l2_dev` NULL:
  returns at once, so neither `unregistered` nor `release` runs.
- A sub-device that was never registered, or whose registration failed, never
  gets `release`; memory freed only from `release` is then not freed.
- `v4l2_subdev_release()`: reads `sd->owner` and `sd->owner_v4l2_dev` before
  it calls `internal_ops->release()`.
- `v4l2_device_unregister()`: reads `sd->flags` after
  `v4l2_device_unregister_subdev()` has returned, which for a sub-device
  without a node is after `release`.
- `sd->active_state`: not read by `subdev_close()` or `v4l2_subdev_release()`.
- After unregistration `subdev_do_ioctl_lock()` returns `-ENODEV` before
  `subdev_ioctl_get_state()` runs, so the core does not need
  `v4l2_subdev_cleanup()` to wait for `release`.
- In-flight ioctls: `video_unregister_device()` does not wait for an ioctl
  that has already passed the `video_is_registered()` test, and sub-device
  nodes have no `vdev->lock`.
- **Potentially unsafe usage**: freeing the memory that holds the
  `struct v4l2_subdev` when `v4l2_device_unregister_subdev()` returns, by
  `kfree()` in `remove()` or by devres.
  - Unsafe: when a node was registered (`sd->devnode` set) and a file handle
    is still open; `subdev_close()` reads `sd->internal_ops`, and
    `v4l2_subdev_release()` then reads and writes `sd`.
  - Safe: when no node was ever registered for `sd`, because
    `v4l2_device_unregister_subdev()` calls `v4l2_subdev_release()` before it
    returns; `tuner_remove()` in `drivers/media/v4l2-core/tuner-core.c` frees
    right after it.

## Calling sub-device operations

**Calling an operation**

- `sd->ops` NULL: not tested; `v4l2_subdev_call()` dereferences `__sd->ops`.
  `v4l2_subdev_init()` in `drivers/media/v4l2-core/v4l2-subdev.c` does
  `BUG_ON(!ops)`.
- `CONFIG_MEDIA_CONTROLLER`: changes nothing in `v4l2_subdev_call()`; the
  macro takes no module or entity reference.
- NULL `sd` in the sibling macros: only `v4l2_subdev_call()` tolerates it.
  `v4l2_subdev_call_state_active()` reads `sd->active_state` and
  `v4l2_subdev_call_state_try()` reads `sd->state_lock` before the NULL test
  runs; `v4l2_subdev_has_op()` dereferences `sd` too.
- `-ENOIOCTLCMD` returned from an ioctl handler: `video_usercopy()` in
  `drivers/media/v4l2-core/v4l2-ioctl.c` turns it into `-ENOTTY`, so
  `subdev_do_ioctl()` can return the result of `v4l2_subdev_call()`
  unchanged, as it does for example for `VIDIOC_SUBDEV_G_FMT`.
- `-ENOIOCTLCMD` on any other path (probe, streaming start, notifier):
  `v4l2_subdev_call()` does not convert it; the caller filters or maps it, as
  `v4l2_get_link_freq()` does with `ret < 0 && ret != -ENOIOCTLCMD`.
- `-ENOIOCTLCMD` does not prove that the operation is missing: an implemented
  operation can return the same code, for example
  `v4l2_subdev_s_stream_helper()` returns `-ENOIOCTLCMD`.

**Operation wrappers**

- `v4l2_subdev_call_wrappers`: a `struct v4l2_subdev_ops` with only `.pad`
  and `.video` set; the members are in `v4l2_subdev_call_pad_wrappers` and
  `v4l2_subdev_call_video_wrappers`.
- Easy to miss in the pad table: `s_dv_timings`, `g_dv_timings` and
  `query_dv_timings` are wrapped; `set_routing`, `enable_streams`,
  `disable_streams`, `set_frame_desc` and `link_validate` are not.
- `DEFINE_STATE_WRAPPER`: instantiated for seven operations (formats,
  selections, the three enumerations). `get_frame_interval` and
  `set_frame_interval` are installed as `call_get_frame_interval()` and
  `call_set_frame_interval()`, so a NULL state stays NULL for them.
- State lock: the state wrapper locks only when the caller passed NULL and
  `sd->active_state` exists. With a non-NULL state it does not lock; the lock
  is asserted only for a sub-device with `V4L2_SUBDEV_FL_STREAMS`, by
  `__v4l2_subdev_state_get_format()` under `check_state()`.
- NULL state, no active state: the driver receives NULL; `check_state()`
  lets it through for `V4L2_SUBDEV_FORMAT_ACTIVE` and `stream` 0 on a
  sub-device without `V4L2_SUBDEV_FL_STREAMS`.
- Without `CONFIG_MEDIA_CONTROLLER`: the state wrapper only forwards, so a
  NULL state is not replaced.
- `call_s_stream()` on a failed stop: logs, returns 0, and still clears
  `sd->s_stream_enabled` and the privacy LED.
- `call_get_frame_desc()`: returns `-EOPNOTSUPP` for a pad without
  `MEDIA_PAD_FL_SOURCE` under `CONFIG_MEDIA_CONTROLLER`. It does not call
  `check_pad()`; it indexes `sd->entity.pads[pad]` with the caller's value.
- `call_get_mbus_config()`: zeroes `*config` before `check_pad()`. When the
  operation is missing the wrapper does not run and nothing is zeroed.
- **Unsafe usage**: under `CONFIG_MEDIA_CONTROLLER`, passing a NULL state to
  one of the seven state-wrapped operations while holding the lock of the
  active state of that sub-device; the wrapper calls `mutex_lock()` on it
  again. With `sd->state_lock` set, `__v4l2_subdev_state_alloc()` gives every
  state of the sub-device that one lock, so a locked try state is the same
  case.
  - Safe: pass the state that is already locked, as
    `v4l2_subdev_link_validate_get_format()` does with
    `v4l2_subdev_get_locked_active_state()` when `states_locked` is true; the
    wrapper calls `v4l2_subdev_lock_and_get_active_state()` only for a NULL
    state.

**Paths to an operation**

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

**State, pad and stream checks**

- NULL argument pointer: `-EINVAL` before any other check, in the wrappers
  that call `check_state()`.
- `check_pad()`: bounds by `sd->entity.num_pads` only under
  `CONFIG_MEDIA_CONTROLLER` and when `num_pads` is not 0; otherwise only
  pad 0 passes.
- `check_state()` on a sub-device with `V4L2_SUBDEV_FL_STREAMS`: passes only
  if `v4l2_subdev_state_get_format()` finds an entry for the pad and stream
  in the state. `which` is not consulted.
- NULL state on a sub-device with `V4L2_SUBDEV_FL_STREAMS`:
  `__v4l2_subdev_state_get_format()` hits `WARN_ON_ONCE(!state)` and the
  check returns `-EINVAL`.
- `CONFIG_VIDEO_V4L2_SUBDEV_API` in `check_state()`: matters only inside the
  `V4L2_SUBDEV_FL_STREAMS` branch, where without it every call returns
  `-EINVAL`. It does not affect `V4L2_SUBDEV_FORMAT_TRY` on a sub-device
  without the flag.
- `V4L2_SUBDEV_FORMAT_ACTIVE` without `V4L2_SUBDEV_FL_STREAMS`: a NULL
  state passes `check_state()` when `stream` is 0.
- `v4l2_subdev_enable_streams_api`: not consulted; `check_state()` tests
  `sd->flags` only.

**Sub-device node ioctls**

- `vdev->lock`: `__v4l2_device_register_subdev_nodes()` in
  `drivers/media/v4l2-core/v4l2-device.c` allocates the
  `struct video_device` zeroed and never sets `lock`, so for a node the core
  creates only the state lock is taken.
- Order in `subdev_do_ioctl_lock()`: `vdev->lock` if set (interruptible),
  then the state lock with `v4l2_subdev_lock_state()` (not interruptible),
  only if the state is non-NULL.
- Try state: `subdev_fh->state` in `struct v4l2_subdev_fh`, allocated in
  `subdev_open()`; there is no `state` member in `struct v4l2_fh`.
- `which` other than `V4L2_SUBDEV_FORMAT_TRY`: any value selects the active
  state in `subdev_ioctl_get_state()`; `check_which()` rejects a bad value
  later, in the wrapper (not for the routing ioctls, which have none).
- `v4l2_subdev_enable_streams_api`: a `static bool` in
  `drivers/media/v4l2-core/v4l2-subdev.c` that nothing assigns.
  `VIDIOC_SUBDEV_S_CLIENT_CAP` therefore strips
  `V4L2_SUBDEV_CLIENT_CAP_STREAMS`, and `subdev_do_ioctl()` zeroes `stream`
  for every client.
- `VIDIOC_SUBDEV_G_ROUTING`: never calls the driver; it copies from the
  state with `v4l2_subdev_copy_routes()`.

**Frame interval operations**

- `struct v4l2_subdev_video_ops`: has no frame interval member; there are no
  g_frame_interval or s_frame_interval ops in this tree.
- `call_get_frame_interval()` and `call_set_frame_interval()`: only run
  `check_frame_interval()`; they never write `which` and never replace a
  NULL state (see "Operation wrappers").
- Ioctl path: `subdev_ioctl_get_state()` overwrites `fi->which` with
  `V4L2_SUBDEV_FORMAT_ACTIVE` when the file handle lacks
  `V4L2_SUBDEV_CLIENT_CAP_INTERVAL_USES_WHICH`, before it picks the state,
  so the state and the driver both see the forced value.
- `V4L2_SUBDEV_CLIENT_CAP_INTERVAL_USES_WHICH`: accepted by
  `VIDIOC_SUBDEV_S_CLIENT_CAP` regardless of
  `v4l2_subdev_enable_streams_api`.
- `v4l2_g_parm_cap()` and `v4l2_s_parm_cap()` in
  `drivers/media/v4l2-core/v4l2-common.c`: call through
  `v4l2_subdev_call_state_active()`, which passes the active state locked,
  or NULL when the sub-device has none.
- **Unsafe usage**: an in-kernel call of `get_frame_interval` or
  `set_frame_interval` with `which` left at 0. 0 is
  `V4L2_SUBDEV_FORMAT_TRY`; on a sub-device without `V4L2_SUBDEV_FL_STREAMS`
  `check_state()` returns `-EINVAL` for it when the state is NULL or has no
  `pads`, and drivers such as `ov7670_get_frame_interval()` return `-EINVAL`
  for anything but `V4L2_SUBDEV_FORMAT_ACTIVE`.
  - Safe: set `which` to `V4L2_SUBDEV_FORMAT_ACTIVE` before the call, as
    `subdev_ioctl_get_state()` does for a client without the capability.

## Sub-device state

**Active state and try state**

- `__v4l2_subdev_state_alloc()`: takes no lock argument; `lock_name` and
  `lock_key` only name `state->_lock` for lockdep. `state->lock` is
  `sd->state_lock` when that is non-NULL, else `&state->_lock`.
- `state->pads`: allocated only when `V4L2_SUBDEV_FL_STREAMS` is clear and
  `sd->entity.num_pads` is non-zero; NULL otherwise.
- `init_state` for the active state: runs before
  `__v4l2_subdev_init_finalize()` stores `sd->active_state`, so
  `sd->active_state` is NULL and the active-state getters return NULL inside
  it. Only the `state` argument is usable.
- Sub-device with no active state: still gets a try state per open, with
  `pads` and the `init_state` call on the same conditions as for an active
  state; `subdev_fh_init()` does not test `sd->active_state`.
- `v4l2_subdev_call_state_try()` in `include/media/v4l2-subdev.h`: a third
  allocator; allocates a state, locks it, calls one op, frees it.
- Direct driver calls to `__v4l2_subdev_state_alloc()`: a few exist, each
  under a FIXME comment; search for the name. `vsp1_entity_init()` keeps its
  state in `entity->state`, and `sd->active_state` stays NULL.
- `CONFIG_MEDIA_CONTROLLER`: `__v4l2_subdev_state_alloc()`,
  `__v4l2_subdev_state_free()`, `__v4l2_subdev_init_finalize()` and
  `v4l2_subdev_cleanup()` are compiled only with it.
- `CONFIG_VIDEO_V4L2_SUBDEV_API`: `subdev_fh_init()` and the per-open try
  state exist only with it; without it `subdev_open()` returns `-ENODEV`.
- **Unsafe usage**: implementing the `enable_streams` or `disable_streams`
  pad op, or setting `V4L2_SUBDEV_FL_STREAMS`, without an active state.
  `v4l2_subdev_enable_streams()` and `v4l2_subdev_disable_streams()` unlock
  the result of `v4l2_subdev_lock_and_get_active_state()` with no NULL test;
  `v4l2_subdev_has_pad_interdep()` dereferences it the same way.
  `__v4l2_subdev_init_finalize()` is not what enforces this; nothing does.
  - Safe: call `v4l2_subdev_init_finalize()` before registering, as
    `imx219_probe()` in `drivers/media/i2c/imx219.c` does.
  - Safe: no active state, with only `s_stream` and without
    `V4L2_SUBDEV_FL_STREAMS`; `v4l2_subdev_enable_streams()` then passes
    `state = NULL` and never locks.

**State accessors**

- NULL state: `__v4l2_subdev_state_get_format()`,
  `__v4l2_subdev_state_get_crop()` and `__v4l2_subdev_state_get_compose()`
  return NULL after `WARN_ON_ONCE()`; `__v4l2_subdev_state_get_interval()`
  uses `WARN_ON()`, so it warns on every call.
- Missing pad or stream: returns NULL silently on both paths; no warning.
- `lockdep_assert_held(state->lock)`: format, crop and compose assert only
  on the streams path, after the `pads` branch has returned;
  `__v4l2_subdev_state_get_interval()` asserts before the `pads` branch, so
  for every non-NULL state.
- Streams state: entries exist only for the two ends of each route with
  `V4L2_SUBDEV_ROUTE_FL_ACTIVE`; `v4l2_subdev_init_stream_configs()` builds
  them from `for_each_active_route()`. A pad and stream that only inactive
  routes use returns NULL.
- New streams state: holds no entries until `init_state` calls
  `v4l2_subdev_set_routing()`; until then every accessor returns NULL.
- Ops with no wrapper entry, for example `set_routing`: `v4l2_subdev_call()`
  passes the state as given, NULL included.

**Locking a state**

- `v4l2_subdev_get_unlocked_active_state()`: calls
  `lockdep_assert_not_held()` on the active state's lock when the state is
  non-NULL.
- `sd->state_lock`: the core never sets it and there is no
  _synthetic_state_lock field; `v4l2_subdev_init()` does not write it. NULL
  means each state uses its own `_lock`.
- Try states: use `sd->state_lock` too. Every state allocated while it is
  set shares it, including the one from `v4l2_subdev_call_state_try()`.
- With a shared lock, `v4l2_subdev_get_unlocked_active_state()` trips
  lockdep whenever the caller holds that mutex for any reason, for example
  with a try state locked, or inside `s_ctrl` when the mutex is also the
  control handler's lock.
- `v4l2_ctrl_handler_init()`: is what sets the `lock` field of
  `struct v4l2_ctrl_handler`. Assigning `sd->state_lock` from it earlier
  copies NULL, and each state silently gets its own lock.
- Driver mutex as the one lock: overwrite the handler's `lock` after
  `v4l2_ctrl_handler_init()`, and point `sd->state_lock` at the same mutex;
  see `ccs_init_controls()` and `ccs_init_subdev()` in
  `drivers/media/i2c/ccs/ccs-core.c`.
- `v4l2_subdev_enable_streams()` and `v4l2_subdev_disable_streams()`: lock
  the active state and pass it locked to the op; the op must not lock it
  again.
- `call_s_stream()`: locks nothing; an `s_stream` op locks the active state
  itself.
- `subdev_do_ioctl_lock()`: locks only a non-NULL state; an op of a
  sub-device with no active state runs with no state lock held for
  `V4L2_SUBDEV_FORMAT_ACTIVE`.
- `v4l2_subdev_lock_states()`: its only caller is
  `v4l2_subdev_link_validate()`, with the active states of the sink and
  source sub-devices, and only when both are non-NULL. The pointer compare
  covers two sub-devices on one mutex.
- **Unsafe usage**: with `sd->state_lock` equal to the control handler's
  lock, calling a control helper that takes it through `v4l2_ctrl_lock()`
  (for example `v4l2_ctrl_s_ctrl()`, `v4l2_ctrl_modify_range()`,
  `v4l2_ctrl_grab()`) or `v4l2_ctrl_handler_setup()` while the state is
  locked: in a pad op that takes a state, called by the core, in
  `enable_streams`, in `init_state`. The mutex is taken twice by one task.
  - Safe: the unlocked variants, as `imx219_set_pad_format()` does with
    `__v4l2_ctrl_modify_range()` and `__v4l2_ctrl_s_ctrl()`, and
    `imx219_enable_streams()` with `__v4l2_ctrl_handler_setup()`;
    `__v4l2_ctrl_handler_setup()` asserts the lock is held.
  - Safe: the locking helpers where the state is not locked, as
    `imx214_ctrls_init()` does through `imx214_pll_update()` in probe,
    before `v4l2_subdev_init_finalize()`.
- **Unsafe usage**: with the same shared lock, calling
  `v4l2_subdev_lock_and_get_active_state()` inside `s_ctrl`; the control
  framework already holds the handler lock there.
  - Safe: `v4l2_subdev_get_locked_active_state()`, as `imx219_set_ctrl()`
    does.

## Streams and routing

**Streams API availability**

- `v4l2_subdev_enable_streams_api`: `static bool` in
  `drivers/media/v4l2-core/v4l2-subdev.c`, under
  `CONFIG_VIDEO_V4L2_SUBDEV_API`; nothing assigns it and there is no
  `module_param()` for it, so it is false unless the source is edited.
- Userspace result while it is false: `subdev_do_ioctl()` returns
  `-ENOIOCTLCMD` for both routing ioctls, which `video_usercopy()` in
  `drivers/media/v4l2-core/v4l2-ioctl.c` turns into `-ENOTTY`.
- Three gates on the routing ioctls, in order: the variable
  (`-ENOIOCTLCMD`), `V4L2_SUBDEV_FL_STREAMS` in `sd->flags`
  (`-ENOIOCTLCMD`), `V4L2_SUBDEV_CLIENT_CAP_STREAMS` in the file handle's
  `client_caps` (`-EINVAL`).
- `__v4l2_subdev_init_finalize()`: does not read the variable; in-kernel
  routing, stream configs and `v4l2_subdev_enable_streams()` work with the
  variable false.
- Enforced by the core for a `V4L2_SUBDEV_FL_STREAMS` sub-device: only the
  two `-EINVAL` tests in `__v4l2_subdev_init_finalize()`. A streams
  sub-device with neither `s_stream` nor `enable_streams` passes.
- `set_routing`: optional; without it `VIDIOC_SUBDEV_S_ROUTING` copies the
  current table back and returns 0.
- `init_state`: not checked; without a routing installed there, the state
  has no stream configs and `check_state()` returns `-EINVAL` for every
  pad/stream.
- **Unsafe usage**: calling `v4l2_subdev_enable_streams()` or
  `v4l2_subdev_disable_streams()` on a `V4L2_SUBDEV_FL_STREAMS` sub-device
  that lacks `enable_streams`/`disable_streams`; the state pointer is NULL
  on that path and `v4l2_subdev_collect_streams()` dereferences it.
  - Safe: the sub-device implements both ops and has an active state from
    `v4l2_subdev_init_finalize()`, as `ub913_enable_streams()` and
    `ub913_subdev_init()` in `drivers/media/i2c/ds90ub913.c`; the state is
    then locked and passed.

**Setting a routing table**

- Core checks before `set_routing`, in order:

  | Check | Result |
  |---|---|
  | `len_routes > 256`, in `check_array_args()` | `-E2BIG` |
  | `v4l2_subdev_enable_streams_api` false | `-ENOIOCTLCMD` |
  | no `V4L2_SUBDEV_FL_STREAMS` | `-ENOIOCTLCMD` |
  | no `V4L2_SUBDEV_CLIENT_CAP_STREAMS` on the file handle | `-EINVAL` |
  | `which` not `V4L2_SUBDEV_FORMAT_TRY` on a read-only node | `-EPERM` |
  | `num_routes > len_routes` | `-EINVAL` |
  | a stream id above `V4L2_SUBDEV_MAX_STREAM_ID` (63) | `-EINVAL` |
  | pad out of range or wrong direction | `-EINVAL` |
  | active routes above `V4L2_FRAME_DESC_ENTRY_MAX` | `-E2BIG` |

- `which`: not validated for routing; `check_which()` is not called, and
  any value other than `V4L2_SUBDEV_FORMAT_TRY` selects the active state in
  `subdev_ioctl_get_state()`.
- Streaming: the core makes no test; `-EBUSY` comes only from the driver's
  `set_routing`.
- `v4l2_subdev_routing_validate()`: called only by drivers, never by the
  core.
- `v4l2_subdev_routing_validate()` on a violation: returns `-ENXIO`, not
  `-EINVAL`; `-ENOMEM` if its scratch array cannot be allocated.
- `v4l2_subdev_routing_validate()`: walks every route, inactive ones
  included, so an inactive route can violate a restriction.
- `v4l2_subdev_routing_validate()` with `disallow` 0: checks pad index and
  direction only; duplicate ends pass.
- `v4l2_subdev_set_routing()`: takes no format argument and does not
  validate the routes; only `v4l2_subdev_set_routing_with_fmt()` takes a
  format.
- `v4l2_subdev_set_routing_with_fmt()`: writes `fmt` only; crop, compose
  and interval of every stream config stay zero.
- Old stream configs: the whole array is replaced by a new one, zeroed
  except for `pad` and `stream`, so the `enabled` flag of every stream is
  cleared along with the formats.
- **Unsafe usage**: on a state of a `V4L2_SUBDEV_FL_STREAMS` sub-device,
  using a pointer from `v4l2_subdev_state_get_format()` (or the crop,
  compose, interval accessors) taken before `v4l2_subdev_set_routing()`;
  `v4l2_subdev_init_stream_configs()` frees the old array.
  - Safe: fetch the pointer after the call, as `_ub913_set_routing()` in
    `drivers/media/i2c/ds90ub913.c` does.
- **Potentially unsafe usage**: `v4l2_subdev_set_routing()` on the active
  state.
  - Unsafe: while streams are enabled; `enabled` is lost, so
    `v4l2_subdev_is_streaming()` reports false and
    `v4l2_subdev_disable_streams()` returns `-EALREADY` or `-EINVAL`
    without calling the op.
  - Safe: the driver returns `-EBUSY` first for
    `V4L2_SUBDEV_FORMAT_ACTIVE` while streaming, as
    `mxc_isi_crossbar_set_routing()` does with
    `media_entity_is_streaming()`.

**Lookups through the routing table**

- `v4l2_subdev_routing_find_opposite_end()`: returns an `int`, `-EINVAL`
  when no route matches; `other_pad` and `other_stream` are left unwritten.
- `v4l2_subdev_routing_find_opposite_end()`: does not test
  `V4L2_SUBDEV_ROUTE_FL_ACTIVE`; it returns the first route in table order
  with a matching end, so an inactive route can hide a later active one.
- `v4l2_subdev_state_get_opposite_stream_format()`: same route match,
  inactive included; the result for an inactive route is `NULL` unless an
  active route has the same opposite pad/stream.
- `v4l2_subdev_state_xlate_streams()`: the only one of the three that uses
  `for_each_active_route()`.
- `v4l2_subdev_state_xlate_streams()`: overwrites `*streams` with the
  subset that had a route; with no match it returns 0 and sets `*streams`
  to 0.

**Enabling and disabling streams**

- There is no v4l2_subdev_enable_streams_fallback() here; the `s_stream`
  fallback is inline in `v4l2_subdev_enable_streams()` and
  `v4l2_subdev_disable_streams()`, chosen when the op is absent.
- Returns of `v4l2_subdev_enable_streams()`, in order:

  | Request | Return |
  |---|---|
  | `pad >= sd->entity.num_pads` | `-EINVAL` |
  | pad lacks `MEDIA_PAD_FL_SOURCE` | `-EOPNOTSUPP` |
  | pad index 64 or above | `-EOPNOTSUPP` |
  | `streams_mask` is 0 | 0, nothing done |
  | a requested stream is not on the pad | `-EINVAL` |
  | any requested stream already enabled | `-EALREADY` |

- Kerneldoc in `include/media/v4l2-subdev.h`: says `-EINVAL` for a
  non-source pad and `-EOPNOTSUPP` for several source pads; the code does
  neither.
- Fallback with several source pads: allowed; each pad is a bit in
  `sd->enabled_pads`.
- `v4l2_subdev_collect_streams()`: chooses its branch by
  `V4L2_SUBDEV_FL_STREAMS`, not by which ops exist; without the flag only
  `BIT_ULL(0)` is valid, with or without `enable_streams`.
- Fallback enable: calls `s_stream(1)` only when `sd->s_stream_enabled` is
  false; otherwise it only records the pad.
- Fallback disable: calls `s_stream(0)` only when no other bit remains in
  `sd->enabled_pads`.
- `disable_streams` op returns an error: the error is returned and the
  streams stay marked enabled.
- Fallback disable, driver returns an error: `call_s_stream()` returns 0,
  so the pad is cleared and the caller sees success.
- Entry: both functions read `sd->entity.graph_obj.mdev->dev` before any
  check, so the entity must be registered with a media device.

**The s_stream operation**

- `call_s_stream()`: makes no test that the op exists;
  `v4l2_subdev_call()` returns `-ENOIOCTLCMD` for a missing op and
  `-ENODEV` for a NULL sub-device before the wrapper runs.
- `call_s_stream()` on a redundant start or a redundant stop: `WARN_ON()`
  and return 0; the driver is not called.
- `call_s_stream()`: takes no lock; only the callers serialise
  `sd->s_stream_enabled`.
- `v4l2_subdev_is_streaming()`, three cases:

  | Sub-device | Reports | Lock asserted |
  |---|---|---|
  | no `enable_streams` | `sd->s_stream_enabled` | none |
  | `enable_streams`, no `V4L2_SUBDEV_FL_STREAMS` | `sd->enabled_pads != 0` | none |
  | `enable_streams` and `V4L2_SUBDEV_FL_STREAMS` | any `enabled` stream config | active state lock |

- Second row: `sd->enabled_pads` is written by
  `v4l2_subdev_set_streams_enabled()` with the active state lock held, but
  the read is not asserted.
- Sub-device with `enable_streams` whose `s_stream` is
  `v4l2_subdev_s_stream_helper()`: `v4l2_subdev_is_streaming()` does not
  read `sd->s_stream_enabled`.
- Third row with no active state: `v4l2_subdev_is_streaming()` dereferences
  NULL; it does not return false.

## Async registration

**Notifier callbacks**

- `unbind`: `v4l2_async_unbind_subdev_one()` calls it only when the
  connection is the last one left on `sd->asc_list`.
- Sub-device bound through several connections: one `bound` per connection,
  one `unbind`, for the connection removed last.
- `asc->sd`: cleared, and `v4l2_device_unregister_subdev()` called, only in
  that same last-connection case.
- `bound` on a sub-device notifier: never runs inside that notifier's own
  `v4l2_async_nf_register()`; `v4l2_async_nf_try_all_subdevs()` returns 0
  while `v4l2_async_nf_find_v4l2_dev()` finds no `struct v4l2_device`.
- `parent` of a sub-device notifier: set only by
  `v4l2_async_nf_try_subdev_notifier()`, when the notifier's own sub-device
  is bound; its `bound` calls start then.
- `v4l2_async_match_notify()`: does not touch the sub-device's own notifier;
  its callers call `v4l2_async_nf_try_subdev_notifier()` after it, when the
  parent's connection is already on `done_list`.
- `complete`: can run more than once for one notifier; the core keeps no
  completed state, so unbinding and re-binding a sub-device calls it again.
- Root notifier with no connections: `complete` runs inside
  `v4l2_async_nf_register()`.
- `bound` or `complete` error in `__v4l2_async_nf_register()`:
  `v4l2_async_nf_unbind_all_subdevs()` unbinds everything bound through the
  notifier and its sub-notifiers, and the notifier is not added to
  `notifier_list`.
- Error in `__v4l2_async_register_subdev()`: the unwind depends on the step
  that failed.

| Failing step | Undone by the caller |
|---|---|
| `v4l2_async_match_notify()`, including `bound` | nothing beyond what `v4l2_async_match_notify()` undid itself |
| `v4l2_async_nf_try_subdev_notifier()` | `v4l2_async_unbind_subdev_one()` for the current connection |
| `v4l2_async_nf_try_complete()` | `v4l2_async_nf_unbind_all_subdevs()` on the sub-device's own notifier, then `v4l2_async_unbind_subdev_one()` |

**Notifier lifecycle**

- Notifier memory: must be zeroed before init; `v4l2_async_nf_init()` and
  `v4l2_async_subdev_nf_init()` each set one of `v4l2_dev` and `sd` and leave
  the other, `parent` and `ops` untouched.
- `v4l2_async_nf_init()`: takes only a `struct v4l2_device`; a sub-device
  notifier uses `v4l2_async_subdev_nf_init()`.
- `v4l2_async_nf_register()`: `-EINVAL` with `WARN_ON()` when both of
  `v4l2_dev` and `sd` are set, as well as when neither is.
- Add helpers: the only errors are `ERR_PTR(-ENOMEM)`, plus
  `ERR_PTR(-ENOTCONN)` from `__v4l2_async_nf_add_fwnode_remote()`; they never
  return `-EEXIST`.
- Duplicate or invalid match: found by `v4l2_async_nf_match_valid()` inside
  `v4l2_async_nf_register()`; there is no v4l2_async_nf_asc_valid() here.
- Connection added after register: only linked onto `waiting_list`; it skips
  `v4l2_async_nf_match_valid()` and is not tried against sub-devices already
  on `subdev_list`.
- `ops` with a `destroy` op: must be set before any
  `v4l2_async_nf_cleanup()`, including the one after a failed add;
  `v4l2_async_nf_call_destroy()` reads `notifier->ops` at cleanup time. See
  `rkisp1_subdev_notifier_register()` in
  `drivers/media/platform/rockchip/rkisp1/rkisp1-dev.c`, which sets it
  before the first add.
- Root notifier: `v4l2_device_register()` must have run first;
  `__v4l2_device_register_subdev()` uses `v4l2_dev->lock` and
  `v4l2_dev->subdevs` during register.
- **Unsafe usage**: `v4l2_async_nf_cleanup()` on a registered notifier
  without `v4l2_async_nf_unregister()` first.
  - Unsafe: `__v4l2_async_nf_cleanup()` frees `waiting_list` only and hits
    `WARN_ON()` for a non-empty `done_list`; it clears `v4l2_dev` and `sd`,
    so a later `v4l2_async_nf_unregister()` returns early and the notifier
    stays on `notifier_list`.
  - Safe: unregister, then cleanup, as `rkisp1_remove()` does;
    `__v4l2_async_nf_unregister()` moves every connection back to
    `waiting_list` and unlinks the notifier.
  - Safe: cleanup alone after a failed add or a failed
    `v4l2_async_nf_register()`, as `rkisp1_subdev_notifier_register()` does;
    the failed register left nothing on `done_list` or `notifier_list`.
- Reuse after cleanup: needs init again, because cleanup cleared `v4l2_dev`
  and `sd`.
- `sd->subdev_notifier`: `v4l2_async_unregister_subdev()` passes it to
  `kfree()`; only `__v4l2_async_register_subdev_sensor()` in
  `drivers/media/v4l2-core/v4l2-fwnode.c` assigns it, to a notifier it
  allocated.

**Registering an async sub-device**

- `__v4l2_async_register_subdev()` refuses one thing: an `sd->fwnode` that is
  a graph endpoint, with `-EINVAL`.
- Missing fwnode: not refused; `sd->fwnode` stays NULL when `sd->dev` is NULL
  or `dev_fwnode(sd->dev)` is NULL.
- Already registered sub-device: not refused; the function re-initialises
  `sd->asc_list` and adds `sd->async_list` to `subdev_list` again.
- NULL `sd->dev`: refused only by `__v4l2_async_register_subdev_sensor()`,
  with `WARN_ON()` and `-ENODEV`.
- Duplicate matches: checked for connections in
  `v4l2_async_nf_match_valid()`, never for sub-devices.
- Refusals at bind time: `__v4l2_device_register_subdev()` returns `-EINVAL`
  for an empty `sd->name` or a set `sd->v4l2_dev`, and `-ENODEV` when
  `try_module_get()` fails.
- Bind-time error: returned by whichever call ran the match, which can be
  the bridge's `v4l2_async_nf_register()` rather than the sub-device's
  register call.
- `match_fwnode_one()`: tests only the connection's fwnode with
  `fwnode_graph_is_endpoint()`, then compares its port parent with the
  sub-device fwnode.
- Connection holding a device node: matches by pointer equality only, with
  `sd->fwnode` or `sd->fwnode->secondary`.
- `v4l2_async_subdev_endpoint_add()`: stores the endpoint pointer and takes
  no reference; the driver keeps the endpoint alive for as long as the
  sub-device is registered, as `adv748x_remove()` does by calling
  `adv748x_dt_cleanup()` after `adv748x_csi2_cleanup()`.
- `subdev_list`: the sub-device is added whether or not it was bound, so a
  notifier registered later can bind it again.
- **Unsafe usage**: registering with `sd->fwnode` NULL and no fwnode on
  `sd->dev`, when a notifier tries a waiting `V4L2_ASYNC_MATCH_TYPE_FWNODE`
  connection against the sub-device, at registration or later.
  - Unsafe: `match_fwnode()` reads `sd->fwnode->secondary` with no NULL test
    once `match_fwnode_one()` has failed.
  - Safe: `sd->fwnode` left NULL and `sd->dev` set to a device that has a
    fwnode, as `v4l2_i2c_subdev_init()` sets it;
    `__v4l2_async_register_subdev()` fills `sd->fwnode` from `dev_fwnode()`.
  - Safe: a non-empty `sd->async_subdev_endpoint_list`, as
    `adv748x_csi2_init()` sets up; `match_fwnode()` returns before it
    dereferences `sd->fwnode`.
- **Unsafe usage**: registering a sub-device's own notifier after
  `v4l2_async_register_subdev()`.
  - Unsafe: when the sub-device was bound inside its register call, the
    notifier gets no `parent`; `v4l2_async_nf_try_subdev_notifier()` runs
    only when the sub-device is bound, so the notifier binds nothing until
    the sub-device is bound again.
  - Safe: `v4l2_async_nf_register()` first, then the sub-device, as
    `__v4l2_async_register_subdev_sensor()` does;
    `v4l2_async_nf_try_subdev_notifier()` finds only a notifier that is
    already on `notifier_list`.

## Firmware and sensors

**Parsing an endpoint**

- NULL `fwnode`: both functions return `-EPROBE_DEFER`, from the first test in
  `__v4l2_fwnode_endpoint_parse()`; NULL is an accepted argument.
- `-ENXIO`: only when firmware has a non-zero `bus-type` that maps to a type
  other than a non-`V4L2_MBUS_UNKNOWN` `vep->bus_type`; reported with
  `pr_debug()` only.
- No `bus-type` property (or value 0) with an explicit `vep->bus_type`: no
  mismatch test runs; the call returns 0 even when no property of that bus is
  present, so the caller validates the result, as `imx219_check_hwcfg()` does
  for `num_data_lanes`.
- `-EINVAL` for the bus type: a `bus-type` value absent from the `buses` table
  in `drivers/media/v4l2-core/v4l2-fwnode.c`, and also `V4L2_MBUS_DPI`, which
  is in the table but has no case in the switch.
- Guessing (`V4L2_MBUS_UNKNOWN`, no `bus-type`): `vep->bus_type` is never
  `V4L2_MBUS_UNKNOWN` on a return of 0.

| Endpoint has | Guessed type |
|---|---|
| non-empty `data-lanes`, or `clock-lanes`, or `clock-noncontinuous` | `V4L2_MBUS_CSI2_DPHY` |
| else `hsync-active`, `vsync-active` or `field-even-active` | `V4L2_MBUS_PARALLEL` |
| none of these, including no properties at all | `V4L2_MBUS_BT656` |

- `vep->link_frequencies` and `vep->nr_of_link_frequencies`:
  `v4l2_fwnode_endpoint_parse()` never writes them;
  `v4l2_fwnode_endpoint_alloc_parse()` writes them only when
  `link-frequencies` has entries.
- `v4l2_fwnode_endpoint_free()`: calls `kfree()` on `vep->link_frequencies`
  whatever it holds, so `vep` must be zero-initialised before the parse for the
  free to be safe after a failed parse or an absent property.
- Defaults preset in `vep->bus`: the CSI-2 lane count and lane mapping and the
  parallel flags are taken from them only when the bus type is not guessed; in
  guess mode the CSI-2 lane count and the parallel flags start from 0.
- `bus.mipi_csi2.flags`: always overwritten; an absent `clock-noncontinuous`
  clears a preset `V4L2_MBUS_CSI2_NONCONTINUOUS_CLOCK`.
- Parallel `V4L2_MBUS_MASTER` and `V4L2_MBUS_SLAVE`: always rewritten from
  `slave-mode`; an absent property forces `V4L2_MBUS_MASTER`.

**Link frequency helpers**

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

**Sensor clock helper**

- "ACPI" in `__devm_v4l2_sensor_clk_get()` is `!is_of_node(dev_fwnode(dev))`;
  any device without an OF node takes that path.
- `clock-frequency` present with value 0, or a read error other than `-EINVAL`,
  through `devm_v4l2_sensor_clk_get()`: `ERR_PTR(-EINVAL)` on every platform,
  whether or not a clock was found.
- Clock found on a non-OF node with `clock-frequency` present: `clk_set_rate()`
  to that rate first; its error is returned.
- Clock found on an OF node through `devm_v4l2_sensor_clk_get()`: returned
  untouched, `clock-frequency` is not applied.
- No clock from `devm_clk_get_optional()`, through
  `devm_v4l2_sensor_clk_get()`:

| Case | Result |
|---|---|
| OF node, `clock-frequency` present or not | `ERR_PTR(-ENOENT)`, no fixed clock |
| `CONFIG_COMMON_CLK` off | `ERR_PTR(-ENOENT)` |
| `CONFIG_COMMON_CLK` on, non-OF node, `clock-frequency` absent | `ERR_PTR(-EPROBE_DEFER)` |
| `CONFIG_COMMON_CLK` on, non-OF node, `clock-frequency` valid | fixed-rate clock registered and returned |

- Fixed clock name: "clk-<dev_name>-<id>", or "clk-<dev_name>" when `id` is
  NULL.
- `Documentation/driver-api/media/camera-sensor.rst`: does not tell drivers to
  make the clock optional on ACPI; it says the helper returns a fixed clock
  there.

**Power management of sensors**

- System PM handlers: a sensor driver should in general not implement them, per
  `Documentation/driver-api/media/camera-sensor.rst`; `ccs_pm_ops` and
  `imx219_pm_ops` hold only `SET_RUNTIME_PM_OPS()`.
- Streaming state: the driver must not track it to stop in a suspend handler
  and restart in resume; the bridge driver stops and restarts the pipeline
  through `.enable_streams()` and `.disable_streams()`.
- `.s_stream` in `struct v4l2_subdev_video_ops`: marked DEPRECATED in
  `include/media/v4l2-subdev.h`; a new driver implements `.enable_streams` and
  `.disable_streams` and sets `.s_stream` to `v4l2_subdev_s_stream_helper()`.
- Runtime PM must be enabled before `v4l2_async_register_subdev()`, since the
  sub-device is usable as soon as it is registered; see
  `Documentation/driver-api/media/v4l2-subdev.rst`.
- Runtime PM callbacks: may be left unimplemented when the driver handles no
  clocks, regulators or GPIOs, for example an ACPI-only driver.
- `pm_runtime_put_autosuspend()`: calls `pm_runtime_mark_last_busy()` itself; no
  separate call is needed before it.
- **Potentially unsafe usage**: in `s_ctrl`, dropping a reference after
  `pm_runtime_get_if_active()` or `pm_runtime_get_if_in_use()` whenever the
  result is non-zero.
  - Unsafe: with `CONFIG_PM`, when `s_ctrl` can run while runtime PM is
    disabled for the device; `pm_runtime_get_conditional()` returns `-EINVAL`
    and takes no reference, so the put drops a reference held elsewhere or
    makes `rpm_drop_usage_count()` warn of an underflow.
  - Safe: skip the write on 0, write on any non-zero result, and put only when
    the result is > 0, as `ccs_set_ctrl()` does.
  - Safe: an unconditional put when `s_ctrl` cannot run while runtime PM is
    disabled, as `imx219_set_ctrl()`; `imx219_probe()` calls
    `pm_runtime_enable()` before it registers the sub-device and sets no
    control before that, and `imx219_remove()` frees the handler before
    `pm_runtime_disable()`.

## Control framework

**Handler lifecycle**

- `v4l2_ctrl_handler_free()`: returns `int`, the handler's `hdl->error`; returns
  0 when `hdl` is NULL.
- `v4l2_ctrl_handler_free()` early return: tests `hdl->buckets`, not a mutex
  field; with `hdl->buckets` NULL (failed init, zeroed handler, second call) it
  returns `hdl->error` without taking the lock.
- `hdl->error` after free: unchanged; free never clears it, so a second call
  returns the same error.
- `handler_set_err()`: has no benign error codes; it stores any error while
  `hdl->error` is 0.
- `v4l2_ctrl_new_fwnode_properties()`: returns `int` (`hdl->error`), not a
  control pointer.
- Control ID already in the handler (owned or inherited): not reported.
  `handler_new_ref()` drops the new ref and returns 0, so `v4l2_ctrl_new()`
  links the control on `hdl->ctrls` and returns it non-NULL with `hdl->error`
  still 0.
- Such a duplicate control: has no ref and `ctrl->cluster` stays NULL;
  `__v4l2_ctrl_handler_setup()` reads `ctrl->cluster[0]` for every control on
  `hdl->ctrls`.

**Handler lock**

- Lock held around the ops: `ctrl->handler->lock`, the lock of the handler
  that owns the control, taken for example with `v4l2_ctrl_lock(master)` in
  `try_set_ext_ctrls_common()` and `get_ctrl()`. The handler passed to the
  ioctl, which may be an inheriting one, is locked only for the lookup in
  `find_ref_lock()` and `prepare_ext_ctrls()`.
- Getters: there is no unlocked getter and no string getter.
  `v4l2_ctrl_g_ctrl()` and `v4l2_ctrl_g_ctrl_int64()` both lock in
  `get_ctrl()`; inside an op read `ctrl->val` or `ctrl->cur.val` instead.
- `v4l2_ctrl_find()`: takes `hdl->lock` through `find_ref_lock()`, so it
  deadlocks inside an op of the same handler.
- `v4l2_ctrl_activate()`: neither takes nor asserts the lock, but calls
  `send_event()`, which walks `ctrl->ev_subs`; `v4l2_ctrl_add_event()` and
  `v4l2_ctrl_del_event()` change that list under the handler lock.
- Shared lock with sub-device state: drivers set `sd->state_lock` to
  `hdl->lock`, as `imx219_probe()` does, or point both at one driver mutex.
- `v4l2_ctrl_handler_free()`: locks `hdl->lock` and destroys only
  `hdl->_lock`. A driver mutex installed in `hdl->lock` must still be valid
  then and is destroyed by the driver afterwards, as `ov8865_remove()` does.

**Control operations**

- `V4L2_CTRL_FLAG_VOLATILE` control in `cluster_changed()`: its value is never
  compared and it gets `has_changed = false`. A write reaches `s_ctrl` only if
  a cluster member, this one included, has `V4L2_CTRL_FLAG_EXECUTE_ON_WRITE`
  or a non-volatile member differs.
- Forced set: `try_or_set_cluster()` has none; `V4L2_CTRL_FLAG_EXECUTE_ON_WRITE`
  in `cluster_changed()` is the only way to get `s_ctrl` from it with an
  unchanged value. There is no has_new field.
- `cluster_changed()`: tests every non-NULL member, not only those with
  `is_new`, so an `V4L2_CTRL_FLAG_EXECUTE_ON_WRITE` member the caller did not
  set still triggers `s_ctrl`.
- 64-bit value: there is no val64 field in `struct v4l2_ctrl`; ops use
  `*ctrl->p_new.p_s64`.
- Validation before `try_ctrl`: there is no std_validate() here;
  `validate_new()` in `drivers/media/v4l2-core/v4l2-ctrls-api.c` calls
  `type_ops->validate`, by default `v4l2_ctrl_type_op_validate()`.
- Handler bound to a request: `try_set_ext_ctrls_common()` passes
  `!hdl->req_obj.req && set`, so only `try_ctrl` runs and the value is stored
  with `new_to_req()`; `s_ctrl` runs later from `v4l2_ctrl_request_setup()`.
- `ops` used: every call is `call_op(master, ...)` from
  `drivers/media/v4l2-core/v4l2-ctrls-priv.h`; the `ops` of other cluster
  members are not called.

**Controls shared between handlers**

- Private controls: the test is `ctrl->is_private`, not the ID.
  `v4l2_ctrl_new()` rejects an ID at or above `V4L2_CID_PRIVATE_BASE` with
  `-ERANGE`.
- `V4L2_CTRL_TYPE_CTRL_CLASS` controls: skipped; `handler_new_ref()` creates
  the class control in the target handler itself when the control it adds is
  not a compound type.
- `v4l2_ctrl_add_handler()`: walks `add->ctrl_refs`, so controls that `add`
  itself inherited are passed on; `ctrl->handler` stays the original owner.
- `from_other_dev`: stored as the caller passed it; nothing compares devices.
  Only `v4l2_ctrl_request_clone()` reads it: such refs are left out of request
  handler objects, so those controls cannot be set through a request.
- Reference counting: none. `v4l2_device_unregister_subdev()` leaves the refs
  in `v4l2_dev->ctrl_handler` in place.
- **Potentially unsafe usage**: freeing a handler whose controls another
  handler still references.
  - Unsafe: while the other handler can still be looked up or added to;
    `find_ref()` and `handler_new_ref()` read `ref->ctrl->id` of the freed
    control.
  - Safe: when no lookup can follow, in either free order, because
    `v4l2_ctrl_handler_free()` does not read `ref->ctrl`;
    `vivid_free_controls()` runs from `vivid_dev_release()`, the
    `struct v4l2_device` release callback.

**Control clusters**

- `v4l2_ctrl_cluster()`: stores the array pointer in `ctrl->cluster` of every
  member; nothing is copied.
- NULL entries: `controls[0]` NULL or `ncontrols` 0 gives `WARN_ON()` and
  nothing is clustered; `v4l2_ctrl_cluster()`, `try_or_set_cluster()` and
  `cluster_changed()` skip NULL entries after the first.
- `has_volatiles`: `v4l2_ctrl_cluster()` samples `V4L2_CTRL_FLAG_VOLATILE` of
  the members once, at the call. `v4l2_g_ext_ctrls_common()` tests only the
  master's flag and `has_volatiles`, so a flag set on a member afterwards is
  not seen there.
- `ops`: only `controls[0]->ops` is called for the cluster.
- **Unsafe usage**: passing an array that does not outlive the controls, such
  as a local array; `try_or_set_cluster()` reads `master->cluster[i]` on every
  later set.
  - Safe: consecutive `struct v4l2_ctrl *` fields in the driver state, as
    `&ctrls->auto_wb` in `ov5640_init_controls()`.
- **Unsafe usage**: calling `v4l2_ctrl_auto_cluster()` when `controls[0]` may
  be NULL; it reads `controls[0]->minimum` after `v4l2_ctrl_cluster()` has
  only warned.
  - Safe: check `hdl->error` first, as `ov5640_init_controls()` does; every
    NULL return of `v4l2_ctrl_new_std()` leaves `hdl->error` set.

**Applying control values**

- Skipped controls: `ctrl->done`, `V4L2_CTRL_TYPE_BUTTON`,
  `V4L2_CTRL_FLAG_READ_ONLY`. Volatile controls and controls without `s_ctrl`
  are not skipped; `call_op()` returns 0 when the op is missing.
- Skip test: applies to the control being walked, not to its master, so a
  cluster with a read-only master is still applied when the walk reaches a
  writable member.
- `__v4l2_ctrl_handler_setup()`: calls `s_ctrl` directly; it does not go
  through `try_or_set_cluster()`, so no `try_ctrl`, no `cluster_changed()` and
  no `new_to_cur()`. No event is sent and `has_changed` keeps its old value.
- `Documentation/driver-api/media/camera-sensor.rst`: says
  `v4l2_ctrl_handler_setup()` may not be used in the `runtime_resume`
  callback, and names `pm_runtime_get_if_active()` for `s_ctrl`.
- `pm_runtime_get_if_active()` and `pm_runtime_get_if_in_use()`: both return
  `-EINVAL` when runtime PM is disabled, else 0 when the status is not
  `RPM_ACTIVE`; see `pm_runtime_get_conditional()` in
  `drivers/base/power/runtime.c`.
- There is no imx219_start_streaming() here; `imx219_enable_streams()` in
  `drivers/media/i2c/imx219.c` does that.
- **Potentially unsafe usage**: applying the controls from a `runtime_resume`
  callback.
  - Unsafe: when `s_ctrl` gates register writes on
    `pm_runtime_get_if_in_use()` or `pm_runtime_get_if_active()`; the status
    is `RPM_RESUMING` during the callback, so the get returns 0 and `s_ctrl`
    skips the write.
  - Unsafe: when the callback takes `hdl->lock` and the resume can be
    triggered by a task that already holds it, such as an op or a stream op
    under a shared `sd->state_lock`.
  - Safe: from the stream-start path after `pm_runtime_resume_and_get()` has
    returned, with `__v4l2_ctrl_handler_setup()` under the held lock, as
    `imx219_enable_streams()` does.
  - Safe: in the callback when `s_ctrl` tests `pm_runtime_suspended()`, which
    is false in `RPM_RESUMING`, and no caller resumes the device with the
    handler lock held, as `ov8865_resume()` with `ov8865_s_ctrl()`.

## videobuf2

**Order of queue operations**

- `buf_out_validate`: called on output queues at the start of every
  `__buf_prepare()` that finds `vb->prepared` clear, with or without requests.
- `buf_out_validate` for a request: `vb2_core_qbuf()` calls it when an
  unprepared buffer is bound to a request, and `vb2_req_prepare()` calls it
  again through `__buf_prepare()` when the request is queued.
- `buf_init` at allocation: MMAP only, in `__vb2_queue_alloc()`. USERPTR and
  DMABUF buffers get it at their first prepare.
- `buf_queue` before `start_streaming`: only for buffers already on
  `queued_list` when `vb2_start_streaming()` runs.
- `min_queued_buffers` of 0 with nothing queued: `start_streaming` is called
  with count 0 and every `buf_queue` comes after it.
- `buf_finish` without a dequeue: `__vb2_queue_cancel()` calls it for every
  buffer with `vb->prepared` set, including one that was only prepared and
  never saw `buf_queue`.
- `prepare_streaming` skipped: `vb2_core_streamon()` returns 0 when already
  streaming, and `-EINVAL` with no buffers or fewer buffers allocated than
  `min_queued_buffers`, before the call.
- `unprepare_streaming` after a failed start: called by `vb2_core_streamon()`;
  not called when the failed `vb2_start_streaming()` came from
  `vb2_core_qbuf()`, where it waits for `__vb2_queue_cancel()`.
- `unprepare_streaming` in `__vb2_queue_cancel()`: runs after `stop_streaming`
  and before the core reclaims buffers the driver still owns.
- Can run with `start_streaming` never called: `buf_init`, `buf_out_validate`,
  `buf_prepare`, `buf_finish`, `buf_cleanup`, `prepare_streaming`,
  `unprepare_streaming`.
- `stop_streaming`: only after a `start_streaming` that returned 0.

**Locks around queue operations**

- `__vb2_wait_for_done_vb()`: calls `mutex_unlock(q->lock)` and
  `mutex_lock(q->lock)` unconditionally; a NULL `lock` never gets this far
  (see "Initialising a queue").
- `struct vb2_ops` has no `wait_prepare` or `wait_finish` member; under
  `drivers/media/` those names exist only in the amphion driver's own
  `struct vpu_inst_ops`. There are no vb2_ops_wait_prepare or
  vb2_ops_wait_finish helpers.
- **Unsafe usage**: a blocking `vb2_core_dqbuf()` or `vb2_dqbuf()` when the
  caller does not hold `q->lock`; the wait unlocks a mutex that is not held.
  - Safe: caller holds `q->lock`, as `vb2_thread()` does around
    `vb2_core_dqbuf()`.
  - Safe: ioctl through `video_ioctl2()` with `vdev->queue` set, or with an
    m2m context; `v4l2_ioctl_get_lock()` then returns that queue's lock.
- `vdev->queue` unset and no m2m context: the ioctl core holds only
  `vdev->lock`, so `q->lock` must be that same mutex, or the handler takes
  `q->lock` itself, as `isp_video_dqbuf()` in
  `drivers/media/platform/ti/omap3isp/ispvideo.c` does.
- `videobuf2-core.c` takes `q->lock` itself only in `vb2_req_prepare()`,
  `vb2_req_unprepare()`, `vb2_req_queue()` and `vb2_thread()`, besides the
  relock in `__vb2_wait_for_done_vb()`; the `vb2_core_` functions and the
  `vb2_ioctl_` helpers rely on the caller.
- `q->lock` is never asserted by the core; `v4l2_m2m_ctx_release()` calls
  `vb2_queue_release()` on both queues and takes no lock, so its caller
  decides what `stop_streaming` runs under.
- `buf_cleanup` from `__vb2_queue_free()`: also under `q->mmap_lock`;
  `buf_cleanup` from `__prepare_userptr()` or `__prepare_dmabuf()` is not.
- `q->waiting_in_dqbuf`: set while the lock is dropped; `vb2_core_reqbufs()`
  with a non-zero count, `vb2_core_create_bufs()` on an empty queue,
  `__vb2_perform_fileio()` and a second waiter return `-EBUSY`.
- STREAMOFF and a queue release still run during the wait; the sleeper then
  returns `-EINVAL` because `q->streaming` is clear.

**Queue ownership**

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

**The queue_setup operation**

- `vb2_core_reqbufs()` after the first `queue_setup`: besides the return
  value, checks only that `num_planes` and each `plane_sizes[i]` are
  non-zero; there is no upper bound on `num_planes` and no test of
  `*num_buffers`.
- `vb2_core_create_bufs()` after the first `queue_setup`: checks only the
  return value.
- `__vb2_queue_alloc()` writes `vb->planes[]` for every plane up to
  `num_planes`, so `queue_setup` must keep it at or below `VB2_MAX_PLANES`.
- `vb2_create_bufs()`: rejects a zero requested size and a plane count of 0 or
  above `VIDEO_MAX_PLANES` before the core is called, and always passes at
  least one plane.
- CREATE_BUFS sizes: whatever `queue_setup` leaves in `sizes[]` becomes
  `min_length`; the core never compares it with the current format.
- `*num_buffers` in CREATE_BUFS: the number being added, already limited to
  the free slots; `vb2_get_num_buffers()` gives the existing count.
- `q->min_reqbufs_allocation`: applied to the count before `queue_setup` in
  REQBUFS only; if fewer buffers end up allocated the result is `-ENOMEM`.
- Second `queue_setup` call (fewer buffers allocated than asked): REQBUFS
  zeroes `num_planes` first; CREATE_BUFS passes the values the first call
  left.
- Error from the second call: REQBUFS returns it; CREATE_BUFS returns
  `-ENOMEM` whatever the driver returned.
- Buffers already allocated at the second call keep the first call's sizes.
- CREATE_BUFS on an empty queue: is the first allocation and sets
  `q->memory`, still with a non-zero `*num_planes`.

**Imported buffers**

- `__prepare_dmabuf()`: compares the plane `length` (from user space, or
  `dbuf->size` when 0) with `min_length`; `data_offset` plays no part.
- Real dma-buf size: checked against `length` by the `attach_dmabuf` memop of
  each allocator in `drivers/media/common/videobuf2/`, which returns
  `-EFAULT`, for each plane it attaches.
- `__prepare_userptr()`: skips the `min_length` test for a plane whose pointer
  and length are unchanged; `__prepare_dmabuf()` tests every plane each time.
- Same memory queued again: `buf_prepare` still runs; only `buf_cleanup` and
  `buf_init` are skipped.
- `buf_prepare` fails on an imported buffer: the core calls `buf_cleanup` and
  releases every plane, so the next prepare calls `buf_init` again.
- `buf_init` fails: planes are released with no `buf_cleanup`.
- MMAP `buf_prepare` failure: no `buf_cleanup`, memory kept.
- USERPTR change: only the changed planes are released and pinned again.
- DMABUF change in any plane: all planes are detached and attached again.
- `buf_cleanup` and `buf_init` run once per buffer per reacquire, not once
  per plane.
- `__vb2_queue_free()`: skips `buf_cleanup` when `planes[0].mem_priv` is NULL,
  which is the case for an imported buffer never prepared or whose last
  `__prepare_userptr()` or `__prepare_dmabuf()` failed.
- Core checks nothing against the current format; `__verify_length()` in
  `videobuf2-v4l2.c` covers output queues only.

**Initialising a queue**

- `lock`: mandatory; `vb2_core_queue_init()` returns `-EINVAL` with `WARN_ON`
  when it is NULL.
- `lock` must be the mutex the callers of the queue hold; see "Locks around
  queue operations".
- `max_num_buffers` above `MAX_BUFFER_INDEX`: clamped, not refused.
- `max_num_buffers` below `VB2_MAX_FRAME` (after 0 was replaced): refused.
- `min_reqbufs_allocation` above `max_num_buffers`: refused, tested after it
  was raised to `min_queued_buffers + 1`.
- Not tested at init: `io_modes` against `mem_ops`. `vb2_verify_memory_type()`
  returns `-EINVAL` at REQBUFS or CREATE_BUFS time.
- Init uses `WARN_ON` and `-EINVAL` only; `BUILD_BUG_ON()` in
  `vb2_queue_init_name()` covers the memory enum values.
- `vb2_queue_init_name()` with a NULL name: clears `q->name`, and the core
  then generates one.

**Starting to stream**

- Failed start: `stop_streaming` and `__vb2_queue_cancel()` are not called;
  `vb2_start_streaming()` reclaims by itself.
- No error code is special; any non-zero return is handled the same way.
- Failure from `vb2_core_streamon()`: the core calls `unprepare_streaming`,
  so `start_streaming` undoes only its own work; `q->streaming` stays 0.
- Failure from `vb2_core_qbuf()`: `q->streaming` stays 1,
  `unprepare_streaming` is not called, and the next QBUF that satisfies
  `min_queued_buffers` calls `vb2_start_streaming()` again.
- After a failure the buffers stay on `queued_list`, except the one whose
  QBUF triggered the start; the next `vb2_start_streaming()` passes each of
  them to `buf_queue` again.
- **Unsafe usage**: a failing `start_streaming` that leaves buffers on the
  driver's own list; the core takes them back and later hands them to
  `buf_queue` a second time.
  - Safe: remove each buffer from the driver list and return it with
    `VB2_BUF_STATE_QUEUED`, as `vid_cap_start_streaming()` in
    `drivers/media/test-drivers/vivid/vivid-vid-cap.c` does.
- **Unsafe usage**: a failing `start_streaming` that returns buffers with
  `VB2_BUF_STATE_DONE` or `VB2_BUF_STATE_ERROR`; the core only does
  `WARN_ON(!list_empty(&q->done_list))` and leaves them on `done_list` while
  they are still on `queued_list`.
  - Safe: `VB2_BUF_STATE_QUEUED`, as `vimc_capture_start_streaming()` does
    through `vimc_capture_return_all_buffers()`.

**Stopping a stream**

- Paths that can reach the call: `vb2_core_streamoff()` and
  `vb2_core_queue_release()`, the latter also through `__vb2_cleanup_fileio()`.
- `vb2_core_reqbufs()`: runs `__vb2_queue_cancel()` but returns `-EBUSY` first
  when `q->streaming` is set, so `stop_streaming` is not called from there.
- `vb2_core_create_bufs()`: has no `q->streaming` test and never cancels.
- State passed to `vb2_buffer_done()` in `stop_streaming`: never reaches user
  space; `__vb2_queue_cancel()` empties `done_list` and sets every buffer to
  `VB2_BUF_STATE_DEQUEUED`.
- `__vb2_queue_cancel()` re-initialises `done_list` without `q->done_lock`,
  and `vb2_core_queue_release()` frees the buffers right after.
- **Unsafe usage**: returning from `stop_streaming` while an interrupt
  handler, thread or work item can still call `vb2_buffer_done()`.
  - Safe: stop the producer first, then return the buffers, as
    `vimc_capture_stop_streaming()` does: `vimc_streamer_s_stream()` calls
    `kthread_stop()` before `vimc_capture_return_all_buffers()`.

**Returning a buffer**

- VB2_BUF_STATE_REQUEUEING is not in this tree; `enum vb2_buffer_state` has
  seven values and `vb2_buffer_done()` accepts three of them.
- `queued_list`: the buffer stays on it for every target state;
  `vb2_core_dqbuf()` removes it.
- Request buffer, target not `VB2_BUF_STATE_QUEUED`: calls
  `media_request_object_unbind()` and `media_request_object_put()` under
  `q->done_lock`; it does not call `media_request_object_complete()`.
- After a call with target `VB2_BUF_STATE_DONE` or `VB2_BUF_STATE_ERROR`,
  `vb->req_obj.req` is NULL.
- **Potentially unsafe usage**: `v4l2_ctrl_request_complete()` after
  `vb2_buffer_done()` returned the request's buffer with
  `VB2_BUF_STATE_DONE` or `VB2_BUF_STATE_ERROR`.
  - Unsafe: passing `vb->req_obj.req` read after the buffer was returned; it
    is NULL and `v4l2_ctrl_request_complete()` returns without completing the
    control object.
  - Safe: complete the controls first, as `vivid_stop_generating_vid_cap()`
    in `drivers/media/test-drivers/vivid/vivid-kthread-cap.c` does.
  - Safe: the request pointer was copied before the buffer was returned and
    the request is marked with `media_request_mark_manual_completion()`, as
    `device_run()` in `drivers/media/test-drivers/vicodec/vicodec-core.c`
    does; the request stays QUEUED until `media_request_manual_complete()`.

**Releasing a queue**

- `vb2_fop_release()`: takes `vdev->queue->lock`, and `vdev->lock` only if
  that is NULL.
- `_vb2_fop_release()`: calls `vb2_queue_release()` when `owner` is NULL or is
  the closing file.
- The queue release in `vb2_video_unregister_device()` is unconditional; it
  does not depend on streaming or on there being an owner.
- `vb2_video_unregister_device()` on a device that is not registered: returns
  at once and does not release the queue.
- Close after `vb2_video_unregister_device()`: `owner` is NULL, so
  `_vb2_fop_release()` calls `vb2_queue_release()` again; on the empty queue
  no driver operation runs.
- `video_unregister_device()` alone: does not touch `vdev->queue`; with
  `vb2_fop_release()` as the release op, `stop_streaming` then runs at the
  owner's close.
- `vb2_video_unregister_device()` takes the queue lock itself, so the caller
  must not hold it.
- **Potentially unsafe usage**: freeing the structure that holds the
  `struct vb2_queue` and its mutex.
  - Unsafe: in the remove function while a file is open; the later
    `vb2_fop_release()` reads `vdev->queue->lock` and locks it.
  - Safe: in the `release` callback of `struct video_device`, which
    `v4l2_device_release()` calls after the last close, as
    `video_i2c_release()` in `drivers/media/i2c/video-i2c.c` does.

## Memory-to-memory devices

**Job scheduling**

- `TRANS_RUNNING`: not tested by `__v4l2_m2m_try_queue()`; a running context is
  skipped because `TRANS_QUEUED` stays set until `_v4l2_m2m_job_finish()`.
- CAPTURE streaming: not required when `m2m_ctx->ignore_cap_streaming` is set;
  OUTPUT streaming is always required. Both are tested before `job_spinlock`
  is taken.
- Ready buffers: the list is `rdy_queue`; `out_q_ctx.buffered` waives the
  source buffer, `cap_q_ctx.buffered` the destination buffer.
- Held capture buffer (`is_held`) whose copied timestamp differs from the
  source's: `__v4l2_m2m_try_queue()` completes it as `VB2_BUF_STATE_DONE`
  itself and tests the next destination buffer; none left means no job,
  unless `cap_q_ctx.buffered` is set.
- `has_stopped`: blocks queueing; tested after the held-buffer step and before
  `job_ready`.
- `QUEUE_PAUSED` in `job_queue_flags`: `v4l2_m2m_try_run()` runs nothing while
  it is set.
- `job_ready`: called under `job_spinlock` with interrupts off, and also from
  the job-finish path, so possibly in hard-IRQ context.
- `device_run`: called in process context, with no m2m spinlock held, from
  three places:

| Caller of `v4l2_m2m_try_run()` | Mutex held |
|---|---|
| `v4l2_m2m_try_schedule()` | whatever its caller holds |
| `v4l2_m2m_device_run_work()` (`job_work`) | none |
| `v4l2_m2m_resume()` | whatever its caller holds |

- `v4l2_m2m_try_run()` runs the head of `job_queue`, which need not be the
  context passed to `v4l2_m2m_try_schedule()`; a mutex held by the caller may
  belong to another context.
- **Unsafe usage**: calling `v4l2_m2m_try_schedule()` from hard-IRQ or atomic
  context, or under a spinlock.
  - Unsafe: it calls `device_run` synchronously, and `device_run` may sleep;
    for example `venus_helper_m2m_device_run()` takes a mutex.
  - Safe: from an ioctl handler, as `v4l2_m2m_qbuf()` does.
  - Safe: from a threaded interrupt handler, as
    `wave5_vpu_dec_finish_decode()` does under `wave5_vpu_irq_thread()`.
  - Safe: from atomic context call `v4l2_m2m_job_finish()` instead;
    `v4l2_m2m_schedule_next_job()` defers the run with `schedule_work()`.

**Stop commands and draining**

- `v4l2_update_last_buf_state()`: is the STOP handler, static in
  `drivers/media/v4l2-core/v4l2-mem2mem.c`; called only from
  `v4l2_m2m_encoder_cmd()` and `v4l2_m2m_decoder_cmd()`, never on buffer
  completion.
- START in `v4l2_m2m_encoder_cmd()` and `v4l2_m2m_decoder_cmd()`: returns
  `-EBUSY` while `is_draining` is set; otherwise clears only `has_stopped`.
- `next_buf_last`: `v4l2_update_last_buf_state()` sets it only when no source
  buffer and no capture buffer is on the ready list;
  `v4l2_m2m_update_stop_streaming_state()` sets it for the OUTPUT queue while
  draining when no capture buffer is on the ready list.
- `last_src_buf`: `drivers/media/v4l2-core/v4l2-mem2mem.c` never compares it
  with a buffer, and `v4l2_m2m_buf_done_and_job_finish()` has no draining
  logic. The driver tests `v4l2_m2m_is_last_draining_src_buf()` for each job
  and ends the drain.
- Last capture buffer of a drain, two in-tree forms:
  - in the job that consumes `last_src_buf`, set `V4L2_BUF_FLAG_LAST` on the
    destination buffer and call `v4l2_m2m_mark_stopped()`, then complete the
    buffers as usual, as `hantro_job_finish_no_pm()` does;
  - `v4l2_m2m_last_buffer_done()`, which completes the buffer itself, always
    with `VB2_BUF_STATE_DONE`; not usable with
    `v4l2_m2m_buf_done_and_job_finish()`, which completes the first
    destination buffer on the ready list itself.
- `v4l2_m2m_mark_stopped()`: clears `next_buf_last` as well as `is_draining`.
- `v4l2_m2m_clear_state()`: does not clear `last_src_buf`.
- `v4l2_m2m_qbuf()` on a CAPTURE buffer: completes the first buffer on the
  queue's `queued_list` as LAST through `v4l2_m2m_force_last_buf_done()` only
  when the queue is streaming, `vb2_start_streaming_called()` is false, and
  `has_stopped` is set or `v4l2_m2m_dst_buf_is_last()` is true. Once
  `start_streaming` has run, the driver's `buf_queue` must test
  `v4l2_m2m_dst_buf_is_last()` itself, as `hantro_buf_queue()` does.

**Queue locks of a context**

- NULL `lock`: `vb2_core_queue_init()` does `WARN_ON(!q->lock)` and returns
  `-EINVAL`, so a `queue_init` that returns the result of `vb2_queue_init()`
  fails when a `lock` is NULL. The "optional" comment on `q_lock` in
  `include/media/v4l2-mem2mem.h` does not match that.
- Different locks: `v4l2_m2m_ctx_init()` does
  `WARN_ON(out_q_ctx->q.lock != cap_q_ctx->q.lock)` and returns
  `ERR_PTR(-EINVAL)`.
- `VIDIOC_ENCODER_CMD` and `VIDIOC_DECODER_CMD`: not `INFO_FL_QUEUE`, so they
  run under `vdev->lock`; the stop helpers take no mutex themselves, while
  `v4l2_m2m_qbuf()` reads the same draining state under `q_lock`.
- `job_spinlock`: not available to drivers; `struct v4l2_m2m_dev` is defined
  in `drivers/media/v4l2-core/v4l2-mem2mem.c`.
- **Unsafe usage**: taking the queue mutex in `device_run`, in `job_abort`, or
  on the path that finishes the job.
  - Unsafe: the dispatcher holds `q_lock` across `v4l2_m2m_qbuf()` and
    `v4l2_m2m_streamon()`, which call `device_run` synchronously, and across
    `v4l2_m2m_streamoff()`, where `v4l2_m2m_cancel_job()` calls `job_abort`
    and then sleeps until `TRANS_RUNNING` clears.
  - Safe: a mutex that is not the queue lock, as `mxc_isi_m2m_device_run()`
    takes `m2m->lock` while its queues use `ctx->vb2_lock`.
  - Safe: no mutex on the completion path, as `device_work()` in
    `drivers/media/test-drivers/vim2m.c`.

**Finishing and aborting a job**

- `v4l2_m2m_buf_done_and_job_finish()` order: destination buffer first, unless
  it is held, then the source buffer, then the job; both get the same `state`.
  The reason in the code: completing the source buffer unbinds it from its
  request and may signal the request fd.
- `v4l2_m2m_job_finish()`: does not touch buffers and imposes no order.
- `_v4l2_m2m_job_finish()` for a context that is not `curr_ctx`: returns
  `false` with only a `dprintk()`; no warning, nothing is scheduled.
- Next job: `v4l2_m2m_schedule_next_job()` requeues the same context with
  `__v4l2_m2m_try_queue()` and calls `schedule_work()` on `job_work`; it does
  not call `v4l2_m2m_try_run()` directly.
- Calling either finish function from inside `device_run`: works, because the
  next run is deferred; `cedrus_device_run()` does so on a setup error.
  `include/media/v4l2-mem2mem.h` has no rule against it.
- `v4l2_m2m_job_finish()` on a queue with
  `VB2_V4L2_FL_SUPPORTS_M2M_HOLD_CAPTURE_BUF`: `WARN_ON()` only; the job is
  still finished, but `is_held` is never updated.
- `TRANS_ABORT`: stays set after the job ends, so the context is not requeued
  until `v4l2_m2m_streamoff()` zeroes `job_flags`.
- **Unsafe usage**: calling `v4l2_m2m_buf_done_and_job_finish()` after the
  driver has removed the source or destination buffer from the ready list.
  - Unsafe: with the list then empty it does
    `WARN_ON(!src_buf || !dst_buf)` and returns without finishing the job, so
    `curr_ctx` stays set and `v4l2_m2m_cancel_job()` never wakes; with more
    buffers on the list it completes the next ones instead.
  - Safe: peek with `v4l2_m2m_next_src_buf()` and `v4l2_m2m_next_dst_buf()`
    and let the helper remove them, as `cedrus_device_run()` and
    `hantro_job_finish_no_pm()` do.
  - Safe: remove the buffers yourself and call plain `v4l2_m2m_job_finish()`,
    as `device_work()` in `drivers/media/test-drivers/vim2m.c`.

## Media controller graph

**Changing a link**

- Test order in `__media_entity_setup_link()`: NULL link, then any flag
  difference outside `MEDIA_LNK_FL_ENABLED` (`-EINVAL`), then
  `MEDIA_LNK_FL_IMMUTABLE`, then equal flags, then streaming.
- Requested flags: never masked; the caller must pass the link's other bits
  unchanged.
- `MEDIA_LNK_FL_IMMUTABLE` link with different flags: `-EINVAL`. The core's
  own `-EBUSY` comes only from the streaming test; a `link_notify` or
  `link_setup` callback can return it too, as `ccdc_link_setup()` does.
- Streaming test: `media_pad_is_streaming()` on both pads, which is `pipe` of
  `struct media_pad`; `struct media_entity` and `struct media_pad` have no
  `stream_count` field.
- `MEDIA_LNK_FL_DYNAMIC`: read from `link->flags`, not from the requested
  flags.
- Link type: `__media_entity_setup_link()` has no test for it and, past the
  flag tests, reads `link->source` and `link->sink` as pads.
  `MEDIA_IOC_SETUP_LINK` reaches only data links, through
  `media_entity_find_link()`.
- `link_notify`: called directly by `__media_entity_setup_link()`, before and
  after `__media_entity_setup_link_notify()`, which calls only `link_setup`.
- `MEDIA_DEV_NOTIFY_POST_LINK_CH`: sent also when a `link_setup` failed, with
  the requested flags while `link->flags` still holds the old ones; its return
  value is ignored.
- `MEDIA_DEV_NOTIFY_PRE_LINK_CH`: never undone by the core; the only undo is
  the second source `link_setup` call after a sink failure.

**Graph mutex**

- ioctls: every entry of `ioctl_info[]` in `drivers/media/mc/mc-device.c` has
  `MEDIA_IOC_FL_GRAPH_MUTEX` except `MEDIA_IOC_REQUEST_ALLOC`; that includes
  `MEDIA_IOC_DEVICE_INFO`, `MEDIA_IOC_ENUM_ENTITIES` and
  `MEDIA_IOC_ENUM_LINKS`.
- `MEDIA_IOC_ENUM_LINKS32`: not in the table; `media_device_compat_ioctl()`
  takes the mutex itself.
- `lockdep_assert_held()`: in `drivers/media/mc`, only in
  `__media_pipeline_start()` and `media_graph_walk_iter()`.
  `__media_pipeline_stop()`, `__media_entity_setup_link()`,
  `__media_entity_remove_links()`, `__media_remove_intf_link()` and
  `__media_remove_intf_links()` check nothing.
- Streaming state under the mutex: `pipe` of `struct media_pad` and
  `start_count` of `struct media_pipeline`; `struct media_entity` and
  `struct media_pad` have no `stream_count` field.
- Functions that lock: search `graph_mutex` in `drivers/media/mc` and
  `drivers/media/v4l2-core/v4l2-mc.c`. `media_device_unregister()` locks before
  it tests whether the device was registered.
- Lock only when `graph_obj.mdev` is non-NULL, else no lock:
  `media_entity_pads_init()`. `media_entity_remove_links()`,
  `media_remove_intf_link()` and `media_remove_intf_links()` return at once
  when it is NULL.
- `v4l_enable_media_source()` and `v4l_disable_media_source()`: take the mutex
  and call `enable_source` and `disable_source` of `struct media_device` under
  it.
- `media_gobj_create()`: writes the `mdev` lists, `id` and `topology_version`
  with no lock and no assert. `media_create_pad_link()`,
  `media_create_ancillary_link()`, `media_create_intf_link()` and
  `media_devnode_create()` call it without taking the mutex.
- Callbacks the core runs with the mutex held: `link_setup`, `link_notify`,
  `link_validate`, `has_pad_interdep`, `notify` of
  `struct media_entity_notify`, `enable_source`, `disable_source`.
- **Unsafe usage**: calling a function that takes `graph_mutex` from one of
  those callbacks, for example `media_entity_setup_link()`,
  `media_pipeline_start()` or `v4l2_pipeline_pm_get()`; the mutex is not
  recursive.
  - Safe: the `__` form, as `au0828_enable_source()` does with
    `__media_entity_setup_link()` and `__media_pipeline_start()`;
    `__media_pipeline_start()` asserts the mutex.
  - Safe: `media_create_pad_link()` from a `notify` callback, as
    `au0828_media_graph_notify()` does; it takes no lock.

**Media device lifecycle**

- `struct media_devnode`: allocated in `__media_device_register()`;
  `mdev->devnode` is a pointer, not an embedded structure.
- `media_device_unregister()`: after a NULL test of `mdev` it locks
  `graph_mutex` before any other test, so `media_device_init()` must have run;
  with that done it returns early when `mdev->devnode` is NULL or not
  registered.
- `media_device_unregister()`: removes the `model` attribute and calls
  `media_devnode_unregister()` after it has dropped `graph_mutex`.
- `media_devnode_release()`: calls `devnode->release` and frees the devnode; it
  does not release the minor. `media_devnode_unregister()` clears the bit in
  `media_devnode_nums`, so the minor can be reused while old files are open.
- `media_devnode_unregister()`: sets `devnode->media_dev` to NULL.
- Open file on the media node: holds a reference on the devnode only, not on
  the `struct media_device`.
- After unregistration: ioctl returns `-EIO`, open returns `-ENXIO`, poll
  returns `EPOLLERR | EPOLLHUP`; see `drivers/media/mc/mc-devnode.c`.
- Read and write on the media node: `-EINVAL` before and after unregistration,
  because `media_device_fops` has neither op.
- Request fd: holds no reference on the media device or devnode, and
  `media_request_release()` and the request ioctls in
  `drivers/media/mc/mc-request.c` use `req->mdev` (`ops`, `req_queue_mutex`,
  `num_requests`) for as long as the fd is open.
- Entities after `media_device_unregister()`: every entity and pad has
  `graph_obj.mdev == NULL`. `media_device_unregister_entity()` then returns at
  once; `media_pipeline_start()` and `v4l2_pipeline_pm_get()` dereference it
  with no NULL test.
- Interfaces: `media_device_unregister()` unlinks them and does not free them;
  `media_devnode_remove()` afterwards is safe and frees the interface.
- `media_device_cleanup()`: destroys the ida, `pm_count_walk`, `graph_mutex`
  and `req_queue_mutex`; it touches no request.
- Cleanup from a release callback: see `vimc_v4l2_dev_release()` in
  `drivers/media/test-drivers/vimc/vimc-core.c`.
- Refcounted media device: `media_device_usb_allocate()` and
  `media_device_delete()` in `drivers/media/mc/mc-dev-allocator.c`; the last
  put calls `media_device_unregister()`, `media_device_cleanup()`, `kfree()`.

**Registering an entity**

- `media_entity_pads_init()`: refuses `num_pads >= MEDIA_ENTITY_MAX_PADS` with
  `-E2BIG`, so 512 itself is refused; the macro is private to
  `drivers/media/mc/mc-entity.c`.
- Pad flags: a pad without exactly one of `MEDIA_PAD_FL_SINK` and
  `MEDIA_PAD_FL_SOURCE` gives `-EINVAL`, with no warning.
- `media_entity_pads_init()`: does not touch `entity->links` or any pipeline
  state.
- `entity->links`: initialised only by `media_device_register_entity()`, which
  also zeroes `num_links` and `num_backlinks`.
- Subdevs: `v4l2_subdev_init()` sets `entity.name`, `entity.obj_type` and
  `entity.function = MEDIA_ENT_F_V4L2_SUBDEV_UNKNOWN`; the driver sets
  `function` after that call.
- Video devices: `video_register_media_controller()` does nothing when
  `v4l2_dev->mdev` is NULL or `vfl_dir` is `VFL_DIR_M2M`. Otherwise it writes
  `entity.obj_type` and `entity.function` from `vfl_type`; for every type but
  `VFL_TYPE_RADIO` and `VFL_TYPE_SUBDEV` it also sets `entity.name` and
  registers the entity. The driver sets the pads.
- `graph_obj.mdev`: must be NULL at registration, else `WARN_ON()`; the
  function still goes on and registers.
- **Unsafe usage**: `media_create_pad_link()` with either entity not
  registered, or `media_create_ancillary_link()` with the primary not
  registered; `media_gobj_create()` has `BUG_ON(!mdev)`, and registration
  reinitialises `links`.
  - Safe: register both entities first, as
    `v4l2_m2m_register_media_controller()` does.
- `media_device_unregister_entity()`: calls no `entity_notify` callback.
- `media_device_unregister_entity()` removes, besides the entity: interface
  links in any interface's list whose `entity` is this one; every link in
  `entity->links`, and for a data link its `reverse` in the remote list; the
  pad graph objects; the `internal_idx`.
- Ancillary links: removed only from the entity's own `links`, where it is the
  primary; a link whose `gobj1` is this entity stays in the primary's list.

**Kinds of link**

| Kind | List that holds it | Valid fields |
|---|---|---|
| data, forward | `links` of the source entity | `source`, `sink`, `reverse` |
| data, backlink | `links` of the sink entity | same `source` and `sink`, `reverse`, `is_backlink` set |
| ancillary | `links` of the primary entity only | `gobj0`, `gobj1`: graph objects of the two entities; `reverse` NULL |
| interface | `links` of `struct media_interface` | `intf`, `entity` |

- Ancillary link: holds no pad pointer; `link->source->entity` reads a field
  of `struct media_entity` through the wrong type.
- Backlink: gets its own `media_gobj_create()`, so it has an id and sits in
  `mdev->links`; `media_device_get_topology()` skips it by `is_backlink`.
- `entity->links` before registration: the list head is not initialised, so
  any walk, `for_each_media_entity_data_link()` included, is invalid until
  `media_device_register_entity()` has run.
- `graph_mutex`: excludes link removal by `media_entity_remove_links()`,
  `media_device_unregister_entity()` and `media_device_unregister()`, which
  take it; it does not exclude creation, because `media_create_pad_link()` and
  `media_create_ancillary_link()` add to `links` without it.
- `for_each_media_entity_data_link()`: not safe against removal of the current
  link; `__media_entity_remove_links()` uses `list_for_each_entry_safe()`.
- **Potentially unsafe usage**: `list_for_each_entry()` over `entity->links`
  that uses `link->source` or `link->sink`.
  - Unsafe: dereferencing them with no type test when the entity can be the
    primary of an ancillary link; `v4l2_async_create_ancillary_links()` adds
    one to the notifier's sub-device when it binds a `MEDIA_ENT_F_LENS` or
    `MEDIA_ENT_F_FLASH` sub-device.
  - Safe: test `MEDIA_LNK_FL_LINK_TYPE` against `MEDIA_LNK_FL_DATA_LINK`
    first, as `media_entity_remote_pad_unique()` does.
  - Safe: `for_each_media_entity_data_link()`, as `media_entity_find_link()`
    does; `__media_entity_next_link()` filters by type.
  - Safe: only comparing the two pointers with a pad before any dereference,
    as `media_pad_remote_pad_unique()` does.
- **Potentially unsafe usage**: walking `entity->links` without `graph_mutex`.
  - Unsafe: while an entity at either end can be unregistered or have its
    links removed; `__media_entity_remove_link()` frees the link and its
    `reverse` in the remote entity's list.
  - Safe: with `graph_mutex` held, as in `__media_pipeline_start()`, which
    asserts it, and so in a `link_validate` callback.

## Pipelines

**Starting a pipeline**

- Origin already in another pipeline: `__media_pipeline_start()` returns
  `-EINVAL` through `WARN_ON(origin->pipe && origin->pipe != pipe)`, before any
  walk; `-EBUSY` is only for pads found later.
- Second start: after that `WARN_ON()`, the only test is `pipe->start_count`
  non-zero; whether the origin is in the pipeline is not looked at.
- Second start from an origin the first walk did not reach: returns 0, adds
  nothing, `origin->pipe` stays NULL; `__media_pipeline_stop()` on that pad
  hits `WARN_ON(!pipe)` and returns without decrementing `start_count`.
- Pads the walk adds, in `media_pipeline_explore_next_link()`:
  - the local end of each data link of the entity whose pad is the incoming pad
    or interdependent with it, including disabled links;
  - the remote end, only if the link has `MEDIA_LNK_FL_ENABLED`;
  - pads of the entity with `num_links` zero that are interdependent with the
    incoming pad; this is the block after the `done:` label.
- `media_entity_has_pad_interdep()` in `drivers/media/mc/mc-entity.c`: returns
  false for two sinks or two sources before it consults `has_pad_interdep`;
  only sink/source pairs default to interdependent.
- `v4l2_subdev_has_pad_interdep()`: used only where a driver puts it in its
  `struct media_entity_operations`; nothing in `drivers/media/v4l2-core/`
  installs it for sub-devices.
- Wrappers: `drivers/media/v4l2-core/` has video device wrappers only, in
  `v4l2-dev.c`; the start wrappers return `-ENODEV` unless the entity has
  exactly one pad. There is no sub-device wrapper.
- Membership is recorded twice, at different times: a
  `struct media_pipeline_pad` goes on `pipe->pads` during the walk; the `pipe`
  field of `struct media_pad` is written later, in the validation loop.

**Validation at pipeline start**

- `MEDIA_PAD_FL_MUST_CONNECT` pad with no links at all: `-ENOLINK`, because
  `has_enabled_link` starts false; the comment above the test in
  `__media_pipeline_start()` says "either no link or an enabled link", and the
  test does not do that.
- Such a pad gets on `pipe->pads` as the origin or through the unlinked-pad
  step described under "Starting a pipeline".
- Error path, `pad->pipe`: set to NULL only on list entries before the failing
  one; the failing pad and every later pad keep their value, so a pad that
  gave `-EBUSY` stays in its other pipeline.
- Error path, list: `media_pipeline_cleanup()` then frees every
  `struct media_pipeline_pad`, including those after the failing one.
- `media_pipeline_walk_destroy()`: called at the end of
  `media_pipeline_populate()`, on success too; the validation error path does
  not call it.
- `media_pipeline_alloc_start()` on failure: frees the pipeline only when this
  call allocated it; a pipeline reused from `media_pad_pipeline()` is kept.

**Link validation for sub-devices**

- Sink entity not a sub-device: `WARN_ON_ONCE()` and `-EINVAL`.
- Source is a video device: the result is that of the source entity's
  `link_validate`.

  | Source video device | Result |
  |---|---|
  | `ops` or `link_validate` missing | `pr_warn_once()`, returns 0 |
  | `link_validate` is `v4l2_subdev_link_validate()` | `WARN_ON()`, `-EINVAL` |
  | otherwise | return of its `link_validate` |

- Source neither video device nor sub-device: `WARN_ON()` and `-EINVAL`.
- Locking: both active states come from
  `v4l2_subdev_get_unlocked_active_state()`; `v4l2_subdev_lock_states()` takes
  them only when both are non-NULL, sink first.
- Either active state NULL: nothing is held across the validation;
  `v4l2_subdev_link_validate_get_format()` and
  `__v4l2_link_validate_get_streams()` lock and unlock around each call with
  `v4l2_subdev_lock_and_get_active_state()`.
- Caller precondition: neither active-state lock may be held when the pipeline
  starts; `v4l2_subdev_get_unlocked_active_state()` has
  `lockdep_assert_not_held()`, and `v4l2_subdev_lock_states()` then does
  `mutex_lock()`.
- Stream masks: for a sub-device with `V4L2_SUBDEV_FL_STREAMS`, built per link
  end by `__v4l2_link_validate_get_streams()` from `for_each_active_route()`,
  under `CONFIG_VIDEO_V4L2_SUBDEV_API`; without the flag the mask is
  `BIT_ULL(0)`. `v4l2_subdev_has_pad_interdep()` is not called.
- Sink stream with no source stream of the same number: `dev_err()` and
  `-EINVAL`, before any format is read.
- Unreadable format: any negative return from `get_fmt` on either end skips
  that stream with `continue`, without an error.
- What counts as unreadable: also `-ENOIOCTLCMD` when the sub-device has no
  `get_fmt` op, and `-EINVAL` from `check_state()` when a
  `V4L2_SUBDEV_FL_STREAMS` sub-device has no format for that pad and stream.
- A skipped stream reaches neither the `link_validate` pad op nor
  `v4l2_subdev_link_validate_default()`.
- `v4l2_subdev_link_validate_default()`: compares `width`, `height`, `code`
  and `field` only; `field` also passes when the sink has `V4L2_FIELD_NONE`.
- `v4l2_subdev_link_validate_default()` does not compare `colorspace`,
  `ycbcr_enc`, `quantization`, `xfer_func` or stream numbers.

## Requests

**Request states**

- `media_request_lock_for_update()`: succeeds from
  `MEDIA_REQUEST_STATE_IDLE` and from `MEDIA_REQUEST_STATE_UPDATING`; it only
  counts in `updating_count`, so concurrent updaters all succeed.
- `MEDIA_REQUEST_STATE_UPDATING` keeps out `media_request_ioctl_queue()` and
  `media_request_ioctl_reinit()` (both `-EBUSY`), not a second updater; object
  contents need their own lock.
- `media_request_ioctl_reinit()`: accepts IDLE as well as COMPLETE.
- `media_request_lock_for_access()`: called in `.c` files only by
  `v4l2_g_ext_ctrls_request()` in
  `drivers/media/v4l2-core/v4l2-ctrls-request.c`, which returns `-EACCES` for
  a request that is not COMPLETE before it reaches the `-EBUSY` of the lock.
- Objects of a VALIDATING or QUEUED request: read with neither counter held;
  `v4l2_ctrl_request_hdl_find()` WARNs and returns NULL in any other state.
- `req_validate` op: runs in VALIDATING under `mdev->req_queue_mutex`;
  `vb2_request_validate()` walks `req->objects` there without `req->lock`.
- `media_request_object_find()` and `vb2_request_buffer_cnt()`: take
  `req->lock` for the list walk, usable in any state.
- `mdev->req_queue_mutex`: also taken by `media_request_ioctl_reinit()`, by
  `__video_do_ioctl()` for `VIDIOC_STREAMON`, `VIDIOC_STREAMOFF` and
  `VIDIOC_REQBUFS`, and by `v4l2_release()`, each V4L2 case only when
  `v4l2_device_supports_requests()` is true.
- `VIDIOC_QBUF` and `VIDIOC_S_EXT_CTRLS`: do not take `req_queue_mutex`; they
  rely on `media_request_lock_for_update()` alone.
- `req_queue_mutex`, on the paths that take it, is what keeps a vb2 cancel out
  of VALIDATING; `media_request_object_unbind()` WARNs and skips the count in
  that state.
- Lock order: `req_queue_mutex` first, then `q->lock`; see
  `__video_do_ioctl()` and `vb2_req_prepare()`.

**Manual completion**

- This tree has it: `media_request_mark_manual_completion()` in
  `include/media/media-request.h` and `media_request_manual_complete()` in
  `drivers/media/mc/mc-request.c`.
- `media_request_mark_manual_completion()`: a plain store to
  `req->manual_completion`, no lock, no state check.
- Call it in the `req_queue` op before the objects are queued, as
  `vicodec_request_queue()` does; `media_request_clean()` clears the flag, so
  it has to be set again on every queue.
- With the flag set, `media_request_object_complete()` and
  `media_request_object_unbind()` still count down but leave the request
  QUEUED at zero.
- `media_request_manual_complete()` returns after a `WARN_ON_ONCE()` if `req`
  is NULL, the flag is clear, or the state is not QUEUED; a second call
  therefore WARNs.
- `media_request_manual_complete()` with `num_incomplete_objects` non-zero:
  clears the flag, WARNs, does not complete; the request then completes
  automatically when the last object is completed or unbound.
- On success it sets COMPLETE, wakes `req->poll_wait` and drops the queue-time
  reference with `media_request_put()`.
- **Unsafe usage**: calling `media_request_manual_complete()` before every
  object of the request is completed or unbound.
  - Safe: return the buffer, then `v4l2_ctrl_request_complete()`, then
    `media_request_manual_complete()`, as `device_run()` in
    `drivers/media/test-drivers/vicodec/vicodec-core.c` does; the `WARN_ON()`
    on `req->num_incomplete_objects` defines the requirement.

**Controls in a request**

- `struct v4l2_ctrl_ref`: the request value is `p_req`, `p_req_valid` says the
  request holds a value, `req_done` is scratch for
  `v4l2_ctrl_request_setup()`; there is no field named req.
- No control flag makes a control mandatory in a request; a driver checks
  that in its `req_validate` op.
- `v4l2_ctrl_request_hdl_ctrl_find()`: returns NULL for a control the request
  did not set (`p_req_valid` false), not only for an unknown id.
- `v4l2_ctrl_request_setup()`: applies whole clusters; if any member has
  `p_req_valid` the other members are written with their current values.
- `v4l2_ctrl_request_setup()`: skips controls with
  `V4L2_CTRL_FLAG_READ_ONLY`.
- `v4l2_ctrl_request_setup()` return: 0 when the request has no control
  object, `-EBUSY` when the request is not QUEUED (with WARN) or the object is
  already completed.
- `v4l2_ctrl_request_complete()`: for `V4L2_CTRL_FLAG_VOLATILE` controls it
  calls `g_volatile_ctrl` and overwrites `p_req` even if the request set the
  control.
- `v4l2_ctrl_request_complete()` with `req` NULL: returns without doing
  anything.
- **Potentially unsafe usage**: calling `v4l2_ctrl_request_complete()` after
  the last buffer of the request was returned.
  - Unsafe: when the request is not marked for manual completion and holds no
    control object; the request is already COMPLETE, so
    `media_request_object_bind()` WARNs, returns `-EBUSY`, and no values are
    stored.
  - Safe: when the request is marked for manual completion and so still
    QUEUED, as `device_run()` in
    `drivers/media/test-drivers/vicodec/vicodec-core.c`.
  - Safe: complete the controls first, then return the buffer, as
    `vim2m_stop_streaming()` in `drivers/media/test-drivers/vim2m.c`.

**Request objects**

- Outside `drivers/media/mc/mc-request.c`, in `.c` files only
  `drivers/media/common/videobuf2/videobuf2-core.c` and
  `drivers/media/v4l2-core/v4l2-ctrls-request.c` call bind, unbind or
  complete; drivers reach them through vb2 and the control helpers.
- `media_request_object_bind()`: accepts `MEDIA_REQUEST_STATE_UPDATING` and
  `MEDIA_REQUEST_STATE_QUEUED`; any other state is a WARN and `-EBUSY`.
- Bind in QUEUED exists for `v4l2_ctrl_request_complete()`, which adds a
  control object to a request that had none.
- `media_request_object_bind()`: takes no request reference and no object
  reference; the reference from `media_request_object_init()` belongs to the
  binding.
- Every in-tree `media_request_object_unbind()`, except the one inside
  `media_request_object_release()`, is followed by
  `media_request_object_put()` to drop that reference.
- `media_request_object_put()` dropping the last reference of a still-bound
  object: `WARN_ON()`, then it unbinds.
- `media_request_object_complete()` on an already completed object: returns
  silently, no WARN.
- `media_request_object_complete()`: dereferences `obj->req` without a NULL
  check, so an unbound object oopses.
- `media_request_object_unbind()`: tests `obj->completed` only in CLEANING; in
  IDLE, UPDATING and QUEUED it decrements `num_incomplete_objects` without
  that test; in COMPLETE it leaves the count alone.
- **Unsafe usage**: unbinding an already completed object while the request
  is still QUEUED; the count drops twice and the request can complete early.
  - Safe: unbind without completing, as `vb2_buffer_done()` does for buffers.
  - Safe: complete and leave bound until `media_request_clean()` unbinds in
    CLEANING, as `v4l2_ctrl_request_complete()` does for controls.
- A request becomes COMPLETE in `media_request_object_complete()` or
  `media_request_object_unbind()` when it is QUEUED, the count reaches zero
  and `manual_completion` is clear; otherwise in
  `media_request_manual_complete()`.
- Completion calls `media_request_put()` for the queue-time reference in the
  caller's context; `vb2_core_qbuf()` holds an extra reference in
  `vb->request` until dequeue or cancel so that the put from
  `vb2_buffer_done()` is not the last one.

**Queues that use requests**

- `min_queued_buffers` must be 0 when `supports_requests` is set;
  `vb2_core_queue_init()` WARNs and returns `-EINVAL` otherwise.
- Missing `buf_request_complete`: detected only at the first request QBUF, in
  `vb2_queue_or_prepare_buf()` in
  `drivers/media/common/videobuf2/videobuf2-v4l2.c`, as WARN and `-EINVAL`.
- Missing `buf_out_validate`: same check, but only for queue types
  `V4L2_BUF_TYPE_VIDEO_OUTPUT` and `V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE`.
- Request QBUF runs `buf_out_validate` only (output queue, buffer not yet
  prepared); `buf_prepare` runs later, from `vb2_req_prepare()` during
  `MEDIA_REQUEST_IOC_QUEUE`.
- `vb2_request_validate()`: calls the `prepare` op of every object that has
  one; the control object's `req_ops` has none, so it validates no controls.
- A buffer prepared with `VIDIOC_PREPARE_BUF` can be queued in a request; it
  is in `VB2_BUF_STATE_DEQUEUED` and `vb2_core_qbuf()` skips
  `buf_out_validate` for it.
- `vb2_prepare_buf()`: refuses `V4L2_BUF_FLAG_REQUEST_FD` with `-EINVAL`.
- Request QBUF of a buffer not in `VB2_BUF_STATE_DEQUEUED`: `-EINVAL`;
  `-EBUSY` is what a direct QBUF gets while `uses_requests` is set and
  `requires_requests` is clear.
- `v4l2_m2m_qbuf()`: refuses a request on the capture queue with `-EPERM`.
- `uses_requests` and `uses_qbuf`: cleared in `__vb2_queue_cancel()`, reached
  from `vb2_core_streamoff()`, `vb2_core_queue_release()` and the freeing
  path of `vb2_core_reqbufs()`.
- `buf_request_complete`: called from `__vb2_queue_cancel()` only for a
  buffer whose request is in `MEDIA_REQUEST_STATE_QUEUED`; a buffer in an
  IDLE request is unbound without the callback.

## Model gaps

### Other mistakes models make

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
