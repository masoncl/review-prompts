- kern_path_locked(), kern_path_create(), done_path_create(),
  user_path_locked_at() and start_removing_user_path_at(): none is defined in
  this tree, not even as a wrapper.

| Helper | Returns | Holds on success | Released by |
|---|---|---|---|
| `start_creating_path()` | negative dentry, or `-EEXIST` | parent lock, write access, parent path | `end_creating_path()` |
| `start_creating_user_path()` | same, from a user string | same | `end_creating_path()` |
| `start_removing_path()` | positive dentry, or `-ENOENT` | parent lock, write access, parent path | `end_removing_path()` |

- `end_removing_path()`: is `end_creating_path()`; it unlocks, drops the
  dentry, calls `mnt_drop_write()` and `path_put()`. `end_removing()` plus
  `path_put()` leaks the write access.
- `end_creating_path()` with an `ERR_PTR` dentry: skips unlock and `dput()`
  but still drops write access and the path, so it is right after a failed
  `vfs_mkdir()` and wrong after a failed `start_creating_path()`.
- User-string removal: no helper; `filename_rmdir()` and
  `filename_unlinkat()` call `filename_parentat()`, `mnt_want_write()` and
  `start_dirop()` themselves.
- `kern_path_parent()`: returns the parent in `*path` and the child dentry
  with nothing locked and no write access; the child can be negative; the
  caller releases with `dput()` and `path_put()`.
