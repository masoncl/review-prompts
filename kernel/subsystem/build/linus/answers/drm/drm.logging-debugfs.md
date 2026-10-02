- `_ratelimited` forms: of the macros that are not deprecated, only
  `drm_err_ratelimited()`, `drm_dbg_ratelimited()` and
  `drm_dbg_kms_ratelimited()` exist; info, notice and warn have `_once` forms
  only.
- No device, debug: `include/drm/drm_print.h` deprecates `DRM_DEBUG_KMS()` and
  its siblings in favour of `drm_dbg_kms(NULL, ...)` and so on.
- No device, other levels: `DRM_ERROR()`, `DRM_WARN()`, `DRM_INFO()` and
  `DRM_NOTE()` are deprecated in favour of `pr_err()` and its siblings.
- `DRM_DEV_ERROR()` and `DRM_DEV_INFO()`: deprecated in favour of `drm_err()`
  or `dev_err()`, and `drm_info()` or `dev_info()`.
- `DRM_DEV_DEBUG()`, `DRM_DEV_DEBUG_DRIVER()` and `DRM_DEV_DEBUG_KMS()`:
  deprecated in favour of `drm_dbg_core()`, `drm_dbg()` and `drm_dbg_kms()`.
- `drm_debugfs_add_file()`: creates the file at once under
  `dev->debugfs_root`, which `drm_dev_init()` has already made.
- `drm_debugfs_entry_open()`: returns `-ENODEV` until the minor is registered.
- `drm_debugfs_add_files()`: does not test `driver_features` of `struct
  drm_debugfs_info`; `drm_debugfs_create_files()` tests it for `struct
  drm_info_list`.
- Device directory: named `dev->unique` under dri, or under accel for
  `DRIVER_COMPUTE_ACCEL`; `drm_debugfs_register()` adds a symlink named by
  minor index.
- `debugfs_init` of `struct drm_driver`: not called for the render minor, nor
  for an accel device.
- Connector: `debugfs_init` is called from `drm_debugfs_connector_add()`,
  before `late_register`; there is no drm_debugfs_connector_init() here.
- CRTC: `struct drm_crtc_funcs` has no `debugfs_init`; create files under
  `crtc->debugfs_entry` from `late_register`.
- `drm_crtc_register_all()`: makes `crtc->debugfs_entry` just before it calls
  `late_register`.
- Plane: no `debugfs_init` hook.
- Bridge: `debugfs_init` of `struct drm_bridge_funcs` is called only from
  `drm_bridge_connector_debugfs_init()`, with the connector's directory as
  root.
