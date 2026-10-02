- Just-created file (`FMODE_CREATED`): `may_open()` still runs;
  `inode_permission()` is called with `MAY_OPEN` alone, and the type switch,
  `IS_APPEND()` and `O_NOATIME` tests still apply.
- `mnt_want_write()` in `do_open()`: taken before `may_open()`, and only for a
  regular file with `O_TRUNC` that was not just created; that same test
  decides whether `handle_truncate()` runs.
- After `vfs_open()`: `do_open()` calls `security_file_post_open()`, then
  `handle_truncate()`; it does not call `ima_file_check()`, which is a static
  LSM hook in `security/integrity/ima/ima_main.c`, reached through
  `security_file_post_open()`.
- `->atomic_open()` that opened the file (`FMODE_OPENED`): `may_open()` runs
  after the filesystem's open method.
- `vfs_tmpfile()`: calls `may_open()` with `acc_mode` 0 after `->tmpfile()` has
  created and opened the file.
- No `may_open()` at all, for example: `O_PATH` (`do_o_path()`),
  `dentry_open()`, `kernel_file_open()` and `vfs_lookup_open()` reach
  `vfs_open()` without it.
- `__O_REGULAR` on a non-regular file: `-EFTYPE` from `do_open()`, before
  `may_open()`.
- `O_CREAT` on an existing directory: `-EISDIR` from `do_open()`, not from
  `may_open()`.

| Type | `may_open()` check |
|---|---|
| `S_IFLNK` | `-ELOOP` |
| `S_IFDIR` | `MAY_WRITE` gives `-EISDIR`; `MAY_EXEC` gives `-EACCES` |
| `S_IFBLK`, `S_IFCHR` | `may_open_dev()` false gives `-EACCES`: `MNT_NODEV` or `SB_I_NODEV` |
| devices, `S_IFIFO`, `S_IFSOCK` | `MAY_EXEC` gives `-EACCES` |
| `S_IFREG` | `MAY_EXEC` with `path_noexec()` gives `-EACCES`; nothing else |
| other | `VFS_BUG_ON_INODE(!IS_ANON_FILE(inode), inode)`, only with `CONFIG_DEBUG_VFS` |

- Devices, FIFOs and sockets: `O_TRUNC` is dropped from the local `flag` only;
  `acc_mode` is kept and `inode_permission()` still runs.
- Immutable inode: not tested in `may_open()`; `inode_permission()` returns
  `-EPERM` for `MAY_WRITE`.
