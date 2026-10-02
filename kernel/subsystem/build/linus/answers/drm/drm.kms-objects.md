- Every `struct drm_connector` is reference counted, static ones included:
  `drm_connector_init_only()` in `drivers/gpu/drm/drm_connector.c` always
  installs `drm_connector_free()` as `free_cb`, so a connector returned by
  `drm_connector_lookup()` always needs `drm_connector_put()`.
- Hotplugged connector (DP MST): `drm_connector_dynamic_init()`, then
  `drm_connector_dynamic_register()`; removed with
  `drm_connector_unregister()` then `drm_connector_put()`.
- `drm_connector_init()`, `drm_connector_init_with_ddc()` and
  `drmm_connector_init()` put the connector on `connector_list` at once;
  `drm_connector_dynamic_init()` does not.
- `drm_connector_unregister()` leaves the id in the idr, so a lookup still
  returns the connector until the last reference goes; test with
  `drm_connector_is_unregistered()`.
- `struct drm_colorop` (`DRM_MODE_OBJECT_COLOROP`, `drm_colorop_find()`) is a
  mode object with device lifetime, not reference counted, like planes, CRTCs
  and encoders.
- Device lifetime is enforced by a `WARN_ON()` in `__drm_mode_object_add()` and
  `drm_mode_object_unregister()`: an object without `free_cb` added or removed
  once `dev->registered` is set warns, unless the driver has `load`.
- Lease check in `__drm_mode_object_find()`: `_drm_lease_held()`, not
  `drm_lease_held()`; applied only to the types in
  `drm_mode_object_lease_required()`; passes when `file_priv` is NULL.
- There is no drmm_plane_init() here; the only managed plane helper is
  `drmm_universal_plane_alloc()`.
- `drm_universal_plane_alloc()` is unmanaged: plain `kzalloc()`, the driver
  frees it with `kfree()`.
- **Potentially unsafe usage**: plain `drm_crtc_init_with_planes()`,
  `drm_universal_plane_init()` or `drm_encoder_init()` on memory the driver
  does not `kfree()` itself.
  - Unsafe: when the memory is freed before `drm_mode_config_cleanup()` runs,
    which calls `funcs->destroy` on every object still listed.
  - Safe: object embedded in the structure from `devm_drm_dev_alloc()`, with
    `destroy` set to the cleanup function only, as `gm12u320_usb_probe()` does
    through `drm_simple_display_pipe_init()`; `drm_dev_release()` frees
    `managed.final_kfree` after `drm_managed_release()`.
- **Unsafe usage**: a drmm-initialised object still on its `mode_config` list
  when `drm_mode_config_cleanup()` runs; it calls `funcs->destroy` with no
  NULL check.
  - Safe: `drmm_mode_config_init()` called before the drmm object helper, and
    no direct call of `drm_mode_config_cleanup()`, as `vkms_modeset_init()`
    does; `drm_managed_release()` releases in reverse order, so the object's
    cleanup action unlinks it first.
- **Unsafe usage**: dropping the last reference of a connector made with
  `drmm_connector_init()`; `drm_connector_free()` calls `funcs->destroy`,
  which is NULL.
  - Safe: dropping the last reference of a connector from
    `drm_connector_dynamic_init()`, which returns `-EINVAL` without
    `funcs->destroy`, as `drm_dp_delayed_destroy_port()` does.
