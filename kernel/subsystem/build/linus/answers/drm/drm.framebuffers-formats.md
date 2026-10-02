- `fb_create` in `struct drm_mode_config_funcs` takes four arguments:
  `dev`, `file_priv`, `const struct drm_format_info *info`,
  `const struct drm_mode_fb_cmd2 *mode_cmd`.
- `drm_get_format_info()` takes `(dev, pixel_format, modifier)`; the core
  passes `r->modifier[0]`, and the `get_format_info` hook gets no `dev`.
- `framebuffer_check()` runs against the info from `drm_get_format_info()`,
  which is the driver's when `get_format_info` returns one, so plane count and
  block sizes are then the driver's.
- `drm_internal_framebuffer_create()` never calls
  `drm_any_plane_has_format()`.
- `drm_gem_fb_init_with_funcs()` calls `drm_any_plane_has_format()`, only when
  `drm_drv_uses_atomic_modeset()`; an `fb_create` that does not go through
  this helper gets no such check from the core.
- There is no allow_fb_modifiers here; the field is
  `mode_config.fb_modifiers_not_supported`.
- `drm_mode_addfb2()` puts the fb on `file_priv->fbs`;
  `drm_internal_framebuffer_create()` does not, and
  `drm_mode_cursor_universal()` calls it directly.
- Pitch check in `framebuffer_check()`: skipped when
  `info->char_per_block[i]` is 0; such a plane is rejected with
  `DRM_FORMAT_MOD_LINEAR` instead.
- Unused planes in `framebuffer_check()`: modifier must always be 0; handle,
  pitch and offset must be 0 only when `DRM_MODE_FB_MODIFIERS` is set.
- Size check in `drm_gem_fb_init_with_funcs()`: object size at least
  `(height - 1) * pitch + drm_format_info_min_pitch() + offset`, with plane
  width and height.
- `drm_gem_fb_init_with_funcs()` ends in `drm_framebuffer_init()`: the fb is
  visible to lookups when it returns.
- `drm_framebuffer_init()`: returns `-EINVAL` with a warning when `fb->dev` is
  not `dev` or `fb->format` is NULL; `drm_helper_mode_fill_fb_struct()` sets
  both.
- `drm_gem_fb_afbc_init()`: reads `afbc_fb->base.obj`, so it runs after
  `drm_gem_fb_init_with_funcs()`; on failure the caller puts the objects.
