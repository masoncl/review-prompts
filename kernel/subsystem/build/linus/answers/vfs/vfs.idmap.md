- `struct mnt_idmap`: holds `uid_map`, `gid_map` and `count`, no user
  namespace pointer; `alloc_mnt_idmap()` in `fs/mnt_idmapping.c` copies the
  maps out of the namespace.
- `&invalid_mnt_idmap`: no mount carries it; only `fs/fuse/` passes it, for
  requests that have no idmap; `make_vfsuid()` returns `INVALID_VFSUID` and
  `from_vfsuid()` returns `INVALID_UID` for it.
- `&nop_mnt_idmap`: `make_vfsuid()` returns the kuid unchanged and never looks
  at `s_user_ns`, so the vfsuid is invalid only when `i_uid` is `INVALID_UID`.
- Mount idmap changes: `can_idmap_mount()` allows one only while the mount is
  in an anonymous mount namespace (`is_anon_ns()`); replacing or clearing an
  existing idmap needs `MOUNT_KATTR_IDMAP_REPLACE`, which only
  `open_tree_attr()` with `OPEN_TREE_CLONE` sets.
- `SB_I_NOIDMAP`: `can_idmap_mount()` returns `-EINVAL` for it even with
  `FS_ALLOW_IDMAP`; fuse sets it and clears it only for `FUSE_ALLOW_IDMAP`
  with `default_permissions`.
- nfsd and ecryptfs: pass `&nop_mnt_idmap` for the exported or lower object,
  and refuse an idmapped mount up front with `is_idmapped_mnt()` in
  `check_export()` and `ecryptfs_get_tree()`.
- overlayfs: passes the idmap of the layer's mount, for example
  `mnt_idmap(realpath.mnt)` in `ovl_permission()`.
- New inode owner: `inode_init_owner()` in `fs/inode.c`, built on
  `mapped_fsuid()` and `mapped_fsgid()`.
- What is refused when an id has no mapping, beyond `inode_permission()` and
  `notify_change()`:

| Where | Unmapped | Result |
|---|---|---|
| `may_create_dentry()`, `may_o_create()`, `vfs_tmpfile()` | caller's fsuid or fsgid | `-EOVERFLOW` |
| `may_delete_dentry()` | victim's owner | `-EOVERFLOW`, before `inode_permission()` on the directory |
| `may_linkat()` | source's owner | `-EOVERFLOW` |
| `vfs_link()` | source's owner | `-EPERM` |
| `may_write_xattr()` | inode's owner | `-EPERM` |
| `atime_needs_update()` | inode's owner | returns false, no error |

- `setattr_prepare()`: has no `-EOVERFLOW` test for an unmapped id;
  `-EOVERFLOW` for attribute changes comes from `notify_change()`.
- `chown_ok()` and `chgrp_ok()` with an invalid current owner: return true
  when the caller has `CAP_CHOWN` in `inode->i_sb->s_user_ns`, so an unmapped
  owner can be made valid.
- **Potentially unsafe usage**: comparing `inode->i_uid` or `inode->i_gid`
  with the caller's ids, or comparing or storing `ia_uid` or `ia_gid`, as raw
  kuid/kgid values.
  - Unsafe: in a filesystem with `FS_ALLOW_IDMAP`, or in code that can be
    reached with any mount's idmap; on an idmapped mount the wrong user
    matches, or an unmapped id is stored.
  - Safe: in a filesystem without `FS_ALLOW_IDMAP`, as `jfs_setattr()` does;
    `can_idmap_mount()` returns `-EINVAL` for it, so the idmap is always
    `&nop_mnt_idmap` and `ia_uid` equals `ia_vfsuid`.
  - Safe: through `i_uid_into_vfsuid()` with `vfsuid_eq_kuid()`, and
    `i_uid_update()` for the store, as `inode_owner_or_capable()` and
    `setattr_copy()` do.
