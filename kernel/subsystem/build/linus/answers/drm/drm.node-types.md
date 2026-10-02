- `drm_ioctl_permit()` in `drivers/gpu/drm/drm_ioctl.c`: tests `DRM_ROOT_ONLY`,
  `DRM_AUTH`, `DRM_MASTER`, then the render rule; every failure is `-EACCES`.
- Accel node: `drm_is_render_client()` is false for it, so `DRM_RENDER_ALLOW`
  is not needed and `DRM_AUTH` is not waived.
- Accel node and `DRM_MASTER`: the ioctl fails; `drm_open_helper()` calls
  `drm_master_open()` only for primary files, so `is_master` stays false.
- Control node: `DRM_MINOR_CONTROL` is still a value of `enum drm_minor_type`
  in `include/drm/drm_file.h`, but `drm_dev_init()` allocates no such minor.
- `create_compat_control_link()` in `drivers/gpu/drm/drm_drv.c`: adds only a
  sysfs symlink named controlD<n> to the primary minor, for `DRIVER_MODESET`.
- `authenticated`: written only in `drm_file_alloc()` (to
  `capable(CAP_SYS_ADMIN)`), `drm_new_set_master()`, `drm_authmagic()` and
  `drm_mode_create_lease_ioctl()`; nothing clears it, so a file that drops
  master stays authenticated.
- `drm_getmagic()` and `drm_authmagic()`: each uses the calling file's own
  `master->magic_map`, so authentication works only when both files point at
  the same `struct drm_master`; `drm_authmagic()` returns `-EINVAL` for a
  magic that is not in the caller's map.
- `drm_authmagic()`: replaces the entry with NULL, so a magic works once; the
  id is freed in `drm_master_release()`.
- `drm_setmaster_ioctl()`: does not take master from another holder; it
  returns `-EBUSY` while `dev->master` is set and the caller is not the
  current master.
- `drm_master_check_perm()`: passes without `CAP_SYS_ADMIN` only when
  `was_master` is set and the caller's tgid equals `file_priv->pid`.
- Lease owner: not blocked from leased objects; `_drm_lease_held_master()`
  returns true for a master with no `lessor`.
- Double leasing: `drm_lease_create()` returns `ERR_PTR(-EBUSY)` when
  `_drm_has_leased()` finds the object in another lessee.
- Lessee and the lease ioctls: all four are `DRM_MASTER`, which a lessee
  passes while its owner is `dev->master`; `drm_mode_create_lease_ioctl()`
  then returns `-EINVAL` for a lessee; `drm_mode_get_lease_ioctl()` returns
  the caller's own leased ids.
- `drm_mode_revoke_lease_ioctl()`: empties the lessee's `leases`; the lessee
  file stays master and authenticated, but every CRTC, connector and plane
  lookup by that file then fails.
- `drm_lease_revoke()`: is the close path, called from `drm_master_release()`
  for a file with `is_master` on a `DRIVER_MODESET` device.
- Lessee and master switching: both ioctls call `drm_master_check_perm()`
  first; once it passes, `drm_dropmaster_ioctl()` returns `-EINVAL` for a
  master with a `lessor`, and `drm_setmaster_ioctl()` does the same when the
  device has no master.
