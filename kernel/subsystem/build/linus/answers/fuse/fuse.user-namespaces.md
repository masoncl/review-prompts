- `fuse_fill_creds()` in `fs/fuse/req.c`: the only place that fills request
  credentials. It writes `args->uid`, `args->gid` and `args->pid` in
  `struct fuse_args`; `fuse_args_to_req()` in `fs/fuse/dev.c` copies them to
  the header.
- There is no fuse_force_creds() here, and `fuse_get_req()` does not touch
  credentials.
- `fc->user_ns`: the `user_ns` argument of `fuse_conn_init()`.
  `fuse_get_tree()` passes `fsc->user_ns`; CUSE passes
  `file->f_cred->user_ns`.
- `/dev/fuse` fd opened in another user namespace: rejected by
  `fuse_opt_fd()` while the `fd=` parameter is parsed.
- `user_id=` and `group_id=`: `fs_param_is_uid()` and `fs_param_is_gid()`
  convert with `current_user_ns()`; `fuse_parse_param()` then requires a
  mapping in `fsc->user_ns`.
- Reply uid and gid: `make_kuid()` and `make_kgid()` results are stored in
  the inode unchecked; `fuse_invalid_attr()` tests only mode and size.
- `fuse_fill_creds()` chooses by `SB_I_NOIDMAP` on `fm->sb`, not by whether
  the mount in use is idmapped. `fm->sb` NULL counts as `SB_I_NOIDMAP` set.

| Request | `SB_I_NOIDMAP` set | `SB_I_NOIDMAP` clear |
|---|---|---|
| not `force` | `from_kuid()`/`from_kgid()` of fsuid/fsgid; `-EOVERFLOW` if either is unmapped | ids from `mapped_fsuid()`/`mapped_fsgid()` with the idmap passed; no `-EOVERFLOW`; with `&invalid_mnt_idmap` both are `FUSE_INVALID_UIDGID` |
| `force`, not `nocreds` (for example `fuse_flush()`) | `from_kuid_munged()`/`from_kgid_munged()` | `FUSE_INVALID_UIDGID` |
| `force` and `nocreds` | uid and gid not written | uid and gid not written |

- `args->pid`: written for every row above, before the `force` test.
- `fuse_simple_background()` and `fuse_simple_notify_reply()`: always pass
  `&invalid_mnt_idmap`.
- `FS_ALLOW_IDMAP`: unconditional in `fs_flags` of `fuse_fs_type`,
  `fuseblk_fs_type` and the type in `fs/fuse/virtio_fs.c`.
- `SB_I_NOIDMAP`: set by `fuse_sb_defaults()`, cleared only by
  `process_init_reply()`, tested by `can_idmap_mount()` in `fs/namespace.c`.
- `FUSE_ALLOW_IDMAP` without `fc->default_permissions`:
  `process_init_reply()` fails the connection (`fc->conn_error = 1`).
- `FUSE_POSIX_ACL` in the same reply sets `fc->default_permissions` before
  that test, so it satisfies it without the mount option.
- `fuse_simple_idmap_request()`: three call sites, all in `fs/fuse/dir.c`:
  `create_new_entry()`, `fuse_create_open()`, `fuse_rename_common()`.
- `fuse_rename2()`: passes the real idmap only with `RENAME_WHITEOUT`.
- `fuse_link()`: passes `&invalid_mnt_idmap`, through `create_new_nondir()`
  to `create_new_entry()`.
- getattr, setattr and permission requests go through
  `fuse_simple_request()`; the idmap is applied to their payload or result,
  in `iattr_to_fattr()`, `fuse_fillattr()` and `generic_permission()`.
- **Potentially unsafe usage**: sending a request that creates an inode
  through `fuse_simple_request()`.
  - Unsafe: when the server uses the header uid and gid as the owner of the
    new inode; with `SB_I_NOIDMAP` clear it receives `FUSE_INVALID_UIDGID`.
  - Safe: `fuse_simple_idmap_request()` with the idmap the VFS passed, as
    `fuse_mkdir()` does through `create_new_entry()`; `fuse_fill_creds()`
    defines the mapping.
  - Safe: `FUSE_LINK`, which creates no inode; `fuse_link()` passes
    `&invalid_mnt_idmap`.
