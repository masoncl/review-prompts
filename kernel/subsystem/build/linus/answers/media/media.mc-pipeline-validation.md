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
