- Three places resolve a client name to the path that is used, all in
  `fs/smb/server/vfs.c`: `ksmbd_vfs_path_lookup()`,
  `ksmbd_vfs_kern_path_create()` and `ksmbd_vfs_rename()`. For a non-empty
  name each calls `vfs_path_parent_lookup()` with `&share_conf->vfs_path` as
  root and ORs in `LOOKUP_BENEATH`.
- `ksmbd_vfs_kern_path_create()`: confined on its own; it needs no earlier
  confined lookup. There is no convert_to_unix_name() and no
  kern_path_create() in this tree.
- Caller flags on create: passed to the parent walk unchanged, so
  `LOOKUP_NO_SYMLINKS` applies there too.
- `LOOKUP_NO_SYMLINKS`: supplied by the caller of `ksmbd_vfs_kern_path()` and
  `ksmbd_vfs_kern_path_create()`, never added by them; `ksmbd_vfs_rename()`
  sets it itself; `smb2_creat()` re-looks the new file up with flags 0.
- Empty name in `ksmbd_vfs_path_lookup()`: resolves `share_conf->path` with
  no root and without `LOOKUP_BENEATH`.
- Leading `/` in the name: not rejected; the walk starts at the share root
  and skips it.
- Last component: not walked by `vfs_path_parent_lookup()`.
  `ksmbd_vfs_path_lookup()` uses `lookup_noperm_unlocked()`, or
  `start_removing_noperm()` for removal; create uses
  `start_creating_noperm()`.
- Last component `.` or `..`: `vfs_path_parent_lookup()` returns `-EINVAL`,
  even when the result would stay inside the share.
- Symlink as last component: returned, not followed, no `-ELOOP`. The caller
  decides: `smb2_open()` returns `-EACCES` through `d_is_symlink()` when
  `FILE_DELETE_ON_CLOSE_LE` is not set; `ksmbd_vfs_rename()` does the same
  for the target.
- Mount point as last component: crossed by `follow_down()` only in the
  non-remove branch of `ksmbd_vfs_path_lookup()`, and only with
  `KSMBD_SHARE_FLAG_CROSSMNT`. The remove and create paths never cross it.
- `ksmbd_vfs_rename()` and `ksmbd_vfs_link()`: return `-EXDEV` when source
  and target are on different mounts.
- Caseless fallback in `__ksmbd_vfs_kern_path()`: runs only on `-ENOENT`. Its
  `vfs_path_lookup()` is rooted at the share but has no `LOOKUP_BENEATH`.
  It only finds the directory to list; the returned path always comes from
  the `retry` through `ksmbd_vfs_path_lookup()`.
- `KSMBD_SHARE_FLAG_CROSSMNT`: tested in one place,
  `ksmbd_vfs_path_lookup()`.
- `KSMBD_SHARE_FLAG_FOLLOW_SYMLINKS`: defined in
  `fs/smb/server/ksmbd_netlink.h` and named in the proc table in
  `fs/smb/server/mgmt/share_config.c`; no server code tests it.
