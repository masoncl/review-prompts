- Order in `drm_atomic_helper_commit_tail_rpm()`: modeset disables, modeset
  enables, then planes with `DRM_PLANE_COMMIT_ACTIVE_ONLY`; planes never run
  first.
- Planes skipped while their CRTC was inactive are not lost:
  `drm_atomic_helper_check_modeset()` calls `drm_atomic_add_affected_planes()`
  for every CRTC that needs a modeset, so their `atomic_update` runs after the
  enable.
- With `DRM_PLANE_COMMIT_ACTIVE_ONLY`, planes on a CRTC that goes inactive in
  the same commit get no `atomic_disable` or `atomic_update`:
  `plane_crtc_active()` reads the CRTC's current state, which is already the
  new one.
- With `DRM_PLANE_COMMIT_ACTIVE_ONLY`, `atomic_begin` and `atomic_flush` are
  skipped as well for a CRTC whose new state is inactive.
- Nothing in the helpers tests which tail a driver uses.
