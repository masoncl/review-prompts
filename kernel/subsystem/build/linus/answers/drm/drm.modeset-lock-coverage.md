- `mode_config.mutex` does not protect the object lists.
- `crtc_list`, `plane_list`, `encoder_list`, `property_list`: no lock, fixed
  once the device is registered.
- `connector_list`: `connector_list_lock`; `fb_list`: `fb_lock`.
- `mode_config.mutex` protects connector probe state: `connector->status`,
  `connector->modes`, `connector->probed_modes`, and use of
  `mode_config.acquire_ctx`.
- Asserts on `mode_config.mutex`: for example `check_connector_changed()` and
  `drm_helper_probe_single_connector_modes()` in
  `drivers/gpu/drm/drm_probe_helper.c`; search `mutex_is_locked(` for the
  rest.
- `connection_mutex` does not cover `connector->status`;
  `check_connector_changed()` writes it after `drm_helper_probe_detect()` has
  dropped `connection_mutex`.
- `drm_modeset_lock_all_ctx()` order: `connection_mutex`, every CRTC, every
  plane, every `struct drm_private_obj`; no `mode_config.mutex`.
- `drm_warn_on_modeset_not_all_locked()`: checks the CRTC locks,
  `connection_mutex` and `mode_config.mutex` only, not plane or private
  object locks.
- `drm_warn_on_modeset_not_all_locked()` after `drm_modeset_lock_all_ctx()`
  alone: warns, because `mode_config.mutex` is not held.
- `drm_modeset_is_locked()`: `ww_mutex_is_locked()`, true when any task holds
  the lock; `drm_modeset_lock_assert_held()` is the lockdep check for the
  caller.
- `struct drm_colorop` state: protected by the owning plane's `mutex`; see
  `drm_atomic_get_colorop_state()`.
