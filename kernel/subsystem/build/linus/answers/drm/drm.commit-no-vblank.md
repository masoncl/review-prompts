- `drm_atomic_helper_fake_vblank()` acts only on a CRTC whose new state has
  `no_vblank` set and a non-NULL `event`; it completes `flip_done` only.
- `hw_done` and `cleanup_done` are signalled as for any other commit.
- `no_vblank` is written by `drm_atomic_helper_check_modeset()` for every CRTC
  in the update, on every call: true when `drm_dev_has_vblank()` is false.
- `drm_dev_has_vblank()` is per device, not per CRTC; it is true once
  `drm_vblank_init()` ran.
- **Potentially unsafe usage**: a driver writing `no_vblank` itself.
  - Unsafe: before a call of `drm_atomic_helper_check_modeset()`, which
    overwrites the value.
  - Safe: in a plane or CRTC `atomic_check` hook when no later call of
    `drm_atomic_helper_check_modeset()` follows; `drm_atomic_helper_check()`
    runs these hooks from `drm_atomic_helper_check_planes()` after
    check_modeset, as `vc4_txp_atomic_check()` relies on.
- A driver may send the event itself and set `new_crtc_state->event` to NULL;
  the helper then skips that CRTC.
- A custom `atomic_commit_tail` gets no fake vblank unless it calls
  `drm_atomic_helper_fake_vblank()` before hw_done, as
  `vkms_atomic_commit_tail()` does.
- An event still set at `drm_atomic_helper_commit_hw_done()` trips its
  `WARN_ON(new_crtc_state->event)`; no helper sends the event after that
  point.
- Alternative with `drm_vblank_init()`: the vblank timer helpers in
  `drivers/gpu/drm/drm_vblank_helper.c`; `no_vblank` stays false and
  `drm_crtc_vblank_atomic_flush()` arms or sends the event. In
  `include/drm/drm_vblank_helper.h`, `DRM_CRTC_VBLANK_TIMER_FUNCS` drives
  `drm_crtc_handle_vblank()` from an hrtimer, started by
  `drm_crtc_vblank_start_timer()`, and `DRM_CRTC_HELPER_VBLANK_FUNCS`
  supplies the matching `atomic_enable`, `atomic_disable` and `atomic_flush`.
