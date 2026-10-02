- First `->state` of a plane, CRTC or connector: `drm_mode_config_reset()`
  calls the `reset` hook if set, otherwise `atomic_create_state`. A driver
  with `atomic_create_state` and no `reset` is complete, as
  `tidss_crtc_funcs` is.
  `drm_mode_config_create_initial_state()` is the variant that calls no
  `reset` hook and also covers private objects.
- There is no struct drm_atomic_helper. The atomic helpers are functions in
  `drivers/gpu/drm/drm_atomic_helper.c` plus the helper vtables in
  `include/drm/drm_modeset_helper_vtables.h`.
- `drm_atomic_helper_check()`: does not check in pipeline order. It runs
  `drm_atomic_helper_check_modeset()` (connectors, encoders, bridges, CRTC
  modes) first, then `drm_atomic_helper_check_planes()`.
- `struct drm_colorop` (`include/drm/drm_colorop.h`): one colour operation on
  one plane, and a mode object (`DRM_MODE_OBJECT_COLOROP`).
  - Colorops chain through `next` into a pipeline;
    `drm_plane_state.color_pipeline` points at the first one of the active
    pipeline.
  - `struct drm_colorop_state` has its own array in
    `struct drm_atomic_commit`.
- `struct drm_mode_object`: base of planes, CRTCs, encoders, connectors,
  colorops, properties, blobs and framebuffers only. `struct drm_bridge`,
  `struct drm_panel` and `struct drm_private_obj` have no object id.
- `struct drm_bridge`: embeds a `struct drm_private_obj` as `base`, and
  `struct drm_bridge_state` embeds a `struct drm_private_state`. Bridge state
  therefore travels in the `private_objs` array of the commit.
  - `drm_bridge_attach()` calls `drm_atomic_private_obj_init()` for every
    bridge; there is no drm_bridge_is_atomic() test and no atomic_reset hook.
  - Allocated only by `devm_drm_bridge_alloc()`.
  - `drm_bridge_add()` (global list) and `drm_bridge_attach()` (encoder chain)
    each hold their own reference.
- `struct drm_minor`: a device has either the accel minor alone, or the
  primary minor plus an optional render minor; see `drm_dev_init()` in
  `drivers/gpu/drm/drm_drv.c`.
  - `DRIVER_COMPUTE_ACCEL` together with `DRIVER_RENDER` or `DRIVER_MODESET`:
    `drm_dev_init()` returns `-EINVAL`.
  - Accel nodes are not under `/dev/dri/`: they use `ACCEL_MAJOR` and the
    devnode "accel/%s", see `drivers/accel/drm_accel.c`.
- Leases: there is no struct drm_lease. A lease is a `struct drm_master` whose
  `lessor` points at the owning master (`include/drm/drm_auth.h`).
- `struct drm_crtc_commit`: progress of one commit on one CRTC (`hw_done`,
  `flip_done`, `cleanup_done`). Plane, CRTC and connector states each hold a
  reference in their `commit` field; later commits wait on it, which is what
  orders nonblocking commits.
- `struct drm_client_dev`: an in-kernel KMS user with its own internal
  `struct drm_file`, opened on the primary minor and kept on
  `drm_device.filelist_internal`. For example the "fbdev" and "drm_log"
  clients in `drivers/gpu/drm/clients/`; search for `drm_client_init()` for
  the rest.
- `struct drm_gpusvm` (`include/drm/drm_gpusvm.h`): mirror of part of a CPU
  `struct mm_struct` into a GPU address space, built from
  `struct drm_gpusvm_notifier` (an MMU interval notifier) holding
  `struct drm_gpusvm_range` entries. Not refcounted; it lives inside the
  driver's VM object. Ranges are refcounted.
- `struct drm_pagemap` (`include/drm/drm_pagemap.h`): refcounted wrapper
  around a `struct dev_pagemap` of device-private memory.
  `struct drm_pagemap_devmem` is one device memory allocation that belongs
  to it.
