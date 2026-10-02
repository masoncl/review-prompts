# What the media measurement found

Three models were asked the 88 questions in `media-measurement.md` with no
sources. A checker that had the sources then corrected each answer against a
mainline tree (kernel 7.3.0-rc5). The readers are labelled A, B and C; which
models they were does not matter here.

Reader A needed the fewest corrections and reader C the most. The check
rewrote 18% of what reader A wrote, 28% of what reader B wrote and 51% of what
reader C wrote. On every question at least one reader needed a correction.
The build set keeps 77 of the 88 questions.

The hand-written guide is 568 words about one subject: the checks that the
core makes before it calls a pad operation of a sub-device. It was never
checked against current sources. The measurement set covers the whole core,
so most of what the readers got wrong was never in the hand-written guide.

Every statement below about the tree was confirmed in the tree, unless the
sentence says "the check found".

## What all three readers got wrong

- **Every driver must use `struct v4l2_fh`.** `v4l2_open()` calls the `open`
  of the driver and then tests `V4L2_FL_USES_V4L2_FH`. If the flag is clear it
  warns, calls the `release` of the driver and returns `-ENODEV`.
  `v4l2_fh_init()` sets the flag. `__video_do_ioctl()` calls
  `file_to_v4l2_fh()` with no test and reads the result. Reader A said the flag
  no longer exists. Readers B and C said the core supports a driver with no
  file handle.
- **A failed `device_register()` does not run `release`.**
  `__video_register_device()` skips `put_device()` on that path and jumps to
  `cleanup`. It sets `vdev->dev.release` only after `device_register()` has
  succeeded. So `release` runs on no failure path, and the caller still owns
  the `struct video_device`. All three said the core calls `put_device()` and
  that `release` runs.
- **`__video_do_ioctl()` takes `req_queue_mutex` for `VIDIOC_REQBUFS` too**,
  and takes it before the lock that `v4l2_ioctl_get_lock()` returns. Readers
  A and B listed only `VIDIOC_STREAMON` and `VIDIOC_STREAMOFF`. Reader C left
  the mutex out.
- **The frame interval operations have no state wrapper.**
  `DEFINE_STATE_WRAPPER` is used for seven operations.
  `v4l2_subdev_call_pad_wrappers` installs `call_get_frame_interval()` and
  `call_set_frame_interval()` directly, so a NULL state stays NULL for them.
  With `CONFIG_MEDIA_CONTROLLER` off, the macro replaces no state at all. All
  three said that every operation that takes a state gets the locked active
  state in place of NULL.
- **`include/media/media-entity.h` has no stubs.** The header does not test
  `CONFIG_MEDIA_CONTROLLER` anywhere. `drivers/media/Makefile` builds
  `drivers/media/mc/` only when the symbol is `y`. All three described stubs
  or empty macros for the entity functions.
- **A NULL fwnode gives `-EPROBE_DEFER`.** The test for a NULL fwnode is the
  first test of `__v4l2_fwnode_endpoint_parse()`. The readers said `-EINVAL`,
  or that the pointer is dereferenced.
- **`v4l2_subdev_routing_validate()` returns `-ENXIO`** for a table that
  breaks a restriction. All three said `-EINVAL`.
- **`match_fwnode()` looks at `async_subdev_endpoint_list` first.** When that
  list is not empty, the function compares only the endpoints on the list and
  returns. All three described only the comparison with `sd->fwnode` and its
  secondary fwnode.
- **`__vb2_queue_cancel()` calls `unprepare_streaming` straight after
  `stop_streaming`**, before it looks for buffers that the driver still owns.
  All three had the order wrong. All three also listed `vb2_core_reqbufs()` as
  a path to `stop_streaming`. That function returns `-EBUSY` while
  `q->streaming` is set.
- **`media_devnode_unregister()` clears the minor and sets
  `devnode->media_dev` to NULL.** `media_devnode_release()` only calls
  `devnode->release` and frees the devnode. `devnode->release` is
  `media_device_release()`, which only prints a debug line. The readers put the
  clearing of the minor in `media_devnode_release()`, and said that an open
  file still reaches the `struct media_device` through the devnode.
- **The core zeroes the fields after a named field only for the ioctls that
  carry `INFO_FL_CLEAR`.** `VIDIOC_G_FMT`, `VIDIOC_S_FMT` and
  `VIDIOC_TRY_FMT` do not carry it, and their handlers clear the fields
  themselves. All three said that a driver always sees zeroed reserved fields.
- **Allocations use `kzalloc_obj()`.** All three wrote kzalloc(), for example
  for the `struct media_devnode` or for the `struct v4l2_fh` that
  `v4l2_fh_open()` allocates.
- **`Documentation/driver-api/media/camera-sensor.rst` names
  `pm_runtime_get_if_active()` only.** All three said the document names
  `pm_runtime_get_if_in_use()`. The document also says that
  `v4l2_ctrl_handler_setup()` may not be used in the `runtime_resume`
  callback. Reader C said the document puts the call there.

## What only some readers got wrong

### Readers B and C

- **The `priv` argument of an ioctl callback is NULL.** Every call in
  `drivers/media/v4l2-core/v4l2-ioctl.c` passes NULL, as in
  `ops->vidioc_querycap(file, NULL, cap)`. Both said the core passes
  `file->private_data`. The check found that the two event callbacks take a
  `struct v4l2_fh *` and get the file handle.
- **`v4l2_fh_add()` and `v4l2_fh_del()` take the file as a second argument**
  and set and clear `filp->private_data` themselves. Reader B gave both
  functions one argument. Both readers said that the driver or
  `v4l2_fh_open()` writes `private_data`.
- **The `lock` of a `struct vb2_queue` is required.**
  `vb2_core_queue_init()` warns and returns `-EINVAL` for a NULL `lock`. Both
  said the field is optional. The same function refuses `supports_requests`
  together with a non-zero `min_queued_buffers`, which reader C said it
  accepts.
- **The state accessors assert the lock on one path only.**
  `__v4l2_subdev_state_get_format()` returns from the `state->pads` branch
  before it reaches `lockdep_assert_held()`. It returns NULL with no warning
  for a pad out of range and for a stream other than 0. Both readers said that
  every accessor asserts the lock, and reader B said that an accessor warns
  for a wrong pad. Reader A had this right, and missed that
  `__v4l2_subdev_state_get_interval()` asserts the lock first.
- **`__v4l2_ctrl_handler_setup()` calls `s_ctrl` directly.** It does not go
  through `try_or_set_cluster()`. It skips buttons and read-only controls, and
  does not test for volatile controls.
- **`v4l2_m2m_buf_done_and_job_finish()` returns the destination buffer
  first**, then the source buffer. Both said source first.
- **There is no CONFIG_MEDIA_CONTROLLER_REQUEST_API.** The request stubs are
  under `CONFIG_MEDIA_CONTROLLER`.
- **`struct media_device` holds a pointer to its `struct media_devnode`.**
  `__media_device_register()` allocates the devnode. Both said it is embedded.
- **`v4l2_async_nf_try_complete()` walks up to the root notifier** and calls
  `complete` there only.
- **The core does not compare the size of a dma-buf with the plane length.**
  The `attach_dmabuf` operation of each allocator does, and returns
  `-EFAULT`.
- **`v4l2_subdev_link_validate()` hands a link whose source is a video device
  to the `link_validate` operation of that source.** Both said it returns 0
  without validating.
- **`media_create_pad_link()` takes no lock.** Both said links are added
  under `graph_mutex`. Reader A said every walk of the links needs the mutex;
  the check found correct code that walks without it.
- **`v4l2_get_link_freq()` returns `-ENOENT`** when it has to use the pixel
  rate and `mul` or `div` is 0. Both said `-EINVAL`.
- **`video_usercopy()` uses `kmalloc()` for a large argument** and
  `kvmalloc()` only for the array.
- **The format handlers clear with `memset_after()`.** Both named
  CLEAR_AFTER_FIELD().

### Readers A and C

- **`check_pad()` is always compiled.** Without `CONFIG_MEDIA_CONTROLLER` it
  accepts pad 0 only. Both said the pad check is compiled out.
- **`v4l2_get_link_freq()` takes a `struct media_pad *` as its first
  argument**, and is declared only with `CONFIG_MEDIA_CONTROLLER`. No variant
  takes a control handler, which both thought was still accepted. The function
  asks the `get_mbus_config` operation first, which reader C left out.
- **`__v4l2_async_register_subdev()` adds the sub-device to `subdev_list` on
  every success**, also when a notifier matched.

### Reader A

- `v4l2_ioctl_get_lock()` has no case for `VIDIOC_DQEVENT`, so the ioctl runs
  under `vdev->lock`. `v4l2_event_dequeue()` drops that lock while it waits.
  Reader A said the ioctl runs with no lock.
- `v4l2_ioctl_get_lock()` has no `#if`. Reader A said the branch for
  `q_lock` is compiled only with the memory-to-memory framework.
- `v4l2_subdev_lock_states()` locks two states. Reader A did not remember such
  a helper.
- `vb2_core_reqbufs()` sets `num_planes` to 0 before it calls `queue_setup`
  the second time. Reader A said the second call looks like the call for
  `VIDIOC_CREATE_BUFS`.
- The check found that `v4l_sanitize_format()` clamps `num_planes` and does
  not reject a value that is too large.
- `media_create_pad_link()` returns `-EINVAL` for a link type bit in `flags`.
  Reader A said the function clears the bit.

### Reader B

- Reader B had each of these the other way round. The check found that:
  - `video_unregister_device()` calls `v4l2_event_wake_all()` with no
    condition
  - `VIDIOC_QUERYCAP` is enabled only when the driver has the callback
  - `vb2_core_queue_init()` clamps `max_num_buffers`
  - `v4l2_subdev_release()` calls the `release` operation before
    `module_put()`
  - `vb2_core_streamon()` sets `q->streaming` after `start_streaming` has
    succeeded
- Reader B named video_translate_cmd(). The function is
  `v4l2_translate_cmd()`.
- The check found that `vb2_req_queue()` takes `q->lock`. Reader B said
  `buf_queue` on the request path runs without it.
- `media_request_object_bind()` accepts a request in the state
  `MEDIA_REQUEST_STATE_QUEUED` as well as one in
  `MEDIA_REQUEST_STATE_UPDATING`. Reader B said the bind fails unless the
  request is being updated. Readers A and C knew both states, and still said
  in another answer that every bind needs `media_request_lock_for_update()`.

### Reader C

- **`call_s_stream()` returns 0 for a second start**, after a warning, and
  does not call the driver. It also turns an error from a stop into 0. Reader C
  said `-EALREADY`, and that the error from a stop reaches the caller.
- **`v4l2_disable_ioctl()` sets a bit.** `determine_valid_ioctls()` inverts
  the set. The check found that a call after registration therefore enables
  the ioctl. Reader C said the function clears a bit.
- **`v4l2_device_register()` takes a reference on the parent device** with
  `get_device()`. The check found that `v4l2_device_unregister()` does not end
  with `v4l2_device_put()`.
- **`v4l2_open()` returns `-ENODEV` until `V4L2_FL_REGISTERED` is set**, which
  is the last step of registration. Reader C named the flag VIDEO_REGISTERED.
- **`v4l2_ctrl_handler_free()` returns an `int`.** Reader C said it returns
  nothing.
- **`media_request_manual_complete()` exists.** Reader C said it does not.
- **`v4l2_subdev_enable_streams_api` is a `static bool` that nothing sets.**
  Reader C called it a module parameter. All four reads of it are in
  `subdev_do_ioctl()`.
- **`__v4l2_subdev_init_finalize()` reads `sd->ctrl_handler` only to set
  `V4L2_SUBDEV_FL_HAS_EVENTS`.** The lock of a state is `sd->state_lock` if
  the driver set it, and the `_lock` of the state otherwise. Reader C said the
  lock of the control handler becomes the lock of the state.
- **`v4l2_ioctl_get_lock()` tries `m2m_ctx->q_lock` first**, then
  `vdev->queue->lock`, both only for ioctls with `INFO_FL_QUEUE`, and
  `vdev->lock` last. Reader C had the order reversed.
- **`v4l2_subdev_link_validate_default()` compares width, height, code and
  field.** Reader C said it compares the colorimetry fields.
- **`__media_entity_setup_link()` returns `-EINVAL` when any flag other than
  `MEDIA_LNK_FL_ENABLED` differs**, and tests `media_pad_is_streaming()` on
  both pads. Reader C said the test is a stream count of the entity.
- **Every ioctl of the media device node but the request allocation runs
  under `graph_mutex`.**
- Reader C had each of these the other way round. The check found that:
  - `__v4l2_subdev_state_alloc()` calls `init_state` itself
  - the ioctl helpers of videobuf2, such as `vb2_ioctl_qbuf()`, take no lock
  - the core never calls `v4l2_subdev_routing_validate()`
  - `v4l2_subdev_routing_find_opposite_end()` also matches a route that is
    not active
  - an interface link is never on the `links` list of an entity
  - `cluster_changed()` never counts a volatile control as changed
- `struct vb2_ops` has no `wait_prepare` or `wait_finish` member, and
  `__vb2_wait_for_done_vb()` unlocks and locks `q->lock` itself. Reader C
  described helpers named vb2_ops_wait_prepare() and vb2_ops_wait_finish().
- Names that reader C gave and that no source file of the tree defines:
  V4L2_FL_LOCK_ALL_FOPS, v4l2_ioctl_m2m_queue_is_output(),
  v4l2_subdev_call_until_err(), v4l2_subdev_lock_active_state(),
  v4l2_subdev_enable_streams_fallback(), v4l2_async_nf_add_subdev(),
  v4l2_m2m_update_stop_state(), min_buffers_needed, INFO_FL_STD, INFO_FL_FUNC
  and a file request-api.rst under `Documentation/driver-api/media/`.

## What a reader said it did not know

- Reader A marked many statements with "I believe". Most of them were right,
  and the check only removed the hedge.
- Reader A was not sure whether the frame interval operations have a state
  wrapper, whether `_vb2_fop_release()` releases a queue that has no owner,
  and what `v4l2_ctrl_handler_free()` returns for a handler whose
  initialisation failed.
- Reader B was not sure whether unregistering a sub-device removes the
  controls that the sub-device gave to the parent. The check found that
  unregistering does not remove them.
- Reader C was not sure how `v4l2_subdev_call()` reaches the wrappers, where
  `buf_init` is called, or whether a notifier may get a connection after it
  is registered.

## What the readers already knew

- What the main objects are, apart from the devnode of the media device.
- The current names of the async functions and of
  `struct v4l2_async_connection`.
- The fields of `struct vb2_queue` that count buffers, and that
  `vb2_get_buffer()` can return NULL for an index in the range.
- The three sets of memory operations and what `vb2_plane_vaddr()` returns
  for a plane with no mapping.
- The states of a buffer and that the driver owns a buffer in the active
  state.
- What the graph helpers return on failure.
- Which helper reads or sets a control of which type.
- That `v4l2_subdev_call()` returns `-ENODEV` for a NULL sub-device and
  `-ENOIOCTLCMD` for an operation that is not implemented.
- That a pipeline starts from a pad and is recorded in `pad->pipe`.
- Which header of the userspace API holds what, and which test driver
  exercises which part of the core.

## Where the hand-written guide is stale

No statement in the hand-written guide, `media.md`, was found wrong. Each of
these was confirmed in `drivers/media/v4l2-core/v4l2-subdev.c`:

- `call_enum_mbus_code()` calls `check_state()` before the operation of the
  driver.
- `call_get_fmt()` and `call_set_fmt()` reach `check_state()` through
  `check_format()`.
- For a sub-device with `V4L2_SUBDEV_FL_STREAMS`, `check_state()` returns
  `-EINVAL` when `v4l2_subdev_state_get_format()` returns NULL, and returns
  `-EINVAL` for every call when `CONFIG_VIDEO_V4L2_SUBDEV_API` is off.

The guide is incomplete in four places:

- **The call macros of `include/media/v4l2-device.h` skip the checks.**
  `__v4l2_device_call_subdevs_p()` calls `sd->ops` directly, so
  `v4l2_device_call_all()` never reaches `check_state()`. The guide tells a
  reviewer to look for callers that go around the wrapper and does not name
  this one.
- **`check_state()` accepts a NULL state.** For a sub-device without
  `V4L2_SUBDEV_FL_STREAMS` it tests the state only when `which` is
  `V4L2_SUBDEV_FORMAT_TRY`. The guide describes only the streams case.
- **Userspace cannot send a stream id.** `v4l2_subdev_enable_streams_api` is
  false, so `subdev_do_ioctl()` never lets a file claim
  `V4L2_SUBDEV_CLIENT_CAP_STREAMS`, and it sets the `stream` field of an
  argument to 0 before it calls the driver.
- **A wrapper may check a state that it fetched itself.** For seven
  operations, and only with `CONFIG_MEDIA_CONTROLLER`, the wrapper replaces a
  NULL state by the locked active state before the checks run.

About half of the guide tells a reviewer what to do: the four numbered steps
to take before dismissing a NULL dereference, the two paragraphs after them
about keeping a concern, and the four quick checks. A built guide says how the
tree is and holds no instruction, so the build set has no question for them.
`media.subdev-wrappers`, `media.subdev-call-paths`,
`media.subdev-argument-checks` and `media.subdev-state-accessors` ask for the
facts that those instructions depend on.

The guide holds no convention of the maintainers that the code does not
state, such as a subject prefix or a coding style. So the build set has no
verbatim item.

## What is left out of the build set, and why

| Question | Why it is left out |
|---|---|
| `media.objects` | `media.overview` asks the same thing and replaces it. `media.mc-device-lifecycle` asks who allocates the devnode, which readers B and C had wrong |
| `media.uapi-headers` | every reader placed each family of names in the right header. The check replaced wildcard names |
| `media.test-drivers` | every reader knew the test drivers. The corrections were about tools that are not in the tree and about the wording of the maintainer profile |
| `media.async-names` | every reader gave the current names. What reader C had wrong were the members of a structure, which a search shows |
| `media.async-sensor` | every reader knew what the helper adds and who frees it. The corrections completed a list of properties, which a search shows |
| `media.ctrl-driver-access` | every reader chose the right helper for each type |
| `media.vb2-buffer-counts` | every reader gave the three fields and knew that an index can have no buffer |
| `media.vb2-memory-ops` | every reader knew the memory operations and that the mapping helpers can return NULL |
| `media.vb2-buffer-states` | every reader knew which state means that the driver owns the buffer. `media.vb2-buffer-done`, `media.vb2-start-streaming` and `media.vb2-stop-streaming` ask what a driver must do in each state |
| `media.m2m-objects` | every reader knew the two objects and that the functions return an error pointer. `media.m2m-locking` asks about the one failure that two readers left out |
| `media.mc-return-values` | every reader gave the right kind of return value for each helper |

Each of these had corrections, as the numbers show. For each, the corrections
would not change what a review concludes.

## The numbers

Share of each answer from memory that the check rewrote, with the number of
corrections in brackets. Rewritten counts rewording too, so the corrections
are what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A          391        18%     34      1   6.12 to 6.18
reader B          423        28%     17     20   6.12 to 6.18
reader C          474        51%      0     63   6.12 to 6.16

question                            reader A      reader B      reader C   verdict
media.core-files                    12% ( 9)      10% ( 7)      38% (12)   middling
media.objects                       12% ( 5)      12% ( 5)      47% ( 5)   weak: reader C
media.docs                          14% ( 3)      24% ( 4)      34% ( 3)   middling
media.uapi-headers                  31% ( 3)      27% ( 2)      40% ( 1)   weak: reader C
media.test-drivers                  27% ( 6)      39% ( 2)      38% ( 4)   middling
media.config-symbols                27% ( 8)      58% ( 7)      84% ( 5)   weak: reader B, reader C
media.vdev-register                 17% ( 5)      12% ( 8)      62% (11)   weak: reader C
media.vdev-register-failure         51% ( 3)      74% ( 5)      53% ( 4)   all weak
media.vdev-release                  22% ( 3)      29% ( 4)      31% ( 4)   middling
media.vdev-unregister               23% ( 5)      20% ( 5)      72% ( 6)   weak: reader C
media.valid-ioctls                  24% ( 4)      27% ( 5)      55% ( 4)   weak: reader C
media.v4l2-device-lifetime          14% ( 4)      22% ( 5)      71% ( 5)   weak: reader C
media.fh-use                        34% ( 7)      60% ( 8)      80% (12)   weak: reader B, reader C
media.fh-lifecycle                  29% ( 7)      41% (11)      41% ( 8)   weak: reader B, reader C
media.ioctl-priv-argument           21% ( 4)      51% ( 8)      61% ( 8)   weak: reader B, reader C
media.ioctl-locking                 16% ( 5)      21% ( 5)      69% ( 7)   weak: reader C
media.ioctl-usercopy                10% ( 4)      34% ( 7)      58% ( 6)   weak: reader C
media.ioctl-sanitize                19% ( 5)      29% ( 5)      53% ( 5)   weak: reader C
media.compat-ioctl                  26% ( 6)      31% ( 7)      51% ( 6)   weak: reader C
media.subdev-init                   12% ( 4)      39% (11)      59% ( 7)   weak: reader C
media.subdev-register                2% ( 2)      20% ( 3)      49% ( 4)   weak: reader C
media.subdev-release                29% ( 5)      36% ( 4)      42% ( 4)   weak: reader C
media.subdev-devnode                16% ( 7)      16% ( 2)      65% ( 3)   weak: reader C
media.subdev-node-ioctls            15% ( 8)      18% ( 5)      46% ( 3)   weak: reader C
media.subdev-call                   25% ( 4)      43% ( 6)      46% ( 8)   weak: reader B, reader C
media.subdev-wrappers               11% ( 7)      28% ( 5)      53% ( 5)   weak: reader C
media.subdev-call-paths             21% ( 5)      20% ( 2)      71% ( 3)   weak: reader C
media.subdev-argument-checks        11% ( 5)      33% ( 5)      70% ( 5)   weak: reader C
media.subdev-state-kinds            24% ( 8)      13% ( 6)      38% ( 8)   middling
media.subdev-state-accessors        30% ( 4)      47% ( 5)      38% ( 4)   weak: reader B
media.subdev-state-locking          30% ( 6)       6% ( 2)      39% ( 5)   middling
media.subdev-frame-interval         30% ( 6)      13% ( 3)      33% ( 4)   middling
media.subdev-streams-enabled         8% ( 7)      24% ( 6)      76% ( 8)   weak: reader C
media.subdev-routing                16% ( 6)      33% ( 8)      55% ( 5)   weak: reader C
media.subdev-routing-lookups        14% ( 3)      26% ( 2)      51% ( 1)   weak: reader C
media.subdev-enable-streams          6% ( 2)      25% ( 6)      78% ( 4)   weak: reader C
media.subdev-s-stream               27% ( 4)      32% ( 4)      70% ( 4)   weak: reader C
media.async-names                    9% ( 1)       2% ( 4)      23% ( 4)   middling
media.async-notifier-lifecycle      21% ( 1)      26% ( 4)      52% ( 8)   weak: reader C
media.async-subdev-register         24% ( 3)      30% ( 3)      64% ( 6)   weak: reader C
media.async-callbacks                5% ( 2)      15% ( 3)      54% ( 6)   weak: reader C
media.async-sensor                  13% ( 6)      14% ( 5)      25% ( 5)   middling
media.fwnode-endpoint               29% ( 7)      38% (10)      48% ( 8)   weak: reader C
media.link-frequency                 9% ( 2)      18% ( 4)      51% ( 6)   weak: reader C
media.sensor-clock                   9% ( 4)      50% ( 7)      68% ( 5)   weak: reader B, reader C
media.sensor-power                  36% ( 7)      31% ( 4)      69% ( 7)   weak: reader C
media.ctrl-handler-lifecycle        16% ( 6)      18% ( 7)      36% ( 4)   middling
media.ctrl-locking                   0% ( 0)      37% ( 3)      34% ( 4)   middling
media.ctrl-ops                       3% ( 1)      18% ( 4)      25% ( 4)   middling
media.ctrl-clusters                  9% ( 2)       0% ( 0)      34% ( 4)   middling
media.ctrl-handler-setup            18% ( 3)      45% ( 4)      65% ( 6)   weak: reader B, reader C
media.ctrl-inheritance               6% ( 3)      15% ( 2)      57% ( 3)   weak: reader C
media.ctrl-driver-access             7% ( 4)      13% ( 4)      33% ( 2)   middling
media.ctrl-requests                  5% ( 2)      29% ( 4)      46% ( 7)   weak: reader C
media.vb2-queue-init                 4% ( 2)      22% ( 6)      70% (14)   weak: reader C
media.vb2-buffer-counts             16% ( 3)      27% ( 3)      29% ( 5)   middling
media.vb2-queue-setup               11% ( 3)      18% ( 5)      30% ( 2)   middling
media.vb2-memory-ops                13% ( 1)      15% ( 2)      28% ( 2)   middling
media.vb2-imported-buffers          26% ( 8)      32% ( 6)      38% ( 4)   middling
media.vb2-buffer-states             21% ( 6)      36% ( 7)      36% ( 4)   middling
media.vb2-callback-order            11% ( 3)      41% ( 4)      57% ( 6)   weak: reader B, reader C
media.vb2-start-streaming           28% ( 2)      57% ( 5)      45% ( 2)   weak: reader B, reader C
media.vb2-stop-streaming            27% ( 4)      41% ( 3)      40% ( 4)   weak: reader B, reader C
media.vb2-buffer-done               33% ( 4)      32% ( 3)      55% ( 5)   weak: reader C
media.vb2-locking                   26% ( 4)      50% ( 4)      47% ( 6)   weak: reader B, reader C
media.vb2-queue-owner               17% ( 2)      24% ( 2)      52% ( 4)   weak: reader C
media.vb2-release                   19% ( 3)      53% ( 2)      59% ( 3)   weak: reader B, reader C
media.vb2-requests                  12% ( 4)      26% ( 1)      65% ( 5)   weak: reader C
media.m2m-objects                   22% ( 5)      35% ( 9)      39% ( 6)   middling
media.m2m-scheduling                22% ( 3)      20% ( 3)      54% ( 5)   weak: reader C
media.m2m-job-finish                20% ( 3)      30% ( 5)      49% ( 6)   weak: reader C
media.m2m-locking                   33% ( 7)      44% ( 3)      79% ( 7)   weak: reader B, reader C
media.m2m-draining                  17% ( 5)      34% ( 7)      77% ( 8)   weak: reader C
media.mc-device-lifecycle           30% ( 9)      26% ( 7)      74% ( 8)   weak: reader C
media.mc-entity-register            10% ( 3)      17% ( 3)      47% ( 3)   weak: reader C
media.mc-link-kinds                 24% ( 4)      40% ( 3)      33% ( 3)   weak: reader B
media.mc-return-values               2% ( 1)      12% ( 1)      27% ( 2)   middling
media.mc-setup-link                  0% ( 0)       9% ( 1)      83% ( 4)   weak: reader C
media.mc-graph-mutex                16% ( 4)      50% ( 4)      57% ( 4)   weak: reader B, reader C
media.mc-pipeline-start             19% ( 5)       9% ( 2)      23% ( 8)   middling
media.mc-pipeline-validation         7% ( 2)       0% ( 0)      44% ( 4)   weak: reader C
media.mc-subdev-link-validate       16% ( 3)      24% ( 6)      70% ( 5)   weak: reader C
media.req-lifecycle                 24% ( 7)      57% (11)      53% ( 8)   weak: reader B, reader C
media.req-objects                   25% ( 7)      44% (10)      55% ( 7)   weak: reader B, reader C
media.req-manual-completion         27% ( 5)      50% ( 4)      91% ( 2)   weak: reader B, reader C
media.events                        15% ( 9)      31% ( 8)      29% ( 8)   middling
media.uapi-compatibility            17% ( 9)      19% (11)      49% (14)   weak: reader C
media.format-negotiation            28% ( 8)      27% ( 5)      48% ( 6)   weak: reader C
```

The verdict column calls a reader weak on a question when the check rewrote
40% or more of the answer of that reader.

## Questions reorganised

The build set has 79 questions: 77 from the measurement set, `media.overview`
and `media.model-gaps`.

| The check rewrote | Questions | Kept |
|---|---|---|
| 40% or more of the answer of at least one reader | 65 | 63. `media.objects` and `media.uapi-headers` are left out, for the reasons in the table above |
| less than 40% of the answer of every reader | 23 | 14. `media.core-files` and `media.docs` map the tree. The other twelve are in the next table |

Each of these twelve is kept because a correction changes what a review
concludes. The second column says what the check found.

| Question | What a reader had wrong |
|---|---|
| `media.vdev-release` | reader B said that the `poll` and `mmap` operations of the driver still run after the device is unregistered |
| `media.subdev-state-kinds` | reader C said that `__v4l2_subdev_state_alloc()` does not call `init_state` |
| `media.subdev-state-locking` | reader A said that a NULL state is replaced by the locked active state for every operation that takes a state |
| `media.subdev-frame-interval` | reader A said that the frame interval operations have a state wrapper |
| `media.ctrl-handler-lifecycle` | reader C said that `v4l2_ctrl_handler_free()` returns nothing |
| `media.ctrl-locking` | readers B and C said that a call to `v4l2_ctrl_s_ctrl()` from an `s_ctrl` operation always deadlocks. It does not when the control belongs to another handler |
| `media.ctrl-ops` | reader C said that a volatile control always counts as changed |
| `media.ctrl-clusters` | reader C said that every entry of the array passed to `v4l2_ctrl_cluster()` must be set. Only the first must |
| `media.vb2-queue-setup` | readers B and C said that the core checks the largest number of planes that `queue_setup` may return |
| `media.vb2-imported-buffers` | readers B and C said that the core compares the size of a dma-buf with the plane length |
| `media.mc-pipeline-start` | reader C said that a start from a pad of another pipeline returns `-EBUSY`, and that a disabled link adds no pad |
| `media.events` | reader C said that the core calls `merge` in place of dropping the oldest event |

The build set is organised by subject, and every question of a part names the
part as its section:

| Part | Questions |
|---|---|
| Main structures | 1 |
| Where to look | 3 |
| Video devices | 6 |
| File handles | 4 |
| Ioctl dispatch | 6 |
| Sub-device registration | 4 |
| Calling sub-device operations | 6 |
| Sub-device state | 3 |
| Streams and routing | 5 |
| Async registration | 3 |
| Firmware and sensors | 4 |
| Control framework | 6 |
| videobuf2 | 10 |
| Memory-to-memory devices | 4 |
| Media controller graph | 5 |
| Pipelines | 3 |
| Requests | 5 |
| Model gaps | 1 |

These questions moved to another part, so that one call to the builder
answers everything about a subject:

| Question | From | To | Reason |
|---|---|---|---|
| `media.ioctl-priv-argument` | Ioctl dispatch | File handles | the answer is about how a callback reaches the file handle |
| `media.events` | Events | File handles | the event lists belong to the file handle |
| `media.uapi-compatibility`, `media.format-negotiation` | Compatibility | Ioctl dispatch | both are about what the dispatcher clears and what it leaves to the driver |
| `media.subdev-node-ioctls` | Subdev registration | Calling sub-device operations | the answer is about what a pad operation receives |
| `media.subdev-frame-interval` | Subdev state | Calling sub-device operations | what the readers had wrong is whether these operations have a state wrapper |
| `media.vb2-requests`, `media.ctrl-requests` | videobuf2, Controls | Requests | the readers disagreed on the order of completing a request across these answers |

The two videobuf2 sections of the measurement set are one part, since both
ask whether the queue lock is optional.

Three questions ask something different from what was measured. Every other
question asks what was measured.

| Question | What changed | Why |
|---|---|---|
| `media.subdev-wrappers` | it no longer asks what each wrapper checks | `media.subdev-argument-checks` asks that in the same part |
| `media.vb2-queue-init` | it asks for the requirements for the queue, not for the fields a driver must set | a question does not ask for a list of fields |
| `media.vb2-requests` | it asks for the requirements for a queue that uses requests, not for the fields that say so | a question does not ask for a list of fields |

## Wording after the measurement

After the measurement, the wording of some questions was made clearer in both
sets: a sentence that asked three things became two sentences, and a pronoun
became the name it stood for. What each question asks did not change, so the
numbers above still describe the questions.
