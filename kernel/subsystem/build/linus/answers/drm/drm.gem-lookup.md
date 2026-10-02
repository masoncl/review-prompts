- `drm_gem_objects_lookup()` on failure: drops the references it took, frees
  the array and leaves `*objs_out` NULL; the caller releases nothing.
- `drm_gem_objects_lookup()` with `count == 0`: returns 0 with `*objs_out`
  NULL.
- `DRM_IOCTL_GEM_CHANGE_HANDLE`: defined in `include/uapi/drm/drm.h`, but the
  table in `drivers/gpu/drm/drm_ioctl.c` routes it to `drm_invalid_op()`,
  which returns `-EINVAL`.
- `drm_gem_change_handle_ioctl()`: still defined in
  `drivers/gpu/drm/drm_gem.c`, with no caller; user space cannot move an
  object between handles.
