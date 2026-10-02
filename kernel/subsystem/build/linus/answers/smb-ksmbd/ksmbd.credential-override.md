- `__ksmbd_override_fsids()` in `fs/smb/server/smb_common.c`: base is
  `prepare_kernel_cred(&init_task)`. It changes `fsuid`, `fsgid`, the
  supplementary groups and, for a non-root `fsuid`, `cap_effective`; nothing
  else.
- Return value: an `int`. The old credentials are kept in
  `work->saved_cred`, not handed to the caller.
- `ksmbd_override_fsids()`: dereferences `work->tcon->share_conf` and
  `work->sess->user`. Before the tree connect exists, pass the share to
  `__ksmbd_override_fsids()`, as `share_config_request()` does.
- A second mechanism exists for work on an open handle:
  `override_creds(fp->filp->f_cred)` with a local saved pointer.
  `smb2_set_info()` uses it, not `ksmbd_override_fsids()`. `f_cred` is what
  `dentry_open()` recorded under the override in `smb2_open()`.
- `ksmbd_vfs_remove_file()`, `ksmbd_vfs_link()` and `ksmbd_vfs_rename()`:
  each calls `ksmbd_override_fsids()` and `ksmbd_revert_fsids()` itself.
- **Unsafe usage**: calling `ksmbd_override_fsids()`, or one of the three
  helpers above, while `work->saved_cred` is set.
  - Safe: calling them under `override_creds(fp->filp->f_cred)` only, as
    `smb2_set_info()` does through `smb2_rename()`. The requirement is
    `WARN_ON(work->saved_cred)` in `__ksmbd_override_fsids()`, which then
    overwrites the field.
- Example handlers: `smb2_query_info()` and `smb2_query_dir()` in
  `fs/smb/server/smb2pdu.c`; each has one override site.
- `smb2_open()`: has three override sites. Label `err_out2` is below the
  `ksmbd_revert_fsids()` call, so it is correct only for a path that holds no
  override. `err_out` and `err_out1` are for paths that hold it.
- `ksmbd_free_work_struct()`: does `WARN_ON(work->saved_cred != NULL)`, which
  is where a missed revert shows up.
- Share writability: `test_tree_conn_flag()` with
  `KSMBD_TREE_CONN_FLAG_WRITABLE`. No server code tests
  `KSMBD_SHARE_FLAG_WRITEABLE` or `KSMBD_SHARE_FLAG_READONLY`.
- `smb_check_perm_dacl()`: `smb2_open()` calls it for an existing file
  without testing `KSMBD_SHARE_FLAG_ACL_XATTR`. It is skipped when
  `FILE_DELETE_ON_CLOSE_LE` is set.
- `inode_permission()` in `smb2_open()`: needed because the file is opened
  with `dentry_open()`, which makes no such check. For an existing file it is
  skipped when `daccess` holds only `FILE_READ_ATTRIBUTES_LE` and
  `FILE_READ_CONTROL_LE`, and when `daccess` still holds
  `FILE_MAXIMAL_ACCESS_LE` after `smb_check_perm_dacl()`.
- Delete permission: there is no ksmbd_vfs_may_delete() here. `smb2_open()`
  calls `inode_permission()` on the parent with `MAY_EXEC | MAY_WRITE`, only
  after the `inode_permission()` check on the file above ran, and only when
  `daccess` has `FILE_DELETE_LE` or `FILE_DELETE_ON_CLOSE_LE` is set.
- `fp->daccess` for read and write is tested at two levels with different
  masks: `smb2_read()` accepts `FILE_READ_DATA_LE` or
  `FILE_READ_ATTRIBUTES_LE`; `ksmbd_vfs_read()` then requires
  `FILE_READ_DATA_LE` or `FILE_EXECUTE_LE`. `smb2_write()` accepts
  `FILE_WRITE_DATA_LE` or `FILE_READ_ATTRIBUTES_LE`; `ksmbd_vfs_write()` then
  requires `FILE_WRITE_DATA_LE` or `FILE_APPEND_DATA_LE`.
