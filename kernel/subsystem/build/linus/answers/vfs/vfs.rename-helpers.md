- Helpers, all exported from `fs/namei.c` and declared in
  `include/linux/namei.h`:

| Function | Caller has | Permission check |
|---|---|---|
| `start_renaming()` | two parents, two names | `MAY_EXEC` on both parents |
| `start_renaming_dentry()` | source dentry, target name | `MAY_EXEC` on `new_parent` |
| `start_renaming_two_dentries()` | both dentries | none |
| `end_renaming()` | a successful start | - |

- Superblock: the helpers do not compare superblocks. `nfsd_rename()` and
  `ksmbd_vfs_rename()` compare the mounts before the call.
- Dentry variants after locking: `-EINVAL` if `old_dentry` is unhashed, or
  if `rd->old_parent` is non-NULL and is not `old_dentry->d_parent`.
- `start_renaming_two_dentries()`: also `-EINVAL` if `new_dentry` is
  unhashed or `rd->new_parent != new_dentry->d_parent`, and `-EEXIST` if
  `new_dentry` is positive with `RENAME_NOREPLACE`.
- `struct renamedata`, filled by the caller: `mnt_idmap`, `new_parent`,
  `flags`, `delegated_inode`, and `old_parent`.
- `old_parent`: required by `start_renaming()`; may be NULL for the two
  dentry variants, which then set it.
- `old_dentry` and `new_dentry`: filled by the helpers, with references.
- `mnt_idmap`: one field; there are no per-side idmap fields.
- `delegated_inode`: a `struct delegated_inode *`, read only by
  `vfs_rename()`; may be NULL.
- `struct renamedata` on the stack without an initialiser: the helpers read
  `old_parent` and `flags`, so set every caller field, as
  `ksmbd_vfs_rename()` does.
- `end_renaming()`: calls `dput()` on `rd->old_parent`; that is the extra
  reference the start helper took, not the caller's.
- **Unsafe usage**: calling `end_renaming()` after a start helper returned an
  error; nothing is locked and `rd->old_dentry` was not set.
  - Safe: skip it on error, as `nfsd_rename()` does.
