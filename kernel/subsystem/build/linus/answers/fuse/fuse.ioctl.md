- `FUSE_IOCTL_UNRESTRICTED`: passed only by `cuse_file_ioctl()` and
  `cuse_file_compat_ioctl()`, and only when `cc->unrestricted_ioctl` is set
  from `CUSE_UNRESTRICTED_IOCTL` in the CUSE init reply; no FUSE mount path
  passes it.
- Retry count in unrestricted mode: unbounded; there is no
  FUSE_IOCTL_MAX_RETRY in this tree, and `fuse_do_ioctl()` loops as long as
  the server sets `FUSE_IOCTL_RETRY`.
- `in_iovs`, `out_iovs` or their sum above `FUSE_IOCTL_MAX_IOV`: `-ENOMEM`,
  not `-EIO`.
- `fuse_verify_ioctl_iov()`: `-ENOMEM` when the running total of one
  direction exceeds `fc->max_pages << PAGE_SHIFT`.
- `fuse_verify_ioctl_iov()` runs only on iovecs from a `FUSE_IOCTL_RETRY`
  reply; restricted-mode iovecs skip it and are bounded by the
  `max_pages > fm->fc->max_pages` test.
- User copies: inline in `fuse_do_ioctl()` with `copy_folio_from_iter()` and
  `copy_folio_to_iter()`; there is no fuse_ioctl_copy_user() here.
- Entry point for files: `fuse_ioctl_common()` through `fuse_file_ioctl()`;
  there is no fuse_file_do_ioctl() here.
- `FS_IOC_GETFLAGS`, `FS_IOC_SETFLAGS`, `FS_IOC_FSGETXATTR`,
  `FS_IOC_FSSETXATTR`: not special-cased in `fuse_do_ioctl()`;
  `do_vfs_ioctl()` routes them to `fuse_fileattr_get()` and
  `fuse_fileattr_set()`, which use `fuse_priv_ioctl()` with a kernel buffer.
- `FS_IOC_MEASURE_VERITY` in restricted mode: `fuse_setup_measure_verity()`
  resizes the single iovec to `sizeof(struct fsverity_digest)` plus the
  caller's `digest_size`.
- `FS_IOC_ENABLE_VERITY` in restricted mode: `fuse_setup_enable_verity()`
  appends input iovecs for salt and signature from the caller's
  `struct fsverity_enable_arg`; each is limited to
  `FUSE_VERITY_ENABLE_ARG_MAX_PAGES` pages, else `-ENOMEM`.
