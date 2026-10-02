- Models take the HDMI `supported_formats` and `display_info.color_formats`
  bits to be `enum hdmi_colorspace` values or DRM_COLOR_FORMAT_RGB444-style
  masks. Here each bit is `BIT()` of an `enum drm_output_color_format` value
  from `include/drm/drm_connector.h`, for example
  `BIT(DRM_OUTPUT_COLOR_FORMAT_RGB444)`; 4:4:4 and 4:2:2 are in the opposite
  order to `enum hdmi_colorspace`, and DRM_COLOR_FORMAT_RGB444 is defined
  nowhere.
- Models take any `struct file_operations` with `drm_open()` to be enough.
  Here `drm_open_helper()` in `drivers/gpu/drm/drm_file.c` fails with
  `-EINVAL` unless `fop_flags` has `FOP_UNSIGNED_OFFSET`; `DRM_GEM_FOPS` sets
  it.
- Models take an allocation call with no GFP argument to be an error. Here
  `kzalloc_obj()`, `kmalloc_objs()`, `kzalloc_flex()` and `kvmalloc_objs()` in
  `include/linux/slab.h` default to `GFP_KERNEL` through `default_gfp()`.
- Models take `drm_atomic_private_obj_init()` to receive the initial state and
  return nothing. Here it takes `dev`, `obj` and `funcs`, returns int, and
  calls `funcs->atomic_create_state` without testing it for NULL.
- Models take `dma_fence_signal()` to return an error for a fence that has
  already signalled. Here it returns void; `dma_fence_check_and_signal()`
  returns true when the fence was signalled before the call.
- Models take HDMI infoframes to go through one write and one clear callback
  of the connector. Here `struct drm_connector_hdmi_funcs` has one
  `struct drm_connector_infoframe_funcs` per type.
- Models take the legacy plane colour properties to apply to every commit.
  Here `drm_mode_atomic_ioctl()` sets `plane_color_pipeline` in
  `struct drm_atomic_commit` for a client with
  `DRM_CLIENT_CAP_PLANE_COLOR_PIPELINE`; no core helper reads it. The only
  reader is `fill_plane_color_attributes()` in
  `drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c`, which skips
  `color_encoding` and `color_range` when the flag is set and
  `plane_state->state` is non-NULL.
