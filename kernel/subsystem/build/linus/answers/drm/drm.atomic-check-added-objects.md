- `drm_atomic_check_only()` compares the CRTC mask before and after the
  driver's `atomic_check`; a difference logs at debug level and, with
  `allow_modeset` clear, also triggers `WARN()`.
- Both masks count only CRTCs whose new state has `enable` set; adding a
  disabled CRTC never trips the WARN.
- `drm_atomic_get_plane_state()` and `drm_atomic_get_connector_state()` also
  add the CRTC the object is currently on, so adding a plane or connector of
  another enabled CRTC counts as adding that CRTC.
- `checked` in `struct drm_atomic_commit` is set at the end of a successful
  `drm_atomic_check_only()`; from then on the CRTC, plane, connector and
  private object getters hit `drm_WARN_ON()`, and still proceed.
- `drm_atomic_get_colorop_state()` does not test `checked`.
- `drm_atomic_commit_default_clear()` resets `checked`.
- **Potentially unsafe usage**: adding an object from inside a helper's check
  loop.
  - Unsafe: when the loop already passed that object's index and its
    `atomic_check` hook has to run for this update; the hook never runs.
  - Safe: add before the loop starts, as `drm_atomic_helper_check_modeset()`
    does with `drm_atomic_add_affected_planes()` ahead of
    `drm_atomic_helper_check_planes()`; `for_each_oldnew_plane_in_state()`
    walks the array by index once.
  - Safe: loop again over what was added, as
    `drm_atomic_helper_check_modeset()` does with its second connector loop.
- A private object does not trip the CRTC WARN, and gets no commit ordering
  either: setup and the swap stall cover only CRTC, plane and connector
  states. See `atomic_commit_setup` under "Commit ordering and completions".
