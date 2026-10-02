- amdgpu's own choice: `RMX_ASPECT`, not full screen.
- `dm_encoder_helper_atomic_check()` in
  `drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm_connector.c`: for eDP and
  LVDS, when the adjusted mode differs in size from the native mode and the
  state holds `RMX_OFF`, it writes `RMX_ASPECT` into the new connector state.
- After that rewrite `amdgpu_dm_connector_atomic_get_property()` reports
  `DRM_MODE_SCALE_ASPECT`, since it reads the same `scaling` field.
- `amdgpu_dm_update_stream_scaling_settings()`: puts `RMX_OFF` and `RMX_ASPECT`
  in the same branch; `RMX_FULL` keeps the full addressable area; `RMX_CENTER`
  sets destination equal to source.
- There is no update_stream_scaling_settings() here;
  `amdgpu_dm_update_stream_scaling_settings()` in `amdgpu_dm_connector.c` does
  that.
- `amdgpu_dm_connector_atomic_set_property()`: is in `amdgpu_dm_connector.c`,
  not `amdgpu_dm.c`.
- amdgpu does not call `drm_connector_attach_scaling_mode_property()`; it
  attaches the device-wide `mode_config.scaling_mode_property` from
  `drm_mode_create_scaling_mode_property()`.
- `scaling_mode` in `struct drm_connector_state`: not written for amdgpu; the
  value is `scaling` in `struct dm_connector_state`.
- Legacy path in `amdgpu_connectors.c`: LVDS and eDP attach the property with
  default `DRM_MODE_SCALE_FULLSCREEN`; other connector types that attach it use
  `DRM_MODE_SCALE_NONE`.
