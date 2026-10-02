- `fuse_lock_inode()` callers: only `fuse_lookup()` and
  `fuse_readdir_uncached()`.
- LOOKUP sent without `fi->mutex`: from `fuse_dentry_revalidate()`,
  `fuse_get_dentry()` and `fuse_get_parent()`. So without
  `fc->parallel_dirops` the server can still see parallel LOOKUPs in one
  directory.
- `fi->mutex`: no user other than `fuse_lock_inode()` and
  `fuse_unlock_inode()`; it guards no DAX or readdir-cache state.
- `fi->inval_mask`: not protected by `fi->lock`. Writers use
  `set_mask_bits()` (`fuse_invalidate_attr_mask()` holds no lock), readers use
  `READ_ONCE()`.
- `fi->state`: atomic bit operations, no lock needed.
  `FUSE_I_CACHE_IO_MODE` is changed only under `fi->lock`, which also guards
  `fi->iocachectr`, in `fs/fuse/iomode.c`.
- `struct fuse_inode` has no list or rbtree of in-flight writepages; the
  write state under `fi->lock` is `write_files`, `queued_writes`, `writectr`
  and `iocachectr`.
- `fi->rdc`, with `fi->rdc.lock`, shares a union with those write fields.
  `fi->rdc.lock` is initialised only in `fuse_init_dir()`, so it exists only
  on directories, and the write fields only on regular files.
- `fi->dax->sem`: an rw_semaphore in `struct fuse_inode_dax`, defined in
  `fs/fuse/dax.c`; `fi->dax` exists only under `CONFIG_FUSE_DAX` and is NULL
  unless `fc->dax` is set.
