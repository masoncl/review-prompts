- `fuse_permissible_uidgid()`: compares euid, suid, uid with `fc->user_id`
  and egid, sgid, gid with `fc->group_id`. It does not compare fsuid or fsgid.
- `current_in_userns(fc->user_ns)`: tested only when `fc->allow_other` is
  set. Without `allow_other` the user namespace is not tested.
- `allow_sys_admin_access` (module parameter in `fs/fuse/dir.c`, default
  off): with it, `capable(CAP_SYS_ADMIN)` overrides a failed test in either
  branch.
- Callers: search for `fuse_allow_current_process` in `fs/fuse`; they are in
  `fs/fuse/dir.c`, `fs/fuse/inode.c`, `fs/fuse/xattr.c` and
  `fs/fuse/ioctl.c`.
- Not callers: `fuse_lookup()`, `fuse_open()`, `fuse_dir_open()`,
  `fuse_atomic_open()`, `fuse_get_link()`, `fuse_access()`,
  `fuse_xattr_get()`, `fuse_xattr_set()`, `fuse_get_acl()`, `fuse_set_acl()`.
- There is no fuse_open_common() here.
- Open: the test runs because `may_open()` in `fs/namei.c` calls
  `inode_permission()`, which reaches `fuse_permission()`.
- `fuse_ioctl_common()`: the one file operation that runs the test on every
  call. CUSE calls `fuse_do_ioctl()` directly and skips it.
- Fileattr get and set: tested in `fuse_priv_ioctl_prepare()`.

| Denied caller in | Result |
|---|---|
| `fuse_getattr()`, `request_mask` zero | 0; only `stat->dev` set, `stat->result_mask = 0`; no request |
| `fuse_getattr()`, otherwise | `-EACCES` |
| `fuse_statfs()` | 0; only `buf->f_type = FUSE_SUPER_MAGIC`; no request |
| other callers | `-EACCES` |

- **Potentially unsafe usage**: an inode or superblock operation that sends
  a request without calling `fuse_allow_current_process()`.
  - Unsafe: when the VFS reaches the operation without a prior
    `inode_permission()` on an inode of this connection; a task that fails
    the test then waits on the server.
  - Safe: when the VFS calls `inode_permission()` on the inode or its parent
    first, since `fuse_permission()` runs the test before it sends a
    request; for example `fuse_unlink()` after `may_delete_dentry()`,
    `create_new_entry()` after `may_create_dentry()`.
  - Safe: when the operation runs the test itself before it sends, as
    `fuse_setattr()`, `fuse_listxattr()` and `fuse_statfs()` do.
