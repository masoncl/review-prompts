- Copy-in: `drm_ioctl()` copies the full user `in_size`, also when it is larger
  than the kernel structure; `ksize` is the largest of the three sizes.
- Longer user structure: the handler sees its own structure at the start of
  `data`; with `IOC_IN` and `IOC_OUT` both set, bytes beyond it are copied
  back unchanged.
- Copy-out: `copy_to_user()` of `out_size` bytes runs whatever
  `drm_ioctl_kernel()` returned, so what a failing handler wrote to `data`
  reaches user space.
- Direction bits: `in_size` or `out_size` becomes 0 unless both the user `cmd`
  and `ioctl->cmd` have `IOC_IN` or `IOC_OUT`; with `in_size` 0 the whole
  buffer is zeroed.
- Unknown ioctl: `-ENOTTY` only when `DRM_IOCTL_TYPE(cmd)` is not
  `DRM_IOCTL_BASE`; a number past the table or an entry with no `func` gives
  `-EINVAL`.
- `DRIVER_LEGACY`: only a value of `enum drm_driver_feature`; `drm_ioctl()`
  has no legacy test and there is no legacy ioctl flag.
- `DRM_ROOT_ONLY`: a plain `capable(CAP_SYS_ADMIN)` test; nothing in the tree
  marks it deprecated.
- `DRM_ROOT_ONLY` kerneldoc in `include/drm/drm_ioctl.h`: names SETMASTER and
  DROPMASTER, but `drm_ioctls[]` gives both flags 0 and the handlers call
  `drm_master_check_perm()`.
