- `drm_atomic_helper_prepare_planes()`: two passes. `prepare_fb` runs on
  every plane in the commit, then `begin_fb_access` runs on every plane.
- `prepare_fb` failure: `cleanup_fb` on the planes before the failing one;
  no `end_fb_access` call.
- `begin_fb_access` failure: `end_fb_access` on the planes before the
  failing one, then `cleanup_fb` on every plane in the commit.
- Planes whose new state has `fb == NULL`: get all four hooks too; the loops
  have no fb test.
- No `prepare_fb` hook: `drm_gem_plane_helper_prepare_fb()` is called when
  the driver has `DRIVER_GEM`; a `cleanup_fb` without `prepare_fb` hits
  `WARN_ON_ONCE()`.
- `begin_fb_access`: called only from `drm_atomic_helper_prepare_planes()`,
  before the swap, never from the commit tail.
- `end_fb_access` in the tail: last step of
  `drm_atomic_helper_commit_planes()`, after `atomic_flush` and before
  `drm_atomic_helper_commit_hw_done()`.
- `end_fb_access` on abort: `drm_atomic_helper_unprepare_planes()` and the
  failure path of `drm_atomic_helper_prepare_planes()` pass the new state.
- `drm_atomic_helper_commit_planes_on_crtc()`: does not call
  `end_fb_access`.
- Async update (`state->async_update` in `drm_atomic_helper_commit()`):
  prepare, `drm_atomic_helper_async_commit()`, then
  `drm_atomic_helper_unprepare_planes()` at once. `cleanup_fb` gets the
  commit's plane state, into which `atomic_async_update` must have swapped
  the old fb; see the `WARN_ON_ONCE()` in `drm_atomic_helper_async_commit()`.
- Fence storage: there is no drm_atomic_set_fence_for_plane() here;
  `drm_gem_plane_helper_prepare_fb()` writes `state->fence` itself.
- `drm_gem_plane_helper_prepare_fb()` with `state->fence` already set: adds
  only `DMA_RESV_USAGE_KERNEL` fences, chained to the explicit fence.
  Without one it takes `DMA_RESV_USAGE_WRITE` fences.
- `drm_gem_plane_helper_prepare_fb()` errors: `-EINVAL` when a framebuffer
  plane has no GEM object, `-ENOMEM` when the chain allocation or
  `dma_resv_get_singleton()` fails.
- Fence wait on a blocking commit: `drm_atomic_helper_commit()` calls
  `drm_atomic_helper_wait_for_fences()` before the swap, interruptibly; an
  error unprepares the planes and fails the commit. The call in
  `commit_tail()` then finds `fence` already NULL.
