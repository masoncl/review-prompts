- Acked-by: the user-space reviewer should give one on the kernel uAPI patch;
  `Documentation/gpu/drm-uapi.rst` does not ask for a link in the commit.
- Canonical upstream: the user-space patches must be against it, not a vendor
  fork.
- Merge order: the kernel patch goes to drm-next or drm-misc-next before the
  user-space patches land.
- IGT: not named as the user, which must not be a toy or test application;
  IGT testcases are a separate requirement, for cross-driver uAPI, under
  "Testing Requirements for userspace API".
- Structure size: padded to a multiple of 64 bits if the structure holds
  64-bit types.
- Variable-sized array: must not be the last member, because `drm_ioctl()`
  zero-extends; see the DOC comment in `drivers/gpu/drm/drm_ioctl.c`.
- Time values: `__s64` seconds plus `__u64` nanoseconds; the handler rejects
  values that are not normalized.
- Code path that cannot restart: must at least be killable.
- sysfs and debugfs: `Documentation/process/botching-up-ioctls.rst` recommends
  considering them instead of an ioctl; it does not forbid them.
- Driver ioctl number: must lie between `DRM_COMMAND_BASE` and
  `DRM_COMMAND_END`, and its name must start with DRM_IOCTL_.
