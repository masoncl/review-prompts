- `__fuse_get_acl()`: `-EOPNOTSUPP` becomes NULL only when `fc->no_getxattr` is
  set; otherwise it is returned as an error.
- `fuse_get_acl()` without `fc->posix_acl`: still asks the server, unless
  `fuse_no_acl()` is true; then it returns `-EOPNOTSUPP` without a request.
- `fuse_set_acl()`: stores nothing in the ACL cache and does not edit `i_mode`.
- `fuse_set_acl()` with `fc->posix_acl`: calls `forget_all_cached_acls()` and
  `fuse_invalidate_attr()` whatever the request returned, also on error.
- `fuse_setxattr()` and `fuse_removexattr()`: on success call only
  `fuse_update_ctime()`; the comment in `fuse_set_acl()` claims more.
- Without `fc->posix_acl`, a successful ACL set marks only `STATX_CTIME` stale;
  the cached mode stays valid.
- `FUSE_SETXATTR_ACL_KILL_SGID`: added only with `fc->posix_acl`.
- `SB_POSIXACL`: set by `fuse_fill_super_common()` on the superblock it fills,
  whatever `fc->posix_acl` is.
- Umask on create: skipped by `fc->dont_mask`, not by `fc->posix_acl`.
