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
