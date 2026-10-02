- Async path (`async_update` set): `drm_atomic_helper_prepare_planes()`,
  `drm_atomic_helper_async_commit()`, `drm_atomic_helper_unprepare_planes()`,
  return 0. It runs no setup, no swap and no `commit_tail()`.
- Fence waits: a blocking commit calls `drm_atomic_helper_wait_for_fences()`
  before the swap with `pre_swap` true; `commit_tail()` calls it again for
  every commit with `pre_swap` false.
- Nonblocking commits are queued as `commit_work` on `system_dfl_wq`, not on
  `system_unbound_wq`.
- `drm_atomic_helper_commit_tail()` passes flags 0 to
  `drm_atomic_helper_commit_planes()`; the default tail never passes
  `DRM_PLANE_COMMIT_ACTIVE_ONLY`.
- **Unsafe usage**: dereferencing a new object state after
  `drm_atomic_helper_commit_hw_done()`, through `new_state` in the container
  or through `obj->state`.
  - Unsafe: a later commit only stalls for `hw_done` in
    `drm_atomic_helper_swap_state()`; once it finishes it destroys this
    commit's new states as its own `state_to_destroy`.
  - Safe: before `drm_atomic_helper_commit_hw_done()`, when the swap ran with
    `stall` true, as `plane_crtc_active()` does for
    `drm_atomic_helper_commit_planes()`.
  - Safe: old states at any point of the tail, as
    `drm_atomic_helper_cleanup_planes()` does.
  - Safe: a value copied out before the hook runs, as `commit_tail()` does
    with `new_self_refresh_mask`.
  - Safe: `state->crtcs[i].commit`, which holds its own reference, as
    `drm_atomic_helper_wait_for_flip_done()` does.
