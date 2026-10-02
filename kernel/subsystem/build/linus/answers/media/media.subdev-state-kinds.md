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
