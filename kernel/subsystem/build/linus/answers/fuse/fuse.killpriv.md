- `fc->handle_killpriv` (v1): `fuse_setattr()` treats it like v2, so chown is
  left to the server as well as write and truncate; `FATTR_KILL_SUIDGID` and
  `FUSE_OPEN_KILL_SUIDGID` are not sent.
- `fuse_cache_write_iter()`: calls `kiocb_modified()` in every mode, so
  `file_remove_privs_flags()` in `fs/inode.c` still runs under v1 and v2.
- `fuse_direct_write_iter()`: calls neither `kiocb_modified()` nor
  `file_remove_privs()`.
- `fuse_direct_io()`: sets `FUSE_WRITE_KILL_SUIDGID` on `!capable(CAP_FSETID)`
  without testing `fc->handle_killpriv_v2`; `fuse_send_write_pages()` tests
  both.
- Writeback requests: carry `FUSE_WRITE_CACHE` only, never
  `FUSE_WRITE_KILL_SUIDGID`.
- `fuse_send_open()`: tests `O_TRUNC` after stripping it when
  `fc->atomic_o_trunc` is clear, so `FUSE_OPEN_KILL_SUIDGID` needs that flag
  too.
- Without `fc->atomic_o_trunc` the truncate of an `O_TRUNC` open arrives as
  `FUSE_SETATTR`, with `FATTR_KILL_SUIDGID` when `fc->handle_killpriv_v2` is
  set and the caller lacks `CAP_FSETID`.
- `fuse_create_open()`: sets `FUSE_OPEN_KILL_SUIDGID` only when also
  `!(flags & O_EXCL)`; that test does not include `fc->atomic_o_trunc`.
- Chown under v2: `fuse_do_setattr()` sets `FATTR_KILL_SUIDGID` for every
  non-directory, with no `CAP_FSETID` test; truncate tests `CAP_FSETID`.
- `setattr_should_drop_suidgid()`: used in `fs/fuse` only by
  `fuse_cache_write_iter()`, not by `fuse_setattr()`; there is no
  fuse_open_common() here.
- `fuse_setattr()` early return on empty `ia_valid`: not reached from write or
  truncate, because `__remove_privs()` adds `ATTR_FORCE` and `do_truncate()`
  sets `ATTR_SIZE`.
- Write under v1 or v2, when `file_remove_privs_flags()` finds bits to kill: a
  `FUSE_SETATTR` without mode goes out before the write, and the mode in its
  reply becomes the cached mode.
- After a write or `O_TRUNC` open: only `FUSE_STATX_MODSIZE` is invalidated;
  nothing in `fs/fuse` invalidates `STATX_MODE` alone, and `i_mode` is not
  edited.
- `security.capability`: when the VFS passes `ATTR_KILL_PRIV`,
  `setattr_prepare()` in `fuse_do_setattr()` removes it through
  `fuse_removexattr()`, whatever the killpriv flags.
