- `lookup_one_common()` in `fs/namei.c`: is `lookup_noperm_common()` followed
  by `inode_permission(idmap, base->d_inode, MAY_EXEC)`; that call is the
  whole difference between the two families.
- `ecryptfs_lookup()` and `ksmbd_vfs_path_lookup()`: call
  `lookup_noperm_unlocked()`, not a `lookup_one()` form.
- cachefiles: calls `lookup_one_positive_unlocked()` and `start_creating()`
  with `&nop_mnt_idmap`, not a noperm form.
- overlayfs: `ovl_lookup_positive_unlocked()` and
  `ovl_lookup_upper_unlocked()` (in `fs/overlayfs/overlayfs.h`) call
  `lookup_one_unlocked()` with the layer's idmap, and `ovl_lookup_index()`
  calls `lookup_one_positive_unlocked()`; there is no ovl_lookup_upper().
- overlayfs NFS export code: uses noperm forms, in `ovl_get_index_fh()` and
  `ovl_lookup_real_one()`.
- **Potentially unsafe usage**: a `lookup_noperm()` form on a directory, with
  a name that comes from a user or a network client.
  - Unsafe: when nothing before the call checked `MAY_EXEC` on that directory
    for the acting credentials; `lookup_noperm_common()` makes no permission
    check, so an unsearchable directory is searched.
  - Safe: when the directory was reached by a path walk, which calls
    `may_lookup()` on it in `link_path_walk()` before parsing the last
    component, as `kern_path_parent()` and `ksmbd_vfs_path_lookup()` do after
    `filename_parentat()` and `vfs_path_parent_lookup()`.
  - Safe: when a filesystem looks up, in its own tree, a name chosen by kernel
    code, as `debugfs_lookup()` does.
