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
