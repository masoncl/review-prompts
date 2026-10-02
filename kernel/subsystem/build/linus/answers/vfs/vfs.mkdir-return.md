- `vfs_mkdir()` on failure: calls `end_creating(dentry)` on every error path,
  so the parent is unlocked and the passed dentry is released before the
  `ERR_PTR` returns.
- `vfs_mkdir()` return value: the dentry to use or an `ERR_PTR`, never NULL;
  only the `->mkdir` method returns NULL.
- Unlock target: `dentry->d_parent->d_inode`, not the `dir` argument, so it
  happens however the caller took the lock.
- Other `vfs_` helpers in `fs/namei.c`: none calls `end_creating()`; after a
  failed `vfs_create()` or `vfs_link()` the parent is still locked and the
  caller ends the bracket with the original dentry.
- Parent after failure: a caller that reached the parent only through the
  passed dentry has no dentry left that names it; `ecryptfs_mkdir()` takes
  `dget(lower_dentry->d_parent)` before the call.
- Successful return: `vfs_mkdir()` does not test that the dentry is positive
  or hashed; `nfsd_create_locked()` tests `d_is_negative()`,
  `ecryptfs_mkdir()` tests `d_unhashed()`, `cachefiles_get_directory()` tests
  both and retries.
- **Unsafe usage**: unlocking the parent, or passing the original dentry to
  `end_creating()`, after `vfs_mkdir()` returned an `ERR_PTR`.
  - Safe: assign the return value over the dentry variable and pass that to
    `end_creating()`, which does nothing for an `ERR_PTR`, as
    `nfsd4_create_clid_dir()` and `cachefiles_get_directory()` do.
  - Safe: pass the return value to `end_creating_path()`, which still drops
    write access and the path, as `dev_mkdir()` in `drivers/base/devtmpfs.c`
    does.
- **Potentially unsafe usage**: `dput()` of the original dentry after
  `vfs_mkdir()` returned an `ERR_PTR`.
  - Unsafe: when the caller's only reference was the one it passed in;
    `end_dirop()` already dropped it.
  - Safe: when the caller took a second reference with `dget()` before the
    call, as `nfsd_create_locked()` does with `dget(resfhp->fh_dentry)`;
    `nfsd_create()` then calls `dput()` on the original.
