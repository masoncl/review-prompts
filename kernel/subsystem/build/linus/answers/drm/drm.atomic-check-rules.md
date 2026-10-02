- `allow_modeset` is a field of `struct drm_atomic_commit`, not of
  `struct drm_crtc_state`.
- `drm_atomic_check_only()` enforces it, after the driver's `atomic_check`
  returned 0: `-EINVAL` if any CRTC in the update needs a modeset.
  `drm_atomic_helper_check_modeset()` never tests it.
- `drm_atomic_commit_init()` sets `allow_modeset` true, so in-kernel commits
  allow modesets by default; `page_flip_common()` clears it for the legacy
  page flip.
- `drm_self_refresh_helper_alter_state()`, the last step of
  `drm_atomic_helper_check()`, sets `allow_modeset` true when an old CRTC
  state has `self_refresh_active`.
- `drm_atomic_helper_check()` calls `drm_atomic_helper_check_modeset()` once;
  a driver that sets `mode_changed` later calls it again itself.
- `drm_atomic_helper_check()` does not call
  `drm_atomic_helper_check_plane_state()`; plane `atomic_check` hooks do.
- `drm_atomic_helper_check_modeset()` only sets `mode_changed`,
  `active_changed` and `connectors_changed`; it never clears them, so a flag
  the driver cleared comes back on a second call if the cause remains.
- After `-EDEADLK`, the `contended` field of
  `struct drm_modeset_acquire_ctx` is set; any further `drm_modeset_lock()`
  on that context hits `WARN_ON(ctx->contended)` in `modeset_lock()`.
- `DRM_MODESET_LOCK_ALL_END()` does not call `drm_atomic_commit_clear()`; it
  backs off and jumps back to `DRM_MODESET_LOCK_ALL_BEGIN()`, so the block
  between them runs again from its first line.
