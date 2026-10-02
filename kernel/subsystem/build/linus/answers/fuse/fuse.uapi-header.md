- `FUSE_KERNEL_MINOR_VERSION`: 46 in this tree; the last changelog entry
  is 7.46.
- `fuse_copy_out_args()` in `fs/fuse/dev.c` defines the reply size rule: a
  reply longer than expected is `-EINVAL`; a shorter one is `-EINVAL`
  unless `out_argvar` is set, and then only the last argument may shrink.
- `fuse_adjust_compat()` in `fs/fuse/dev.c`: applies the compat sizes for
  STATFS, entry-out, attr-out, CREATE and MKNOD from `fch->minor`; the
  call sites in `fs/fuse/dir.c` do not.
- `fuse_adjust_compat()` runs only in `fuse_chan_send()`; a request sent
  with `fuse_chan_send_bg()` is not adjusted.
- Compat sizes set at the call site: `FUSE_COMPAT_WRITE_IN_SIZE` in
  `fuse_write_args_fill()` on `fc->minor < 9`;
  `FUSE_COMPAT_SETXATTR_IN_SIZE` in `fuse_setxattr()` when
  `fc->setxattr_ext` is clear, an INIT flag, not the minor.
- `FUSE_COMPAT_INIT_OUT_SIZE` and `FUSE_COMPAT_22_INIT_OUT_SIZE`: defined
  for servers; no code in `fs/fuse` uses them.
- **Unsafe usage**: enlarging a reply structure and expecting the new
  `sizeof()` from every server.
  - Unsafe: an older server sends the old size; `fuse_copy_out_args()`
    returns `-EINVAL` to its write and the request ends with `-EIO`.
  - Safe: shrink the expected size for older minors, as
    `fuse_adjust_compat()` does with `FUSE_COMPAT_ENTRY_OUT_SIZE`.
  - Safe: set `out_argvar` on a zeroed buffer, as `fuse_new_init()` does
    for `struct fuse_init_out`.
