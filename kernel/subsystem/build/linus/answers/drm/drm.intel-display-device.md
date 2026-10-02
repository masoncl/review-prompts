- Allocation: `intel_display_device_probe()` uses `kzalloc_obj()`; nothing in
  xe allocates the struct itself.
- i915 caller: `i915_driver_probe()`, right after `i915_driver_create()`
  returns; not inside `i915_driver_create()`.
- xe caller: `xe_display_probe()` in `drivers/gpu/drm/xe/display/xe_display.c`;
  the free is the drmm action `display_device_remove()`. There is no
  xe_display_create().
- Probe precondition: it takes `pci_get_drvdata(pdev)` as the
  `struct drm_device *`, so the driver must have set drvdata first.
- Probe return: `ERR_PTR(-ENOMEM)` is the only error. Unknown device id,
  IVB Q, or an unrecognised GMD_ID still return a valid struct whose info is
  `no_display`; test `HAS_DISPLAY()` or `intel_display_device_present()`, not
  the pointer. For an id absent from `intel_display_ids[]` the probe logs
  "Unknown device ID" with `drm_dbg_kms()`.
- xe with `xe->info.probe_display` false at `xe_display_probe()`: probe is
  not called and `xe->display` stays NULL. The member exists only under
  `CONFIG_DRM_XE_DISPLAY`.
- Second probe argument: `const struct intel_display_parent_interface *`
  (`include/drm/intel/display_parent_interface.h`), kept in `display->parent`.
  Each driver passes its own static `parent`.
- `to_intel_display()`: does not accept `struct drm_i915_private *` or
  `struct xe_device *`. It does accept `struct device *` and
  `struct pci_dev *`, both through drvdata.
- `IS_TIGERLAKE()`-style macros: still defined in
  `drivers/gpu/drm/i915/i915_drv.h`, take i915, and have no users under
  `drivers/gpu/drm/i915/display/`. They do not take `display`.
- Version with release: `DISPLAY_VERx100()` and
  `IS_DISPLAY_VERx100(display, from, until)`; the latter build-fails when
  `from` is below 200. There is no DISPLAY_VER_FULL() or
  IS_DISPLAY_VER_FULL().
- Group bits: `display->platform.dgfx`, `display->platform.mobile` and
  `display->platform.g4x` are set by `PLATFORM_GROUP()` alongside the
  platform bit.
- `display->platform.haswell_ult` and `display->platform.broadwell_ult`: also
  set on ULX parts (`SUBPLATFORM_GROUP()`), so test the `_ulx` bit first when
  the two differ. Other platforms' `_ult` bits do not cover ULX.
